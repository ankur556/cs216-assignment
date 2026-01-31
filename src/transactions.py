from dataclasses import dataclass

@dataclass
class TransactionOutput:
    amount: float
    address: str

