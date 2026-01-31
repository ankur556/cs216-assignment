"""
Mempool - Memory pool for unconfirmed transactions
This is the "waiting area" for transactions before they're mined into blocks
"""

from validator import TransactionValidator


class Mempool:
    def __init__(self, max_size=50):
        """
        Initialize mempool.
        
        Args:
            max_size: Maximum number of transactions in mempool
        """
        self.transactions = []  # List of Transaction objects
        self.spent_utxos = set()  # Set of (tx_id, index) tuples being spent
        self.max_size = max_size
        self.validator = TransactionValidator()
    
    def add_transaction(self, tx, utxo_manager):
        """
        Validate and add transaction to mempool.
        
        Args:
            tx: Transaction object
            utxo_manager: UTXO manager instance
            
        Returns:
            Tuple (success: bool, message: str)
        """
        # Check if mempool is full
        if len(self.transactions) >= self.max_size:
            # Evict lowest fee transaction
            success = self._evict_lowest_fee(utxo_manager)
            if not success:
                return False, "Mempool full and cannot evict lower fee transactions"
        
        # Validate transaction
        is_valid, message = self.validator.validate_transaction(tx, utxo_manager, self)
        
        if not is_valid:
            return False, message
        
        # Add transaction to mempool
        self.transactions.append(tx)
        
        # Mark UTXOs as spent in mempool
        for inp in tx.inputs:
            input_key = (inp["prev_tx"], inp["index"])
            self.spent_utxos.add(input_key)
        
        return True, message
    
    def remove_transaction(self, tx_id: str):
        """
        Remove transaction from mempool by ID.
        
        Args:
            tx_id: Transaction ID to remove
            
        Returns:
            Removed transaction or None if not found
        """
        for i, tx in enumerate(self.transactions):
            if tx.tx_id == tx_id:
                removed_tx = self.transactions.pop(i)
                
                # Remove spent UTXOs from tracking
                for inp in removed_tx.inputs:
                    input_key = (inp["prev_tx"], inp["index"])
                    self.spent_utxos.discard(input_key)
                
                return removed_tx
        return None
    
    def get_transaction(self, tx_id: str):
        """Get transaction by ID"""
        for tx in self.transactions:
            if tx.tx_id == tx_id:
                return tx
        return None
    
    def get_top_transactions(self, n: int, utxo_manager):
        """
        Return top N transactions by fee (highest first).
        
        Args:
            n: Number of transactions to return
            utxo_manager: UTXO manager to calculate fees
            
        Returns:
            List of transactions sorted by fee (descending)
        """
        # Calculate fees for all transactions
        tx_with_fees = []
        for tx in self.transactions:
            fee = tx.calculate_fee(utxo_manager)
            tx_with_fees.append((tx, fee))
        
        # Sort by fee (descending)
        tx_with_fees.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N transactions
        return [tx for tx, fee in tx_with_fees[:n]]
    
    def clear(self):
        """Clear all transactions from mempool"""
        self.transactions.clear()
        self.spent_utxos.clear()
    
    def _evict_lowest_fee(self, utxo_manager):
        """
        Evict the transaction with the lowest fee.
        
        Args:
            utxo_manager: UTXO manager to calculate fees
            
        Returns:
            True if eviction successful, False otherwise
        """
        if not self.transactions:
            return False
        
        # Find transaction with lowest fee
        min_fee = float('inf')
        min_fee_tx = None
        
        for tx in self.transactions:
            fee = tx.calculate_fee(utxo_manager)
            if fee < min_fee:
                min_fee = fee
                min_fee_tx = tx
        
        if min_fee_tx:
            self.remove_transaction(min_fee_tx.tx_id)
            return True
        
        return False
    
    def display(self, utxo_manager=None):
        """Display all transactions in mempool"""
        if not self.transactions:
            print("\nMempool is empty")
            return
        
        print(f"\n=== Mempool ({len(self.transactions)} transactions) ===")
        
        for i, tx in enumerate(self.transactions, 1):
            fee = tx.calculate_fee(utxo_manager) if utxo_manager else 0
            
            inputs_summary = ", ".join([
                f"({inp['prev_tx']}, {inp['index']})"
                for inp in tx.inputs
            ])
            
            outputs_summary = ", ".join([
                f"{out['amount']:.3f} BTC to {out['address']}"
                for out in tx.outputs
            ])
            
            print(f"\n{i}. TX {tx.tx_id}")
            print(f"   Inputs: {inputs_summary}")
            print(f"   Outputs: {outputs_summary}")
            print(f"   Fee: {fee:.8f} BTC")
        print()
    
    def get_total_fees(self, utxo_manager):
        """Calculate total fees from all transactions in mempool"""
        total = 0.0
        for tx in self.transactions:
            total += tx.calculate_fee(utxo_manager)
        return total