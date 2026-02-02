from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TransactionInput(BaseModel):
    prev_tx: str
    index: int
    owner: str

class TransactionOutput(BaseModel):
    amount: float
    address: str

class TransactionModel(BaseModel):
    tx_id: str
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]
    timestamp: Optional[int] = None
    status: str = "pending"  # pending, confirmed

class BlockModel(BaseModel):
    block_number: int
    previous_hash: str
    miner: str
    transactions: List[TransactionModel]
    total_fees: float
    timestamp: int
    hash: str

class UTXOModel(BaseModel):
    tx_id: str
    index: int
    amount: float
    owner: str

class CreateTransactionRequest(BaseModel):
    sender: str
    recipient: str
    amount: float
    fee: float = 0.001

class MineBlockRequest(BaseModel):
    miner_address: str
    num_txs: int = 5

class GenesisRequest(BaseModel):
    initial_allocations: Dict[str, float]
