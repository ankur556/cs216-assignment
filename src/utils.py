from src import utxo_manager
from src.mempool import Mempool
from src.utxo_manager import UTXOManager

def validate_transaction(tx, utxo_manager):
    """
    Validate a transaction by checking if all its inputs exist in the UTXO set.
    """
    pass


def mine_block ( miner_address : str , mempool : Mempool , utxo_manager : UTXOManager , num_txs =5) :
    """
    Simulate mining a block .
    1. Select top transactions from mempool
    2. Update UTXO set ( remove inputs , add outputs )
    3. Add miner fee as special UTXO
    4. Remove mined transactions from mempool
    """
    pass

