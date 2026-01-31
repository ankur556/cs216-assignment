"""
UTXO Manager - Manages the Unspent Transaction Output set
This is Bitcoin's "database" of spendable coins
"""

class UTXOManager:
    def __init__(self):
        """Initialize UTXO set as dictionary: (tx_id, index) -> (amount, owner)"""
        self.utxo_set = {}
    
    def add_utxo(self, tx_id: str, index: int, amount: float, owner: str):
        """
        Add a new UTXO to the set.
        
        Args:
            tx_id: Transaction ID that created this UTXO
            index: Output index in that transaction
            amount: Amount in BTC
            owner: Address that owns this UTXO
        """
        key = (tx_id, index)
        self.utxo_set[key] = {
            "amount": amount,
            "owner": owner
        }
    
    def remove_utxo(self, tx_id: str, index: int):
        """
        Remove a UTXO (when spent).
        
        Args:
            tx_id: Transaction ID
            index: Output index
            
        Returns:
            Removed UTXO data or None if not found
        """
        key = (tx_id, index)
        if key in self.utxo_set:
            return self.utxo_set.pop(key)
        return None
    
    def get_balance(self, owner: str) -> float:
        """
        Calculate total balance for an address.
        
        Args:
            owner: Address to check balance for
            
        Returns:
            Total balance in BTC
        """
        balance = 0.0
        for utxo_data in self.utxo_set.values():
            if utxo_data["owner"] == owner:
                balance += utxo_data["amount"]
        return balance
    
    def exists(self, tx_id: str, index: int) -> bool:
        """
        Check if UTXO exists and is unspent.
        
        Args:
            tx_id: Transaction ID
            index: Output index
            
        Returns:
            True if UTXO exists, False otherwise
        """
        key = (tx_id, index)
        return key in self.utxo_set
    
    def get_utxos_for_owner(self, owner: str) -> list:
        """
        Get all UTXOs owned by an address.
        
        Args:
            owner: Address to get UTXOs for
            
        Returns:
            List of tuples: [(tx_id, index, amount), ...]
        """
        utxos = []
        for (tx_id, index), utxo_data in self.utxo_set.items():
            if utxo_data["owner"] == owner:
                utxos.append((tx_id, index, utxo_data["amount"]))
        return utxos
    
    def get_utxo(self, tx_id: str, index: int):
        """
        Get UTXO data for a specific UTXO.
        
        Args:
            tx_id: Transaction ID
            index: Output index
            
        Returns:
            UTXO data dict or None if not found
        """
        key = (tx_id, index)
        return self.utxo_set.get(key)
    
    def display_utxos(self):
        """Display all UTXOs in a readable format"""
        if not self.utxo_set:
            print("No UTXOs in the system")
            return
        
        print("\n=== Current UTXO Set ===")
        # Group by owner
        owner_utxos = {}
        for (tx_id, index), utxo_data in self.utxo_set.items():
            owner = utxo_data["owner"]
            if owner not in owner_utxos:
                owner_utxos[owner] = []
            owner_utxos[owner].append((tx_id, index, utxo_data["amount"]))
        
        for owner, utxos in sorted(owner_utxos.items()):
            total = sum(utxo[2] for utxo in utxos)
            print(f"\n{owner}: {total:.8f} BTC")
            for tx_id, index, amount in utxos:
                print(f"  - ({tx_id}, {index}): {amount:.8f} BTC")
        print()
    
    def get_total_supply(self) -> float:
        """Get total BTC in the system"""
        return sum(utxo["amount"] for utxo in self.utxo_set.values())