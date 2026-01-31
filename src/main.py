from utxo_manager import UTXOManager

if __name__ == "__main__":
    my_manager = UTXOManager()
    my_manager.add_utxo("tx1", 0, 50.0, "Alice")
    print("Alice's Balance:", my_manager.get_balance("Alice"))
