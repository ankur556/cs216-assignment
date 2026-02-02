import abc
import time
from typing import List, Optional, Dict, Tuple
from .models import UTXOModel, TransactionModel, BlockModel
try:
    from google.cloud import firestore
except ImportError:
    firestore = None

class Database(abc.ABC):
    @abc.abstractmethod
    def get_utxos(self, owner: str = None) -> List[UTXOModel]:
        pass

    @abc.abstractmethod
    def get_utxo(self, tx_id: str, index: int) -> Optional[UTXOModel]:
        pass

    @abc.abstractmethod
    def add_utxo(self, utxo: UTXOModel):
        pass

    @abc.abstractmethod
    def remove_utxo(self, tx_id: str, index: int):
        pass

    @abc.abstractmethod
    def get_mempool(self) -> List[TransactionModel]:
        pass

    @abc.abstractmethod
    def add_to_mempool(self, tx: TransactionModel):
        pass

    @abc.abstractmethod
    def remove_from_mempool(self, tx_id: str):
        pass

    @abc.abstractmethod
    def get_blockchain(self) -> List[BlockModel]:
        pass

    @abc.abstractmethod
    def add_block(self, block: BlockModel):
        pass
    
    @abc.abstractmethod
    def reset_system(self, genesis_utxos: List[UTXOModel]):
        pass

class InMemoryDatabase(Database):
    def __init__(self):
        self.utxos: Dict[Tuple[str, int], UTXOModel] = {}
        self.mempool: List[TransactionModel] = []
        self.chain: List[BlockModel] = []
        print("Initialized InMemoryDatabase")

    def get_utxos(self, owner: str = None) -> List[UTXOModel]:
        if owner:
            return [u for u in self.utxos.values() if u.owner == owner]
        return list(self.utxos.values())

    def get_utxo(self, tx_id: str, index: int) -> Optional[UTXOModel]:
        return self.utxos.get((tx_id, index))

    def add_utxo(self, utxo: UTXOModel):
        self.utxos[(utxo.tx_id, utxo.index)] = utxo

    def remove_utxo(self, tx_id: str, index: int):
        if (tx_id, index) in self.utxos:
            del self.utxos[(tx_id, index)]

    def get_mempool(self) -> List[TransactionModel]:
        return self.mempool

    def add_to_mempool(self, tx: TransactionModel):
        self.mempool.append(tx)

    def remove_from_mempool(self, tx_id: str):
        self.mempool = [tx for tx in self.mempool if tx.tx_id != tx_id]

    def get_blockchain(self) -> List[BlockModel]:
        # Return last 20 blocks, newest first
        return self.chain[::-1][:20]

    def add_block(self, block: BlockModel):
        self.chain.append(block)

    def reset_system(self, genesis_utxos: List[UTXOModel]):
        self.utxos.clear()
        self.mempool.clear()
        self.chain.clear()
        for utxo in genesis_utxos:
            self.add_utxo(utxo)

class FirestoreDatabase(Database):
    def __init__(self, project_id: str = None):
        self.db = firestore.Client(project=project_id)
        print(f"Initialized FirestoreDatabase with project {self.db.project}")

    def get_utxos(self, owner: str = None) -> List[UTXOModel]:
        query = self.db.collection('utxos')
        if owner:
            query = query.where('owner', '==', owner)
        docs = query.stream()
        return [UTXOModel(**doc.to_dict()) for doc in docs]

    def get_utxo(self, tx_id: str, index: int) -> Optional[UTXOModel]:
        # Helper ID format: tx_id:index
        doc_id = f"{tx_id}:{index}"
        doc = self.db.collection('utxos').document(doc_id).get()
        if doc.exists:
            return UTXOModel(**doc.to_dict())
        return None

    def add_utxo(self, utxo: UTXOModel):
        doc_id = f"{utxo.tx_id}:{utxo.index}"
        self.db.collection('utxos').document(doc_id).set(utxo.dict())

    def remove_utxo(self, tx_id: str, index: int):
        doc_id = f"{tx_id}:{index}"
        self.db.collection('utxos').document(doc_id).delete()

    def get_mempool(self) -> List[TransactionModel]:
        docs = self.db.collection('mempool').stream()
        return [TransactionModel(**doc.to_dict()) for doc in docs]

    def add_to_mempool(self, tx: TransactionModel):
        self.db.collection('mempool').document(tx.tx_id).set(tx.dict())

    def remove_from_mempool(self, tx_id: str):
        self.db.collection('mempool').document(tx_id).delete()

    def get_blockchain(self) -> List[BlockModel]:
        # Limit to last 20 blocks to prevent huge reads
        docs = self.db.collection('blocks').order_by('block_number', direction=firestore.Query.DESCENDING).limit(20).stream()
        return [BlockModel(**doc.to_dict()) for doc in docs]

    def add_block(self, block: BlockModel):
        self.db.collection('blocks').document(str(block.block_number)).set(block.dict())

    def reset_system(self, genesis_utxos: List[UTXOModel]):
        # This is expensive in Firestore, but okay for Admin tool
        # Batch delete
        batch = self.db.batch()
        
        # Delete UTXOs
        for doc in self.db.collection('utxos').list_documents():
            batch.delete(doc)
            
        # Delete Mempool
        for doc in self.db.collection('mempool').list_documents():
            batch.delete(doc)

        # Delete Operations
        batch.commit()
        
        # Delete Blocks (separate batch to avoid limits, although basic impl here)
        blocks = self.db.collection('blocks').list_documents()
        for doc in blocks:
            doc.delete()

        # Add Genesis
        for utxo in genesis_utxos:
            self.add_utxo(utxo)

# Global DB instance
db: Database = InMemoryDatabase() # Default to InMemory

def get_db() -> Database:
    return db

def init_db(use_firestore: bool = False):
    global db
    if use_firestore:
        try:
            db = FirestoreDatabase()
        except Exception as e:
            print(f"Failed to init Firestore: {e}. Falling back to InMemory.")
            db = InMemoryDatabase()
    else:
        db = InMemoryDatabase()
