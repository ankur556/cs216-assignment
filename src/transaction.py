"""
Transaction - Defines Bitcoin transaction structure and basic operations
"""
import time
import random


class Transaction:
    def __init__(self, tx_id=None):
        """
        Initialize a transaction.
        
        Args:
            tx_id: Unique transaction identifier (auto-generated if None)
        """
        self.tx_id = tx_id if tx_id else self.generate_tx_id()
        self.inputs = []  # List of input dicts
        self.outputs = []  # List of output dicts
    
    @staticmethod
    def generate_tx_id():
        """Generate a unique transaction ID"""
        timestamp = int(time.time() * 1000)  # milliseconds
        random_suffix = random.randint(1000, 9999)
        return f"tx_{timestamp}_{random_suffix}"
    
    def add_input(self, prev_tx: str, index: int, owner: str):
        """
        Add an input to the transaction.
        
        Args:
            prev_tx: Previous transaction ID
            index: Output index in previous transaction
            owner: Owner of this UTXO
        """
        input_data = {
            "prev_tx": prev_tx,
            "index": index,
            "owner": owner
        }
        self.inputs.append(input_data)
    
    def add_output(self, amount: float, address: str):
        """
        Add an output to the transaction.
        
        Args:
            amount: Amount in BTC
            address: Recipient address
        """
        output_data = {
            "amount": amount,
            "address": address
        }
        self.outputs.append(output_data)
    
    def calculate_fee(self, utxo_manager):
        """
        Calculate transaction fee.
        Fee = Sum(inputs) - Sum(outputs)
        
        Args:
            utxo_manager: UTXO manager to look up input values
            
        Returns:
            Fee amount in BTC
        """
        total_input = 0.0
        for inp in self.inputs:
            utxo = utxo_manager.get_utxo(inp["prev_tx"], inp["index"])
            if utxo:
                total_input += utxo["amount"]
        
        total_output = sum(out["amount"] for out in self.outputs)
        return total_input - total_output
    
    def to_dict(self):
        """Convert transaction to dictionary format"""
        return {
            "tx_id": self.tx_id,
            "inputs": self.inputs,
            "outputs": self.outputs
        }
    
    @classmethod
    def from_dict(cls, tx_dict):
        """Create transaction from dictionary"""
        tx = cls(tx_dict["tx_id"])
        tx.inputs = tx_dict["inputs"]
        tx.outputs = tx_dict["outputs"]
        return tx
    
    def __str__(self):
        """String representation of transaction"""
        inputs_str = "\n    ".join([
            f"({inp['prev_tx']}, {inp['index']}) owned by {inp['owner']}"
            for inp in self.inputs
        ])
        outputs_str = "\n    ".join([
            f"{out['amount']:.8f} BTC -> {out['address']}"
            for out in self.outputs
        ])
        
        return f"""Transaction {self.tx_id}:
  Inputs:
    {inputs_str}
  Outputs:
    {outputs_str}"""
    
    def display(self, utxo_manager=None):
        """Display transaction details including fee if UTXO manager provided"""
        print(self)
        if utxo_manager:
            fee = self.calculate_fee(utxo_manager)
            print(f"  Fee: {fee:.8f} BTC")


def create_simple_transaction(sender: str, recipient: str, amount: float, 
                              utxo_manager, fee: float = 0.001):
    """
    Helper function to create a simple transaction.
    
    Args:
        sender: Sender address
        recipient: Recipient address
        amount: Amount to send in BTC
        utxo_manager: UTXO manager instance
        fee: Transaction fee in BTC (default 0.001)
        
    Returns:
        Transaction object or None if insufficient funds
    """
    # Get sender's UTXOs
    sender_utxos = utxo_manager.get_utxos_for_owner(sender)
    
    if not sender_utxos:
        return None
    
    # Select UTXOs to cover amount + fee
    needed = amount + fee
    selected_utxos = []
    total_selected = 0.0
    
    for tx_id, index, utxo_amount in sender_utxos:
        selected_utxos.append((tx_id, index, utxo_amount))
        total_selected += utxo_amount
        if total_selected >= needed:
            break
    
    if total_selected < needed:
        return None  # Insufficient funds
    
    # Create transaction
    tx = Transaction()
    
    # Add inputs
    for tx_id, index, _ in selected_utxos:
        tx.add_input(tx_id, index, sender)
    
    # Add output to recipient
    tx.add_output(amount, recipient)
    
    # Add change output back to sender
    change = total_selected - amount - fee
    if change > 0:
        tx.add_output(change, sender)
    
    return tx