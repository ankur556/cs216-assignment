# Bitcoin UTXO Simulator

**CS 216: Introduction to Blockchain - Assignment 2**

A comprehensive Python implementation of Bitcoin's UTXO (Unspent Transaction Output) model, transaction validation, mempool management, and mining simulation.

## Team Information

**Team Name:**: Just Hash it

**Team Members:**
1. Ankur - 240001009
2. Anurag Prasad - 240001011
3. Saransh Halwai - 240001066
4. Vavadiya Rudra Bhaveshbhai - 240041038

## Project Overview

This simulator demonstrates the core mechanisms of Bitcoin's transaction system:
- UTXO model for tracking spendable coins
- Transaction creation and validation
- Mempool for unconfirmed transactions
- Double-spending prevention
- Mining and block creation
- Transaction lifecycle from creation to confirmation

## Features Implemented

### ✅ Part 1: UTXO Manager (3 marks)
- Add/remove UTXOs
- Balance calculation
- UTXO existence checking
- Owner-based UTXO retrieval

### ✅ Part 2: Transaction Structure & Validation (4 marks)
All 5 validation rules implemented:
1. All inputs must exist in UTXO set
2. No double-spending in inputs
3. Sum(inputs) ≥ Sum(outputs)
4. No negative amounts in outputs
5. No conflict with mempool

### ✅ Part 3: Mempool Management (3 marks)
- Transaction validation before adding
- Conflict detection with spent UTXOs
- Fee-based prioritization
- Mempool size limits with eviction

### ✅ Part 4: Mining Simulation (3 marks)
- Transaction selection by fee
- UTXO set updates (permanent)
- Coinbase transaction creation
- Mempool cleanup

### ✅ Part 5: Double-Spending Prevention (2 marks)
- Simple double-spend detection
- Mempool conflict prevention
- Race attack simulation (first-seen rule)

### ✅ All 10 Mandatory Test Cases
1. ✅ Basic Valid Transaction
2. ✅ Multiple Inputs
3. ✅ Double-Spend in Same Transaction
4. ✅ Mempool Double-Spend
5. ✅ Insufficient Funds
6. ✅ Negative Amount
7. ✅ Zero Fee Transaction
8. ✅ Race Attack Simulation
9. ✅ Complete Mining Flow
10. ✅ Unconfirmed Chain

## Repository Structure

```
CS216-UTXO-Simulator/
├── src/
│   ├── main.py              # Main program entry point
│   ├── utxo_manager.py      # UTXO handling class
│   ├── transaction.py       # Transaction class/structure
│   ├── mempool.py           # Mempool management
│   ├── validator.py         # Validation logic
│   ├── block.py             # Block/mining logic
│   └── test_scenarios.py    # Test cases
├── README.md                # This file
├── requirements.txt         # Dependencies (empty - uses only standard library)
└── sample_output.txt        # Sample program execution
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- No external dependencies required (uses only Python standard library)

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/CS216-UTXO-Simulator.git
cd CS216-UTXO-Simulator
```

2. Verify Python installation:
```bash
python --version  # or python3 --version
```

3. Run the simulator:
```bash
python src/main.py  # or python3 src/main.py
```

## How to Run

### Basic Usage

```bash
cd src
python main.py
```

### Interactive Menu

The program provides an interactive menu with the following options:

```
1. Create new transaction  - Create and validate transactions
2. View UTXO set          - See all unspent transaction outputs
3. View mempool           - View pending transactions
4. Mine block             - Simulate mining process
5. Run test scenarios     - Execute all 10 test cases
6. View blockchain        - Display mined blocks
7. Check balance          - Check address balance
8. Exit                   - Exit program
```

## Usage Examples

### Example 1: Creating a Transaction

```
Enter choice: 1
Enter sender address: Alice
Available balance: 50.00000000 BTC
Enter recipient address: Bob
Enter amount (BTC): 10
Enter fee (BTC) [default: 0.001]: 0.001

Transaction Details:
  TX ID: tx_1738377600123_4567
  From: Alice
  To: Bob
  Amount: 10.00000000 BTC
  Fee: 0.00100000 BTC
  Change: 39.99900000 BTC (back to Alice)

Validation: Valid transaction. Fee: 0.00100000 BTC
✓ Transaction added to mempool
```

### Example 2: Mining a Block

```
Enter choice: 4
Enter miner address: Miner1
Number of transactions to include [max 3]: 3

Mining block...
  Miner: Miner1
  Transactions to include: 3

✓ Block mined successfully with 3 transactions and 0.00300000 BTC in fees
  Block #1
  Transactions mined: 3
  Total fees: 0.00300000 BTC
  Miner reward: 0.00300000 BTC to Miner1
  Remaining in mempool: 0
```

### Example 3: Running Test Scenarios

```
Enter choice: 5

Running Test Scenarios

============================================================
Test 1
============================================================
Test 1: Basic Valid Transaction
Description: Alice sends 10 BTC to Bob with change and fee

Transaction Details:
  TX ID: tx_1738377601234_5678
  Sender: Alice
  Recipient: Bob
  Amount: 10.0 BTC
  Fee: 0.001 BTC
  Change: 39.99900000 BTC back to Alice

Validation: Valid transaction. Fee: 0.00100000 BTC
Mempool: Valid transaction. Fee: 0.00100000 BTC
✅ PASSED
```

## Design Decisions

### 1. UTXO Storage
- **Data Structure:** Dictionary with (tx_id, index) tuple as key
- **Rationale:** O(1) lookup time for existence checks
- **Trade-off:** Memory vs. speed (optimized for speed)

### 2. Mempool Conflict Detection
- **Approach:** Maintain a `spent_utxos` set tracking promised UTXOs
- **Rationale:** Fast O(1) conflict checking
- **First-Seen Rule:** First valid transaction wins, later conflicting transactions rejected

### 3. Transaction Fee Model
- **Formula:** `fee = Sum(inputs) - Sum(outputs)`
- **Zero Fee:** Allowed (valid in Bitcoin protocol)
- **Negative Fee:** Impossible (validation rejects if inputs < outputs)

### 4. Unconfirmed Chain (Test 10)
- **Design Decision:** REJECT unconfirmed UTXOs
- **Rationale:** Simpler and safer - UTXOs only spendable after mining
- **Alternative:** Could track dependencies but adds complexity

### 5. Mining Transaction Selection
- **Strategy:** Fee-based priority (highest fee first)
- **Rationale:** Matches real Bitcoin miner incentives
- **Limitation:** Doesn't consider transaction size (simplified)

## Key Implementation Details

### Transaction Validation Rules

```python
# Rule 1: All inputs must exist
if not utxo_manager.exists(tx_id, index):
    return False, "Input UTXO does not exist"

# Rule 2: No double-spending in same transaction
if input_key in seen_inputs:
    return False, "Double-spend in same transaction"

# Rule 3: Sum(inputs) >= Sum(outputs)
if total_input < total_output:
    return False, "Insufficient inputs"

# Rule 4: No negative amounts
if output["amount"] < 0:
    return False, "Negative output amount"

# Rule 5: No mempool conflicts
if input_key in mempool.spent_utxos:
    return False, "UTXO already spent in mempool"
```

### Mining Process

```python
def mine_block(miner_address, mempool, utxo_manager, num_txs):
    # 1. Select transactions (by fee)
    selected_txs = mempool.get_top_transactions(num_txs, utxo_manager)
    
    # 2. Update UTXO set permanently
    for tx in selected_txs:
        # Remove inputs (spent)
        for inp in tx.inputs:
            utxo_manager.remove_utxo(inp["prev_tx"], inp["index"])
        
        # Add outputs (created)
        for index, output in enumerate(tx.outputs):
            utxo_manager.add_utxo(tx.tx_id, index, output["amount"], output["address"])
    
    # 3. Create coinbase transaction
    coinbase_tx = create_coinbase(total_fees, miner_address)
    utxo_manager.add_utxo(coinbase_tx.tx_id, 0, total_fees, miner_address)
    
    # 4. Clear mempool
    for tx in selected_txs:
        mempool.remove_transaction(tx.tx_id)
```

## Testing

### Running All Tests

```bash
python src/main.py
# Choose option 5 from menu
```

### Test Coverage
- ✅ Valid transactions with change outputs
- ✅ Multiple input aggregation
- ✅ Double-spend detection (same TX)
- ✅ Mempool conflict prevention
- ✅ Insufficient funds handling
- ✅ Invalid input validation
- ✅ Zero-fee transactions
- ✅ Race attack scenarios
- ✅ Complete mining workflow
- ✅ Unconfirmed UTXO handling

## Limitations & Future Enhancements

### Current Limitations
1. No cryptographic signatures (simulated with string comparison)
2. No networking/distributed consensus
3. No Proof-of-Work computation
4. Simplified fee model (doesn't consider transaction size)
5. No transaction replacement (RBF)
6. No blockchain reorganization

### Potential Enhancements
1. Add real ECDSA signatures
2. Implement transaction scripting (Script language)
3. Add blockchain fork handling
4. Implement Replace-By-Fee (RBF)
5. Add transaction size-based fee calculation
6. Persistent storage (database)
7. Multi-signature support
8. Segregated Witness (SegWit) support

## Technical Specifications

### System Requirements
- **OS:** Windows, macOS, or Linux
- **Python:** 3.8+
- **Memory:** Minimal (runs in-memory)
- **Storage:** No database required

### Performance Characteristics
- **UTXO Lookup:** O(1)
- **Balance Calculation:** O(n) where n = total UTXOs
- **Transaction Validation:** O(m) where m = inputs
- **Mining:** O(k log k) where k = mempool size (sorting)

## Educational Value

### Concepts Demonstrated

1. **UTXO Model vs Account Model**
   - Shows how Bitcoin tracks balances differently than Ethereum
   - Demonstrates why "account balance" is derived, not stored

2. **Double-Spending Prevention**
   - Multi-layer protection (validation → mempool → blockchain)
   - First-seen rule in mempool

3. **Transaction Lifecycle**
   - Creation → Validation → Mempool → Mining → Confirmation

4. **Miner Incentives**
   - Fee-based transaction selection
   - Economic security through rewards

5. **State Transitions**
   - How UTXO set evolves with each block
   - Finality through mining
###🚀 Advanced Features (Extended Implementation)
Beyond the core requirements, our team implemented a full-stack suite to bring the simulation to life:

1.Interactive Web Dashboard: We developed a web-based GUI with a full backend, allowing users to run and visualize the UTXO simulation on a live server rather than just the CLI.

2.Parallelized Marketplace: An integrated marketplace utilizing the same UTXO logic. It handles high-concurrency transactions with strict parallelism rules to ensure zero double-spending in a live trading environment.

3.FastAPI Integration: All core simulator functions are exposed via FastAPI, maintaining Python's simplicity while providing a robust RESTful API.

Secure Access: Added a dedicated Login Page to manage user sessions and improve the overall interactive experience.
## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError`
- **Solution:** Make sure you're running from the `src/` directory or use `python src/main.py`

**Issue:** Transaction rejected with "UTXO does not exist"
- **Solution:** Check that the sender has available UTXOs (use option 2 to view UTXO set)

**Issue:** Cannot mine block (no transactions)
- **Solution:** Create transactions first (option 1) before mining (option 4)

**Issue:** Mempool full
- **Solution:** Mine a block to clear mempool, or create higher-fee transactions

## References

### Assignment Materials
- Course Lecture Slides (L3.pdf, Pages 7-37)
- Bitcoin Whitepaper (Sections 2, 5, 6)
- Assignment Specification PDF

### Additional Resources
- [Bitcoin Developer Guide](https://developer.bitcoin.org/devguide/)
- [Mastering Bitcoin](https://github.com/bitcoinbook/bitcoinbook)
- [Bitcoin Wiki - UTXO](https://en.bitcoin.it/wiki/UTXO)

## License

This project is created for educational purposes as part of CS 216 coursework.

## Acknowledgments

- Course Instructor and TAs for guidance
- Bitcoin Core developers for the original implementation
- Team members for collaboration

---

**Submission Date:** February 3, 2025  
**Course:** CS 216 - Introduction to Blockchain  
**Assignment:** Bitcoin Transaction & UTXO Simulator
