"""
Test Scenarios - All 10 mandatory test cases from the assignment
"""

from transaction import Transaction, create_simple_transaction
from utxo_manager import UTXOManager
from mempool import Mempool
from validator import TransactionValidator
from block import mine_block


class TestScenarios:
    """Run all mandatory test cases"""
    
    def __init__(self, utxo_manager, mempool):
        self.utxo_manager = utxo_manager
        self.mempool = mempool
        self.validator = TransactionValidator()
    
    def run_all_tests(self):
        """Run all 10 test scenarios"""
        print("\n" + "="*60)
        print("Running All Test Scenarios")
        print("="*60)
        
        tests = [
            self.test_1_basic_valid_transaction,
            self.test_2_multiple_inputs,
            self.test_3_double_spend_same_transaction,
            self.test_4_mempool_double_spend,
            self.test_5_insufficient_funds,
            self.test_6_negative_amount,
            self.test_7_zero_fee_transaction,
            self.test_8_race_attack,
            self.test_9_complete_mining_flow,
            self.test_10_unconfirmed_chain
        ]
        
        for i, test in enumerate(tests, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}")
            print('='*60)
            test()
        
        print("\n" + "="*60)
        print("All Tests Completed")
        print("="*60)
    
    def test_1_basic_valid_transaction(self):
        """Test 1: Basic Valid Transaction - Alice sends 10 BTC to Bob"""
        print("Test 1: Basic Valid Transaction")
        print("Description: Alice sends 10 BTC to Bob with change and fee")
        
        # Create transaction
        tx = create_simple_transaction("Alice", "Bob", 10.0, self.utxo_manager, fee=0.001)
        
        if not tx:
            print("❌ FAILED: Could not create transaction")
            return
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        
        print(f"\nTransaction Details:")
        print(f"  TX ID: {tx.tx_id}")
        print(f"  Sender: Alice")
        print(f"  Recipient: Bob")
        print(f"  Amount: 10.0 BTC")
        print(f"  Fee: 0.001 BTC")
        print(f"  Change: {sum(out['amount'] for out in tx.outputs if out['address'] == 'Alice'):.8f} BTC back to Alice")
        print(f"\nValidation: {message}")
        
        if is_valid:
            success, msg = self.mempool.add_transaction(tx, self.utxo_manager)
            print(f"Mempool: {msg}")
            print("✅ PASSED")
        else:
            print("❌ FAILED")
    
    def test_2_multiple_inputs(self):
        """Test 2: Multiple Inputs - Combine multiple UTXOs"""
        print("Test 2: Multiple Inputs")
        print("Description: Alice spends multiple UTXOs together")
        
        # Get Alice's UTXOs
        alice_utxos = self.utxo_manager.get_utxos_for_owner("Alice")
        
        if len(alice_utxos) < 2:
            print("❌ FAILED: Alice doesn't have enough UTXOs for this test")
            return
        
        # Create transaction manually with multiple inputs
        tx = Transaction()
        
        total_input = 0.0
        for tx_id, index, amount in alice_utxos[:2]:  # Use first 2 UTXOs
            tx.add_input(tx_id, index, "Alice")
            total_input += amount
        
        # Send most to Bob, keep some change
        send_amount = total_input - 0.5  # Keep 0.5 as fee + change
        tx.add_output(send_amount - 0.001, "Bob")  # 0.001 fee
        tx.add_output(0.499, "Alice")  # Change
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        
        print(f"\nTransaction Details:")
        print(f"  TX ID: {tx.tx_id}")
        print(f"  Number of Inputs: {len(tx.inputs)}")
        print(f"  Total Input: {total_input:.8f} BTC")
        print(f"  Output to Bob: {send_amount - 0.001:.8f} BTC")
        print(f"  Change to Alice: 0.499 BTC")
        print(f"  Fee: 0.001 BTC")
        print(f"\nValidation: {message}")
        
        if is_valid:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
    
    def test_3_double_spend_same_transaction(self):
        """Test 3: Double-Spend in Same Transaction"""
        print("Test 3: Double-Spend in Same Transaction")
        print("Description: Transaction tries to spend same UTXO twice")
        
        # Get one of Alice's UTXOs
        alice_utxos = self.utxo_manager.get_utxos_for_owner("Alice")
        
        if not alice_utxos:
            print("❌ FAILED: Alice has no UTXOs")
            return
        
        tx_id, index, amount = alice_utxos[0]
        
        # Create transaction with duplicate input
        tx = Transaction()
        tx.add_input(tx_id, index, "Alice")
        tx.add_input(tx_id, index, "Alice")  # Same UTXO again!
        tx.add_output(amount * 1.5, "Bob")  # Try to spend it twice
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        
        print(f"\nTransaction Details:")
        print(f"  Attempting to spend ({tx_id}, {index}) twice")
        print(f"\nValidation: {message}")
        
        if not is_valid and "Double-spend in same transaction" in message:
            print("✅ PASSED - Correctly rejected double-spend")
        else:
            print("❌ FAILED - Should reject double-spend in same transaction")
    
    def test_4_mempool_double_spend(self):
        """Test 4: Mempool Double-Spend"""
        print("Test 4: Mempool Double-Spend")
        print("Description: Two transactions try to spend same UTXO")
        
        # Clear mempool for clean test
        temp_mempool = Mempool()
        
        # Get one of Bob's UTXOs
        bob_utxos = self.utxo_manager.get_utxos_for_owner("Bob")
        
        if not bob_utxos:
            print("❌ FAILED: Bob has no UTXOs")
            return
        
        tx_id, index, amount = bob_utxos[0]
        
        # TX1: Bob -> Charlie
        tx1 = Transaction()
        tx1.add_input(tx_id, index, "Bob")
        tx1.add_output(amount - 0.001, "Charlie")
        
        # TX2: Bob -> David (same UTXO!)
        tx2 = Transaction()
        tx2.add_input(tx_id, index, "Bob")
        tx2.add_output(amount - 0.001, "David")
        
        # Add TX1 to mempool
        success1, msg1 = temp_mempool.add_transaction(tx1, self.utxo_manager)
        print(f"\nTX1 (Bob -> Charlie):")
        print(f"  TX ID: {tx1.tx_id}")
        print(f"  Status: {msg1}")
        
        # Try to add TX2 to mempool
        success2, msg2 = temp_mempool.add_transaction(tx2, self.utxo_manager)
        print(f"\nTX2 (Bob -> David):")
        print(f"  TX ID: {tx2.tx_id}")
        print(f"  Status: {msg2}")
        
        if success1 and not success2 and "already spent" in msg2:
            print("\n✅ PASSED - TX1 accepted, TX2 correctly rejected")
        else:
            print("\n❌ FAILED - Should reject second transaction")
    
    def test_5_insufficient_funds(self):
        """Test 5: Insufficient Funds"""
        print("Test 5: Insufficient Funds")
        print("Description: Try to send more than available balance")
        
        # Try to create transaction with insufficient funds
        tx = create_simple_transaction("Eve", "Alice", 100.0, self.utxo_manager)
        
        eve_balance = self.utxo_manager.get_balance("Eve")
        
        print(f"\nEve's balance: {eve_balance:.8f} BTC")
        print(f"Attempting to send: 100.0 BTC")
        
        if tx is None:
            print("✅ PASSED - Transaction creation failed (insufficient funds)")
        else:
            # Validate to get proper error message
            is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
            print(f"Validation: {message}")
            if not is_valid:
                print("✅ PASSED - Transaction rejected")
            else:
                print("❌ FAILED - Should reject insufficient funds")
    
    def test_6_negative_amount(self):
        """Test 6: Negative Amount"""
        print("Test 6: Negative Amount")
        print("Description: Transaction with negative output amount")
        
        alice_utxos = self.utxo_manager.get_utxos_for_owner("Alice")
        
        if not alice_utxos:
            print("❌ FAILED: Alice has no UTXOs")
            return
        
        tx_id, index, amount = alice_utxos[0]
        
        # Create transaction with negative output
        tx = Transaction()
        tx.add_input(tx_id, index, "Alice")
        tx.add_output(-10.0, "Bob")  # Negative amount!
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        
        print(f"\nTransaction Details:")
        print(f"  Output amount: -10.0 BTC")
        print(f"\nValidation: {message}")
        
        if not is_valid and "Negative output" in message:
            print("✅ PASSED - Correctly rejected negative amount")
        else:
            print("❌ FAILED - Should reject negative amounts")
    
    def test_7_zero_fee_transaction(self):
        """Test 7: Zero Fee Transaction"""
        print("Test 7: Zero Fee Transaction")
        print("Description: Transaction with zero fee (valid in Bitcoin)")
        
        charlie_utxos = self.utxo_manager.get_utxos_for_owner("Charlie")
        
        if not charlie_utxos:
            print("❌ FAILED: Charlie has no UTXOs")
            return
        
        tx_id, index, amount = charlie_utxos[0]
        
        # Create transaction with zero fee
        tx = Transaction()
        tx.add_input(tx_id, index, "Charlie")
        tx.add_output(amount, "David")  # Exact amount = zero fee
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        
        fee = tx.calculate_fee(self.utxo_manager)
        
        print(f"\nTransaction Details:")
        print(f"  Input: {amount:.8f} BTC")
        print(f"  Output: {amount:.8f} BTC")
        print(f"  Fee: {fee:.8f} BTC")
        print(f"\nValidation: {message}")
        
        if is_valid and abs(fee) < 1e-8:
            print("✅ PASSED - Zero fee transaction is valid")
        else:
            print("❌ FAILED - Zero fee should be accepted")
    
    def test_8_race_attack(self):
        """Test 8: Race Attack Simulation"""
        print("Test 8: Race Attack Simulation")
        print("Description: Low-fee TX arrives first, high-fee TX arrives second")
        print("Expected: First transaction wins (first-seen rule)")
        
        # Clear mempool for clean test
        temp_mempool = Mempool()
        
        # Get one of David's UTXOs
        david_utxos = self.utxo_manager.get_utxos_for_owner("David")
        
        if not david_utxos:
            print("❌ FAILED: David has no UTXOs")
            return
        
        tx_id, index, amount = david_utxos[0]
        
        # Low-fee transaction (arrives first)
        tx_low = Transaction()
        tx_low.add_input(tx_id, index, "David")
        tx_low.add_output(amount - 0.0001, "Merchant")  # Low fee: 0.0001 BTC
        
        # High-fee transaction (arrives second, tries to replace)
        tx_high = Transaction()
        tx_high.add_input(tx_id, index, "David")
        tx_high.add_output(amount - 0.01, "Attacker")  # High fee: 0.01 BTC
        
        # Add low-fee transaction first
        success1, msg1 = temp_mempool.add_transaction(tx_low, self.utxo_manager)
        fee1 = tx_low.calculate_fee(self.utxo_manager)
        
        print(f"\nLow-fee TX (David -> Merchant):")
        print(f"  TX ID: {tx_low.tx_id}")
        print(f"  Fee: {fee1:.8f} BTC")
        print(f"  Status: {msg1}")
        
        # Try to add high-fee transaction
        success2, msg2 = temp_mempool.add_transaction(tx_high, self.utxo_manager)
        fee2 = tx_high.calculate_fee(self.utxo_manager)
        
        print(f"\nHigh-fee TX (David -> Attacker):")
        print(f"  TX ID: {tx_high.tx_id}")
        print(f"  Fee: {fee2:.8f} BTC")
        print(f"  Status: {msg2}")
        
        if success1 and not success2:
            print("\n✅ PASSED - First-seen rule enforced (low-fee tx accepted, high-fee rejected)")
        else:
            print("\n❌ FAILED - Should enforce first-seen rule")
    
    def test_9_complete_mining_flow(self):
        """Test 9: Complete Mining Flow"""
        print("Test 9: Complete Mining Flow")
        print("Description: Add transactions, mine block, verify state changes")
        
        # Create a temporary test environment
        test_utxo = UTXOManager()
        test_mempool = Mempool()
        
        # Setup: Give Alice and Bob some BTC
        test_utxo.add_utxo("genesis", 0, 50.0, "Alice")
        test_utxo.add_utxo("genesis", 1, 30.0, "Bob")
        
        print("\nInitial State:")
        print(f"  Alice: {test_utxo.get_balance('Alice'):.8f} BTC")
        print(f"  Bob: {test_utxo.get_balance('Bob'):.8f} BTC")
        print(f"  Miner: {test_utxo.get_balance('Miner'):.8f} BTC")
        
        # Add transactions to mempool
        tx1 = create_simple_transaction("Alice", "Bob", 10.0, test_utxo, fee=0.002)
        tx2 = create_simple_transaction("Bob", "Alice", 5.0, test_utxo, fee=0.003)
        
        test_mempool.add_transaction(tx1, test_utxo)
        test_mempool.add_transaction(tx2, test_utxo)
        
        print(f"\nMempool: {len(test_mempool.transactions)} transactions")
        total_fees = test_mempool.get_total_fees(test_utxo)
        print(f"  Total fees: {total_fees:.8f} BTC")
        
        # Mine block
        block, message = mine_block("Miner", test_mempool, test_utxo, num_txs=5)
        
        print(f"\nMining: {message}")
        print(f"  Block: {block}")
        
        # Verify state changes
        print("\nFinal State:")
        print(f"  Alice: {test_utxo.get_balance('Alice'):.8f} BTC")
        print(f"  Bob: {test_utxo.get_balance('Bob'):.8f} BTC")
        print(f"  Miner: {test_utxo.get_balance('Miner'):.8f} BTC (received fees)")
        print(f"  Mempool: {len(test_mempool.transactions)} transactions")
        
        if len(test_mempool.transactions) == 0 and test_utxo.get_balance("Miner") > 0:
            print("\n✅ PASSED - Mining flow complete")
        else:
            print("\n❌ FAILED - Mining flow incomplete")
    
    def test_10_unconfirmed_chain(self):
        """Test 10: Unconfirmed Chain"""
        print("Test 10: Unconfirmed Chain")
        print("Description: Bob tries to spend UTXO from unconfirmed TX")
        print("Design Decision: REJECT - Cannot spend unconfirmed UTXO")
        
        # Create a temporary test environment
        test_utxo = UTXOManager()
        test_mempool = Mempool()
        
        # Setup
        test_utxo.add_utxo("genesis", 0, 50.0, "Alice")
        
        # TX1: Alice -> Bob (creates new UTXO for Bob, but unconfirmed)
        tx1 = Transaction()
        tx1.add_input("genesis", 0, "Alice")
        tx1.add_output(30.0, "Bob")
        tx1.add_output(19.999, "Alice")  # Change
        
        # Add to mempool (not mined yet)
        success1, msg1 = test_mempool.add_transaction(tx1, test_utxo)
        
        print(f"\nTX1 (Alice -> Bob 30 BTC):")
        print(f"  TX ID: {tx1.tx_id}")
        print(f"  Status: {msg1}")
        print(f"  Confirmed: NO (in mempool only)")
        
        # TX2: Bob tries to spend the UTXO from TX1 (which isn't in UTXO set yet)
        tx2 = Transaction()
        tx2.add_input(tx1.tx_id, 0, "Bob")  # Try to spend unconfirmed output
        tx2.add_output(20.0, "Charlie")
        
        # This should fail because the UTXO doesn't exist in UTXO set yet
        is_valid, msg2 = TransactionValidator.validate_transaction(tx2, test_utxo, test_mempool)
        
        print(f"\nTX2 (Bob -> Charlie 20 BTC):")
        print(f"  TX ID: {tx2.tx_id}")
        print(f"  Trying to spend: ({tx1.tx_id}, 0)")
        print(f"  Status: {msg2}")
        
        if not is_valid and "does not exist" in msg2:
            print("\n✅ PASSED - Correctly rejected spending unconfirmed UTXO")
            print("Design: Cannot spend UTXOs until transaction is mined")
        else:
            print("\n❌ FAILED - Should reject unconfirmed UTXOs")