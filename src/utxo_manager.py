from typing import Dict, List
from transactions import TransactionOutput


class UTXOManager:
    def __init__(self) -> None:
        self.utxo_set: Dict[str, TransactionOutput] = {}

    def _make_key(self, tx_id: str, index: int) -> str:
        return f"{tx_id}:{index}"

    def add_utxo(self, tx_id: str, index: int, amount: float, owner: str) -> None:
        key = self._make_key(tx_id, index)
        self.utxo_set[key] = TransactionOutput(amount, owner)

    def remove_utxo(self, tx_id: str, index: int) -> None:
        key = self._make_key(tx_id, index)
        self.utxo_set.pop(key, None)  # safe erase

    def exists(self, tx_id: str, index: int) -> bool:
        return self._make_key(tx_id, index) in self.utxo_set

    def get_balance(self, owner: str) -> float:
        balance = 0.0
        for utxo in self.utxo_set.values():
            if utxo.address == owner:
                balance += utxo.amount
        return balance

    def get_utxos_for_owner(self, owner: str) -> List[TransactionOutput]:
        return [
            utxo
            for utxo in self.utxo_set.values()
            if utxo.address == owner
        ]
