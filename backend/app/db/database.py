"""DB layer: uses MongoDB (Motor) when reachable, else in-memory store.

This keeps the MVP runnable with zero infra (no mongod needed),
while supporting real Mongo when MONGO_URI is configured.
"""
import logging
from typing import Any, Optional

log = logging.getLogger("app.db")

_MEMORY: dict[str, dict[str, dict]] = {
    "users": {},
    "listings": {},
    "orders": {},
    "bids": {},
    "threads": {},
    "messages": {},
    "reviews": {},
    "notifications": {},
    "resets": {},
    "verifies": {},
    "reports": {},
    "follows": {},
    "payouts": {},
    "prefs": {},
}
USE_MONGO = False
_mongo_db = None


async def init_db():
    global USE_MONGO, _mongo_db
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.core.config import settings

        client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=1500)
        await client.admin.command("ping")
        _mongo_db = client[settings.MONGO_DB]
        USE_MONGO = True
        log.info("Connected to MongoDB")
    except Exception as e:
        USE_MONGO = False
        log.warning(f"MongoDB unavailable, using in-memory store: {e}")


def _match(doc: dict, flt: dict) -> bool:
    if "$or" in flt:
        return any(_match(doc, sub) for sub in flt["$or"])
    for k, v in flt.items():
        if k == "$or":
            continue
        if isinstance(v, dict):
            if "$regex" in v:
                import re
                pat = v["$regex"]
                opts = v.get("$options", "")
                flags = re.IGNORECASE if "i" in opts else 0
                if not re.search(pat, str(doc.get(k, "")), flags):
                    return False
            elif "$gte" in v or "$lte" in v:
                val = doc.get(k)
                if val is None:
                    return False
                if "$gte" in v and val < v["$gte"]:
                    return False
                if "$lte" in v and val > v["$lte"]:
                    return False
            elif "$in" in v:
                dv = doc.get(k)
                allowed = v["$in"]
                if isinstance(dv, list):
                    if not any(x in allowed for x in dv):
                        return False
                elif dv not in allowed:
                    return False
            elif "$ne" in v:
                if doc.get(k) == v["$ne"]:
                    return False
            else:
                if doc.get(k) != v:
                    return False
        else:
            if doc.get(k) != v:
                return False
    return True


class Collection:
    def __init__(self, name: str):
        self.name = name

    @property
    def _mem(self):
        return _MEMORY.setdefault(self.name, {})

    async def insert_one(self, doc: dict):
        if USE_MONGO:
            return await _mongo_db[self.name].insert_one(doc)
        self._mem[doc["_id"]] = doc
        class R:
            inserted_id = doc["_id"]
        return R()

    async def find_one(self, flt: dict) -> Optional[dict]:
        if USE_MONGO:
            return await _mongo_db[self.name].find_one(flt)
        for d in self._mem.values():
            if _match(d, flt):
                return dict(d)
        return None

    async def find_many(self, flt: dict, skip: int = 0, limit: int = 20, sort: Optional[list] = None) -> list[dict]:
        if USE_MONGO:
            cursor = _mongo_db[self.name].find(flt)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip).limit(limit)
            return [d async for d in cursor]
        docs = [dict(d) for d in self._mem.values() if _match(d, flt)]
        if sort:
            for key, direction in reversed(sort):
                docs.sort(key=lambda d: d.get(key, 0), reverse=(direction < 0))
        return docs[skip: skip + limit]

    async def count(self, flt: dict) -> int:
        if USE_MONGO:
            return await _mongo_db[self.name].count_documents(flt)
        return sum(1 for d in self._mem.values() if _match(d, flt))

    async def update_one(self, flt: dict, update: dict):
        if USE_MONGO:
            return await _mongo_db[self.name].update_one(flt, update)
        for _id, d in self._mem.items():
            if _match(d, flt):
                for op, fields in update.items():
                    if op == "$set":
                        d.update(fields)
                    elif op == "$inc":
                        for k, v in fields.items():
                            d[k] = d.get(k, 0) + v
                return
        return None

    async def delete_one(self, flt: dict):
        if USE_MONGO:
            return await _mongo_db[self.name].delete_one(flt)
        for _id, d in list(self._mem.items()):
            if _match(d, flt):
                del self._mem[_id]
                return
        return None


def col(name: str) -> Collection:
    return Collection(name)


def users() -> Collection:
    return col("users")


def listings() -> Collection:
    return col("listings")


def orders() -> Collection:
    return col("orders")


def bids() -> Collection:
    return col("bids")


def threads() -> Collection:
    return col("threads")


def messages() -> Collection:
    return col("messages")


def reviews() -> Collection:
    return col("reviews")


# Token blacklist for logout (in-memory; use Redis in prod)
BLACKLISTED_JTIS: set[str] = set()
