"""
Bitcoin UTXO Simulator - Main Program
CS 216: Introduction to Blockchain
"""

from utxo_manager import UTXOManager
from mempool import Mempool
from transaction import Transaction, create_simple_transaction
from validator import TransactionValidator
from block import mine_block, Blockchain
from test_scenarios import TestScenarios


class BitcoinSimulator:
    """Main simulator class with interactive interface"""
    
    def __init__(self):
        """Initialize the simulator with genesis UTXOs"""
        self.utxo_manager = UTXOManager()
        self.mempool = Mempool(max_size=50)
        self.blockchain = Blockchain()
        self.validator = TransactionValidator()
        
        # Initialize genesis UTXOs (as specified in assignment)
        self._initialize_genesis()
    
    def _initialize_genesis(self):
        """Create initial UTXOs (Genesis Block)"""
        genesis_utxos = [
            ("Alice", 50.0),
            ("Bob", 30.0),
            ("Charlie", 20.0),
            ("David", 10.0),
            ("Eve", 5.0)
        ]
        
        for index, (owner, amount) in enumerate(genesis_utxos):
            self.utxo_manager.add_utxo("genesis", index, amount, owner)
    
    def display_banner(self):
        """Display welcome banner"""
        print("\n" + "="*60)
        print("=== Bitcoin Transaction Simulator ===")
        print("="*60)
        print("\nInitial UTXOs (Genesis Block):")
        print("  - Alice: 50.0 BTC")
        print("  - Bob: 30.0 BTC")
        print("  - Charlie: 20.0 BTC")
        print("  - David: 10.0 BTC")
        print("  - Eve: 5.0 BTC")
        print(f"\nTotal Supply: {self.utxo_manager.get_total_supply():.8f} BTC")
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("Main Menu:")
        print("="*60)
        print("1. Create new transaction")
        print("2. View UTXO set")
        print("3. View mempool")
        print("4. Mine block")
        print("5. Run test scenarios")
        print("6. View blockchain")
        print("7. Check balance")
        print("8. Exit")
        print("="*60)
    
    def create_transaction_interactive(self):
        """Interactive transaction creation"""
        print("\n--- Create New Transaction ---")
        
        # Get sender
        sender = input("Enter sender address: ").strip()
        
        # Check balance
        balance = self.utxo_manager.get_balance(sender)
        print(f"Available balance: {balance:.8f} BTC")
        
        if balance <= 0:
            print(f"Error: {sender} has no funds")
            return
        
        # Get recipient
        recipient = input("Enter recipient address: ").strip()
        
        # Get amount
        try:
            amount = float(input("Enter amount (BTC): ").strip())
        except ValueError:
            print("Error: Invalid amount")
            return
        
        if amount <= 0:
            print("Error: Amount must be positive")
            return
        
        # Get fee (optional)
        try:
            fee_input = input("Enter fee (BTC) [default: 0.001]: ").strip()
            fee = float(fee_input) if fee_input else 0.001
        except ValueError:
            fee = 0.001
        
        # Create transaction
        print("\nCreating transaction...")
        tx = create_simple_transaction(sender, recipient, amount, self.utxo_manager, fee)
        
        if not tx:
            print(f"Error: Insufficient funds. {sender} needs {amount + fee:.8f} BTC (including fee)")
            return
        
        # Display transaction details
        print(f"\nTransaction Details:")
        print(f"  TX ID: {tx.tx_id}")
        print(f"  From: {sender}")
        print(f"  To: {recipient}")
        print(f"  Amount: {amount:.8f} BTC")
        
        # Calculate change
        total_input = sum(
            self.utxo_manager.get_utxo(inp["prev_tx"], inp["index"])["amount"]
            for inp in tx.inputs
        )
        change = total_input - amount - fee
        
        print(f"  Fee: {fee:.8f} BTC")
        if change > 0:
            print(f"  Change: {change:.8f} BTC (back to {sender})")
        
        # Validate
        is_valid, message = self.validator.validate_transaction(tx, self.utxo_manager, self.mempool)
        print(f"\nValidation: {message}")
        
        if is_valid:
            # Add to mempool
            success, msg = self.mempool.add_transaction(tx, self.utxo_manager)
            if success:
                print(f"✓ Transaction added to mempool")
                print(f"  Mempool now has {len(self.mempool.transactions)} transaction(s)")
            else:
                print(f"✗ Failed to add to mempool: {msg}")
        else:
            print("✗ Transaction validation failed")
    
    def view_utxo_set(self):
        """Display current UTXO set"""
        self.utxo_manager.display_utxos()
        print(f"Total Supply: {self.utxo_manager.get_total_supply():.8f} BTC")
    
    def view_mempool(self):
        """Display mempool contents"""
        self.mempool.display(self.utxo_manager)
        if self.mempool.transactions:
            total_fees = self.mempool.get_total_fees(self.utxo_manager)
            print(f"Total fees in mempool: {total_fees:.8f} BTC")
    
    def mine_block_interactive(self):
        """Interactive block mining"""
        print("\n--- Mine Block ---")
        
        if not self.mempool.transactions:
            print("Error: No transactions in mempool to mine")
            return
        
        miner_address = input("Enter miner address: ").strip()
        
        try:
            num_txs_input = input(f"Number of transactions to include [max {len(self.mempool.transactions)}]: ").strip()
            num_txs = int(num_txs_input) if num_txs_input else len(self.mempool.transactions)
        except ValueError:
            num_txs = len(self.mempool.transactions)
        
        print(f"\nMining block...")
        print(f"  Miner: {miner_address}")
        print(f"  Transactions to include: {num_txs}")
        
        # Get fees before mining
        selected_txs = self.mempool.get_top_transactions(num_txs, self.utxo_manager)
        total_fees = sum(tx.calculate_fee(self.utxo_manager) for tx in selected_txs)
        
        # Mine block
        block, message = mine_block(miner_address, self.mempool, self.utxo_manager, num_txs)
        
        if block:
            self.blockchain.add_block(block)
            print(f"\n✓ {message}")
            print(f"  Block #{block.block_number}")
            print(f"  Transactions mined: {len(block.transactions)}")
            print(f"  Total fees: {total_fees:.8f} BTC")
            print(f"  Miner reward: {total_fees:.8f} BTC to {miner_address}")
            print(f"  Remaining in mempool: {len(self.mempool.transactions)}")
        else:
            print(f"\n✗ Mining failed: {message}")
    
    def run_test_scenarios(self):
        """Run all test scenarios"""
        # Save current state
        saved_utxo = self.utxo_manager.utxo_set.copy()
        saved_mempool_txs = self.mempool.transactions.copy()
        saved_mempool_spent = self.mempool.spent_utxos.copy()
        
        print("\n" + "="*60)
        print("Running Test Scenarios")
        print("="*60)
        print("\nNote: Tests will use current system state.")
        print("System state will be restored after tests.\n")
        
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Tests cancelled")
            return
        
        # Run tests
        test_runner = TestScenarios(self.utxo_manager, self.mempool)
        test_runner.run_all_tests()
        
        # Restore state
        self.utxo_manager.utxo_set = saved_utxo
        self.mempool.transactions = saved_mempool_txs
        self.mempool.spent_utxos = saved_mempool_spent
        
        print("\n✓ System state restored")
    
    def view_blockchain(self):
        """Display blockchain"""
        self.blockchain.display()
    
    def check_balance(self):
        """Check balance for an address"""
        print("\n--- Check Balance ---")
        address = input("Enter address: ").strip()
        balance = self.utxo_manager.get_balance(address)
        
        print(f"\n{address}: {balance:.8f} BTC")
        
        # Show UTXOs
        utxos = self.utxo_manager.get_utxos_for_owner(address)
        if utxos:
            print(f"\nUTXOs ({len(utxos)}):")
            for tx_id, index, amount in utxos:
                print(f"  - ({tx_id}, {index}): {amount:.8f} BTC")
    
    def run(self):
        """Main program loop"""
        self.display_banner()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEnter choice (1-8): ").strip()
                
                if choice == '1':
                    self.create_transaction_interactive()
                elif choice == '2':
                    self.view_utxo_set()
                elif choice == '3':
                    self.view_mempool()
                elif choice == '4':
                    self.mine_block_interactive()
                elif choice == '5':
                    self.run_test_scenarios()
                elif choice == '6':
                    self.view_blockchain()
                elif choice == '7':
                    self.check_balance()
                elif choice == '8':
                    print("\n" + "="*60)
                    print("Thank you for using Bitcoin UTXO Simulator!")
                    print("="*60)
                    break
                else:
                    print("\n✗ Invalid choice. Please enter 1-8.")
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Entry point"""
    simulator = BitcoinSimulator()
    simulator.run()


if __name__ == "__main__":
    main()