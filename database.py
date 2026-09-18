"""
MongoDB storage for machine configurations, with an automatic
in-memory fallback so the project runs immediately even without
MongoDB installed (useful for demos / first run in VS Code).

Set MONGO_URI in a .env file to point at a real MongoDB instance:
    MONGO_URI=mongodb://localhost:27017
"""
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

_in_memory_store: dict[str, dict] = {}
_use_mongo = False
_collection = None

if MONGO_URI:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        _db = _client["digital_twin_db"]
        _collection = _db["machines"]
        _use_mongo = True
    except Exception as e:
        print(f"[database] Could not connect to MongoDB, falling back to in-memory store: {e}")
        _use_mongo = False


async def save_machine(machine: dict):
    if _use_mongo:
        await _collection.update_one({"id": machine["id"]}, {"$set": machine}, upsert=True)
    else:
        _in_memory_store[machine["id"]] = machine


async def delete_machine(machine_id: str):
    if _use_mongo:
        await _collection.delete_one({"id": machine_id})
    else:
        _in_memory_store.pop(machine_id, None)


async def get_all_machines() -> list[dict]:
    if _use_mongo:
        cursor = _collection.find({})
        return [doc async for doc in cursor]
    else:
        return list(_in_memory_store.values())


async def clear_all():
    if _use_mongo:
        await _collection.delete_many({})
    else:
        _in_memory_store.clear()
