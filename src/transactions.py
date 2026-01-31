from dataclasses import dataclass

@dataclass
class TransactionInput:
    prev_tx: str
    index: int
    owner: str

@dataclass
class TransactionOutput:
    amount: float
    address: str

class Transaction:
    def __init__(self, tx_id: str, inputs: list[TransactionInput], outputs: list[TransactionOutput]):
        self.tx_id = tx_id
        self.inputs = inputs  # List of (tx_id, index) tuples
        self.outputs = outputs  # List of TransactionOutput instances

