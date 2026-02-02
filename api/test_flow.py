from api.database import init_db, get_db
from api.logic import BitcoinService
from api.models import UTXOModel

def test_flow():
    print("Initializing InMemory DB...")
    init_db(use_firestore=False)
    db = get_db()
    service = BitcoinService(db)

    print("Resetting system to Genesis...")
    genesis_alloc = {"Alice": 50.0, "Bob": 30.0}
    service.init_genesis(genesis_alloc)
    
    print(f"Alice Balance: {service.get_balance('Alice')}")
    print(f"Bob Balance: {service.get_balance('Bob')}")

    assert service.get_balance('Alice') == 50.0
    
    print("Creating Transaction: Alice -> Bob (10.0 BTC)...")
    tx, msg = service.create_transaction("Alice", "Bob", 10.0, 0.001)
    if tx:
        print(f"Transaction created: {tx.tx_id}")
    else:
        print(f"Transaction failed: {msg}")
        return

    print("Checking Mempool...")
    mempool = db.get_mempool()
    print(f"Mempool size: {len(mempool)}")
    assert len(mempool) == 1

    print("Mining Block...")
    block, msg = service.mine_block("Miner1")
    if block:
        print(f"Block mined: {block.hash}")
        print(f"Miner received: {block.total_fees} BTC")
    else:
        print(f"Mining failed: {msg}")
        return

    print("Verifying Balances...")
    alice_bal = service.get_balance('Alice')
    bob_bal = service.get_balance('Bob')
    miner_bal = service.get_balance('Miner1')
    
    print(f"Alice: {alice_bal} (Expected ~39.999)")
    print(f"Bob: {bob_bal} (Expected 40.0)")
    print(f"Miner1: {miner_bal} (Expected 0.001)")
    
    # Alice started with 50, sent 10, paid 0.001 fee -> 39.999
    assert abs(alice_bal - 39.999) < 1e-8
    # Bob started with 30, received 10 -> 40.0
    assert abs(bob_bal - 40.0) < 1e-8
    # Miner got fee 0.001
    assert abs(miner_bal - 0.001) < 1e-8

    print("SUCCESS: Full flow verification passed!")

if __name__ == "__main__":
    test_flow()
