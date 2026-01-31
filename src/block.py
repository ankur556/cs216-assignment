"""
Block - Represents a block in the blockchain and mining simulation
"""

from transaction import Transaction


class Block:
    """Represents a single block in the blockchain"""
    
    block_counter = 0  # Class variable for block numbering
    
    def __init__(self, previous_hash="0", miner="genesis"):
        """
        Initialize a block.
        
        Args:
            previous_hash: Hash of previous block
            miner: Address of miner who created this block
        """
        Block.block_counter += 1
        self.block_number = Block.block_counter
        self.previous_hash = previous_hash
        self.miner = miner
        self.transactions = []
        self.total_fees = 0.0
        self.coinbase_tx = None
    
    def add_transaction(self, tx):
        """Add a transaction to this block"""
        self.transactions.append(tx)
    
    def set_coinbase(self, coinbase_tx):
        """Set the coinbase (mining reward) transaction"""
        self.coinbase_tx = coinbase_tx
    
    def get_hash(self):
        """Simulate block hash (simplified)"""
        return f"block_{self.block_number}_{self.miner}_{len(self.transactions)}"
    
    def __str__(self):
        return f"Block #{self.block_number} by {self.miner} ({len(self.transactions)} txs, {self.total_fees:.8f} BTC fees)"


def mine_block(miner_address: str, mempool, utxo_manager, num_txs=5):
    """
    Simulate mining a block.
    
    This is the atomic moment of "consensus" in our simulator.
    
    Steps:
    1. Select top transactions from mempool (by fee)
    2. Update UTXO set permanently (remove inputs, add outputs)
    3. Create coinbase transaction for miner fees
    4. Remove mined transactions from mempool
    
    Args:
        miner_address: Address of the miner
        mempool: Mempool instance
        utxo_manager: UTXO manager instance
        num_txs: Number of transactions to include (default 5)
        
    Returns:
        Block object or None if no transactions to mine
    """
    
    # Step 1: Select top transactions from mempool
    selected_txs = mempool.get_top_transactions(num_txs, utxo_manager)
    
    if not selected_txs:
        return None, "No transactions in mempool to mine"
    
    # Create new block
    block = Block(miner=miner_address)
    
    total_fees = 0.0
    
    # Step 2: Update UTXO set permanently
    for tx in selected_txs:
        # Calculate fee before removing inputs
        fee = tx.calculate_fee(utxo_manager)
        total_fees += fee
        
        # Remove input UTXOs (they are now spent)
        for inp in tx.inputs:
            utxo_manager.remove_utxo(inp["prev_tx"], inp["index"])
        
        # Add output UTXOs (newly created)
        for index, output in enumerate(tx.outputs):
            utxo_manager.add_utxo(
                tx.tx_id,
                index,
                output["amount"],
                output["address"]
            )
        
        # Add transaction to block
        block.add_transaction(tx)
    
    # Step 3: Create coinbase transaction for miner
    if total_fees > 0:
        coinbase_tx = Transaction(tx_id=f"coinbase_{block.block_number}")
        coinbase_tx.add_output(total_fees, miner_address)
        
        # Add coinbase UTXO to UTXO set
        utxo_manager.add_utxo(coinbase_tx.tx_id, 0, total_fees, miner_address)
        
        block.set_coinbase(coinbase_tx)
        block.total_fees = total_fees
    
    # Step 4: Remove mined transactions from mempool
    for tx in selected_txs:
        mempool.remove_transaction(tx.tx_id)
    
    return block, f"Block mined successfully with {len(selected_txs)} transactions and {total_fees:.8f} BTC in fees"


class Blockchain:
    """Simple blockchain to store mined blocks"""
    
    def __init__(self):
        self.chain = []
    
    def add_block(self, block):
        """Add a block to the blockchain"""
        self.chain.append(block)
    
    def get_latest_block(self):
        """Get the most recent block"""
        return self.chain[-1] if self.chain else None
    
    def display(self):
        """Display blockchain"""
        if not self.chain:
            print("\nBlockchain is empty")
            return
        
        print(f"\n=== Blockchain ({len(self.chain)} blocks) ===")
        for block in self.chain:
            print(f"\n{block}")
            if block.coinbase_tx:
                print(f"  Coinbase: {block.total_fees:.8f} BTC to {block.miner}")
            for i, tx in enumerate(block.transactions, 1):
                inputs_str = ", ".join([f"({inp['prev_tx']}, {inp['index']})" for inp in tx.inputs])
                outputs_str = ", ".join([f"{out['amount']:.3f} to {out['address']}" for out in tx.outputs])
                print(f"  TX {i}: {tx.tx_id}")
                print(f"    In: {inputs_str}")
                print(f"    Out: {outputs_str}")
        print()