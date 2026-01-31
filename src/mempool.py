

class Mempool:
    def __init__(self, max_size=50):
        self.transactions = []
        self.spent_utxos = set()
        self.max_size = max_size

    def add_transaction(self, tx, utxo_manager):
        pass

    def remove_transaction(self, tx_id : str):
        pass

    def get_top_trasactions(self, n: int) -> list:
        pass

    def clear(self):
        pass

