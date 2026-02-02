import time
import random
from typing import List, Tuple, Optional
from .models import TransactionModel, BlockModel, UTXOModel, TransactionInput, TransactionOutput
from .database import Database

class BitcoinService:
    def __init__(self, db: Database):
        self.db = db

    def get_balance(self, address: str) -> float:
        utxos = self.db.get_utxos(owner=address)
        return sum(u.amount for u in utxos)

    def validate_transaction(self, tx: TransactionModel) -> Tuple[bool, str]:
        # 1. No negative outputs
        for output in tx.outputs:
            if output.amount < 0:
                return False, f"Invalid: Negative output amount {output.amount}"

        # 2. No double spending in inputs (same UTXO twice in same tx)
        seen_inputs = set()
        for inp in tx.inputs:
            input_key = (inp.prev_tx, inp.index)
            if input_key in seen_inputs:
                return False, f"Invalid: Double-spend in same transaction - UTXO {input_key} used twice"
            seen_inputs.add(input_key)

        # 3. All inputs must exist in UTXO set AND belong to owner
        total_input = 0.0
        for inp in tx.inputs:
            utxo = self.db.get_utxo(inp.prev_tx, inp.index)
            if not utxo:
                return False, f"Invalid: Input UTXO ({inp.prev_tx}, {inp.index}) does not exist"
            
            if utxo.owner != inp.owner:
                return False, f"Invalid: UTXO owner mismatch. Expected {utxo.owner}, got {inp.owner}"
            
            total_input += utxo.amount

        # 4. No conflict with mempool (UTXO not already spent in unconfirmed tx)
        # Note: This is O(N*M) where N=mempool size, M=inputs. Could be optimized.
        mempool = self.db.get_mempool()
        spent_in_mempool = set()
        for m_tx in mempool:
            if m_tx.tx_id == tx.tx_id:
                continue # Skip self if already in there (shouldn't happen for new tx validation)
            for m_inp in m_tx.inputs:
                spent_in_mempool.add((m_inp.prev_tx, m_inp.index))

        for inp in tx.inputs:
            if (inp.prev_tx, inp.index) in spent_in_mempool:
                return False, f"Invalid: UTXO ({inp.prev_tx}, {inp.index}) already spent by transaction in mempool"

        # 5. Input >= Output
        total_output = sum(out.amount for out in tx.outputs)
        if total_input < total_output:
            return False, f"Invalid: Insufficient inputs. Input: {total_input:.8f}, Output: {total_output:.8f}"

        return True, f"Valid. Fee: {total_input - total_output:.8f}"

    def create_transaction(self, sender: str, recipient: str, amount: float, fee: float = 0.001) -> Tuple[Optional[TransactionModel], str]:
        # Get sender UTXOs
        utxos = self.db.get_utxos(sender)
        
        # Check tracking in mempool to avoid double spending *own* pending UTXOs
        mempool = self.db.get_mempool()
        spent_in_mempool = set()
        for m_tx in mempool:
            for m_inp in m_tx.inputs:
                spent_in_mempool.add((m_inp.prev_tx, m_inp.index))
        
        # Filter available UTXOs
        available_utxos = [u for u in utxos if (u.tx_id, u.index) not in spent_in_mempool]

        # Select UTXOs
        needed = amount + fee
        selected = []
        total_selected = 0.0

        for u in available_utxos:
            selected.append(u)
            total_selected += u.amount
            if total_selected >= needed:
                break
        
        if total_selected < needed:
            return None, f"Insufficient funds. Have {total_selected}, need {needed}"

        # Construct TX
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        tx_id = f"tx_{timestamp}_{random_suffix}"

        inputs = [TransactionInput(prev_tx=u.tx_id, index=u.index, owner=sender) for u in selected]
        outputs = [TransactionOutput(amount=amount, address=recipient)]
        
        change = total_selected - amount - fee
        if change > 0:
            outputs.append(TransactionOutput(amount=change, address=sender))

        tx = TransactionModel(
            tx_id=tx_id,
            inputs=inputs,
            outputs=outputs,
            timestamp=timestamp,
            status="pending"
        )
        
        # Validate again just to be safe (redundant but good)
        valid, msg = self.validate_transaction(tx)
        if not valid:
            return None, msg

        self.db.add_to_mempool(tx)
        return tx, "Transaction created and added to mempool"

    def mine_block(self, miner_address: str, num_txs: int = 5) -> Tuple[Optional[BlockModel], str]:
        mempool = self.db.get_mempool()
        if not mempool:
            return None, "No transactions in mempool"

        # Sort by fee
        # Fee calculation requires looking up UTXOs. 
        # For simplicity/speed, we'll calculate fees for all and sort.
        tx_fees = []
        valid_txs = []
        
        for tx in mempool:
            # Re-validate (UTXOs might have been spent by another block race condition)
            # In a real system, we'd do this carefully. 
            # With Firestore, we might want to do this inside a transaction, but here we do best effort.
            valid, _ = self.validate_transaction(tx)
            if not valid:
                # Invalid tx in mempool (maybe double spent?), remove it
                self.db.remove_from_mempool(tx.tx_id)
                continue
            
            # Calculate fee
            inputs_val = 0.0
            for inp in tx.inputs:
                u = self.db.get_utxo(inp.prev_tx, inp.index)
                if u: inputs_val += u.amount
            outputs_val = sum(o.amount for o in tx.outputs)
            fee = inputs_val - outputs_val
            tx_fees.append((tx, fee))

        tx_fees.sort(key=lambda x: x[1], reverse=True)
        selected = tx_fees[:num_txs]
        
        if not selected:
             return None, "No valid transactions to mine"

        selected_txs = [t[0] for t in selected]
        total_fees = sum(t[1] for t in selected)

        # Create Block
        chain = self.db.get_blockchain()
        prev_hash = chain[-1].hash if chain else "genesis"
        block_num = len(chain) + 1
        
        timestamp = int(time.time() * 1000)
        
        # Create Coinbase
        coinbase_tx = TransactionModel(
            tx_id=f"coinbase_{block_num}_{timestamp}",
            inputs=[],
            outputs=[TransactionOutput(amount=total_fees, address=miner_address)],
            timestamp=timestamp,
            status="confirmed"
        )
        
        # Add coinbase to list of txs for the block
        final_txs = selected_txs + [coinbase_tx] # Wait, typically coinbase is first
        
        block = BlockModel(
            block_number=block_num,
            previous_hash=prev_hash,
            miner=miner_address,
            transactions=final_txs,
            total_fees=total_fees,
            timestamp=timestamp,
            hash=f"block_{block_num}_{miner_address}_{len(final_txs)}_{timestamp}" # simplified hash
        )

        # Commit changes
        # 1. Remove inputs from UTXO
        # 2. Add outputs to UTXO
        # 3. Remove from mempool
        # 4. Add block
        
        for tx in selected_txs:
            for inp in tx.inputs:
                self.db.remove_utxo(inp.prev_tx, inp.index)
            for idx, out in enumerate(tx.outputs):
                self.db.add_utxo(UTXOModel(tx_id=tx.tx_id, index=idx, amount=out.amount, owner=out.address))
            self.db.remove_from_mempool(tx.tx_id)
            
        # Add coinbase UTXO
        self.db.add_utxo(UTXOModel(tx_id=coinbase_tx.tx_id, index=0, amount=total_fees, owner=miner_address))
        
        self.db.add_block(block)
        
        return block, f"Mined block {block.block_number} with {total_fees} fees"
        
    def init_genesis(self, allocations: dict):
        utxos = []
        for i, (owner, amount) in enumerate(allocations.items()):
            utxos.append(UTXOModel(tx_id="genesis", index=i, amount=amount, owner=owner))
        self.db.reset_system(utxos)
