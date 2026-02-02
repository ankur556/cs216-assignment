import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

from .models import (
    TransactionModel, BlockModel, UTXOModel, 
    CreateTransactionRequest, MineBlockRequest, GenesisRequest
)
from .database import init_db, get_db
from .logic import BitcoinService

app = FastAPI(title="Bitcoin UTXO Simulator API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Initialize DB
# Check for GOOGLE_CLOUD_PROJECT to decide if we use Firestore or InMemory
use_firestore = bool(os.environ.get("GOOGLE_CLOUD_PROJECT")) or bool(os.environ.get("USE_FIRESTORE"))
init_db(use_firestore)

def get_service():
    return BitcoinService(get_db())

# Routes
@app.get("/api/balance/{address}")
def get_balance(address: str):
    service = get_service()
    return {"address": address, "balance": service.get_balance(address)}

@app.get("/api/utxos/{address}", response_model=List[UTXOModel])
def get_utxos(address: str):
    return get_db().get_utxos(address)

@app.get("/api/mempool", response_model=List[TransactionModel])
def get_mempool():
    return get_db().get_mempool()

@app.post("/api/transaction")
def create_transaction(req: CreateTransactionRequest):
    service = get_service()
    tx, msg = service.create_transaction(req.sender, req.recipient, req.amount, req.fee)
    if not tx:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "tx": tx}

@app.post("/api/mine")
def mine_block(req: MineBlockRequest):
    service = get_service()
    block, msg = service.mine_block(req.miner_address, req.num_txs)
    if not block:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "block": block}

@app.get("/api/blockchain", response_model=List[BlockModel])
def get_blockchain():
    return get_db().get_blockchain()

@app.post("/api/admin/genesis")
def init_genesis(req: GenesisRequest):
    service = get_service()
    service.init_genesis(req.initial_allocations)
    return {"status": "success", "message": "System reset with new genesis state"}

@app.post("/api/admin/reset")
def reset_system():
    # Default genesis
    default_alloc = {
        "Alice": 50.0,
        "Bob": 30.0,
        "Charlie": 20.0,
        "David": 10.0,
        "Eve": 5.0
    }
    service = get_service()
    service.init_genesis(default_alloc)
    return {"status": "success", "message": "System reset to default genesis"}

# Serve Frontend
app.mount("/", StaticFiles(directory="api/static", html=True), name="static")
