"""
Validator - Implements all Bitcoin transaction validation rules
"""


class TransactionValidator:
    """Validates transactions according to Bitcoin rules"""
    
    @staticmethod
    def validate_transaction(tx, utxo_manager, mempool=None):
        """
        Validate a transaction against all Bitcoin rules.
        
        Validation Rules:
        1. All inputs must exist in UTXO set
        2. No double-spending in inputs (same UTXO twice in same transaction)
        3. Sum(inputs) >= Sum(outputs) (difference = fee)
        4. No negative amounts in outputs
        5. No conflict with mempool (UTXO not already spent in unconfirmed tx)
        
        Args:
            tx: Transaction object to validate
            utxo_manager: UTXO manager instance
            mempool: Mempool instance (optional, for conflict checking)
            
        Returns:
            Tuple (is_valid: bool, message: str)
        """
        
        # Rule 4: No negative amounts in outputs
        for output in tx.outputs:
            if output["amount"] < 0:
                return False, f"Invalid: Negative output amount {output['amount']}"
        
        # Rule 2: No double-spending in inputs (same UTXO twice)
        seen_inputs = set()
        for inp in tx.inputs:
            input_key = (inp["prev_tx"], inp["index"])
            if input_key in seen_inputs:
                return False, f"Invalid: Double-spend in same transaction - UTXO {input_key} used twice"
            seen_inputs.add(input_key)
        
        # Rule 1: All inputs must exist in UTXO set
        total_input = 0.0
        for inp in tx.inputs:
            if not utxo_manager.exists(inp["prev_tx"], inp["index"]):
                return False, f"Invalid: Input UTXO ({inp['prev_tx']}, {inp['index']}) does not exist"
            
            # Verify ownership (simulated signature check)
            utxo = utxo_manager.get_utxo(inp["prev_tx"], inp["index"])
            if utxo["owner"] != inp["owner"]:
                return False, f"Invalid: UTXO owner mismatch. Expected {utxo['owner']}, got {inp['owner']}"
            
            total_input += utxo["amount"]
        
        # Rule 5: No conflict with mempool
        if mempool:
            for inp in tx.inputs:
                input_key = (inp["prev_tx"], inp["index"])
                if input_key in mempool.spent_utxos:
                    # Find which transaction in mempool is spending this UTXO
                    conflicting_tx = None
                    for pending_tx in mempool.transactions:
                        for pending_inp in pending_tx.inputs:
                            if (pending_inp["prev_tx"], pending_inp["index"]) == input_key:
                                conflicting_tx = pending_tx.tx_id
                                break
                    return False, f"Invalid: UTXO {input_key} already spent by transaction {conflicting_tx} in mempool"
        
        # Rule 3: Sum(inputs) >= Sum(outputs)
        total_output = sum(out["amount"] for out in tx.outputs)
        if total_input < total_output:
            return False, f"Invalid: Insufficient inputs. Input: {total_input:.8f} BTC, Output: {total_output:.8f} BTC"
        
        # Calculate fee
        fee = total_input - total_output
        
        return True, f"Valid transaction. Fee: {fee:.8f} BTC"
    
    @staticmethod
    def validate_coinbase_transaction(tx, block_fees: float):
        """
        Validate a coinbase (mining reward) transaction.
        
        Args:
            tx: Transaction object
            block_fees: Total fees from block
            
        Returns:
            Tuple (is_valid: bool, message: str)
        """
        # Coinbase transaction has no inputs
        if len(tx.inputs) != 0:
            return False, "Invalid: Coinbase transaction must have no inputs"
        
        # Should have exactly one output
        if len(tx.outputs) != 1:
            return False, "Invalid: Coinbase transaction must have exactly one output"
        
        # Output amount should equal total fees
        if abs(tx.outputs[0]["amount"] - block_fees) > 1e-8:  # Float comparison with tolerance
            return False, f"Invalid: Coinbase output {tx.outputs[0]['amount']} doesn't match fees {block_fees}"
        
        return True, "Valid coinbase transaction"