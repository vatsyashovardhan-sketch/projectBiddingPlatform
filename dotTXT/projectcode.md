# Project Code Dump

All handwritten source / config files with their file paths. Excluded: installed modules/libraries/build output (node_modules, dist, package-lock.json), VCS (.git), caches (__pycache__, .pytest_cache), uploads/binaries, secrets (backend/.env), and this file itself.

Total files: 64

## Index

- `.github/workflows/ci.yml`
- `.gitignore`
- `backend/.env.example`
- `backend/app/__init__.py`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py`
- `backend/app/core/deps.py`
- `backend/app/core/notify.py`
- `backend/app/core/ratelimit.py`
- `backend/app/core/security.py`
- `backend/app/core/seed_data.py`
- `backend/app/db/__init__.py`
- `backend/app/db/database.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/models/schemas.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/admin.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/bidding.py`
- `backend/app/routers/jobs.py`
- `backend/app/routers/listings.py`
- `backend/app/routers/messages.py`
- `backend/app/routers/notifications.py`
- `backend/app/routers/orders.py`
- `backend/app/routers/reviews.py`
- `backend/app/routers/uploads.py`
- `backend/app/routers/users.py`
- `backend/audit_features.py`
- `backend/backfill_ratings.js`
- `backend/cleanup_demo.js`
- `backend/cleanup_seed.js`
- `backend/demo_delete.py`
- `backend/requirements.txt`
- `backend/seed.py`
- `backend/tests/__init__.py`
- `backend/tests/test_phase2.py`
- `backend/verify_seed.py`
- `frontend/.env.example`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/src/api.js`
- `frontend/src/App.jsx`
- `frontend/src/AuthContext.jsx`
- `frontend/src/main.jsx`
- `frontend/src/Nav.jsx`
- `frontend/src/pages/Admin.jsx`
- `frontend/src/pages/Auth.jsx`
- `frontend/src/pages/Bids.jsx`
- `frontend/src/pages/Browse.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/EditListing.jsx`
- `frontend/src/pages/ListingDetail.jsx`
- `frontend/src/pages/Messages.jsx`
- `frontend/src/pages/NewListing.jsx`
- `frontend/src/pages/Notifications.jsx`
- `frontend/src/pages/Password.jsx`
- `frontend/src/pages/Reviews.jsx`
- `frontend/src/pages/SellerProfile.jsx`
- `frontend/src/pages/Sellers.jsx`
- `frontend/src/styles.css`
- `frontend/vite.config.js`
- `prompt.txt`
- `README.md`

---

## File: `.github/workflows/ci.yml`

```yaml
name: ci
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt pytest httpx
        working-directory: .
      - run: pytest -q
        working-directory: backend
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
```

## File: `.gitignore`

```text
__pycache__/
*.pyc
.venv/
.env
backend/uploads/previews/*
backend/uploads/files/*
!backend/uploads/previews/.gitkeep
!backend/uploads/files/.gitkeep
node_modules/
dist/
*.log
_dev.log*
```

## File: `backend/.env.example`

```text
# Copy to .env and fill in
MONGO_URI=mongodb://localhost:27017
MONGO_DB=projectbidding
JWT_SECRET=change-me-to-a-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://localhost:5173
# Stripe (optional for MVP — mock mode when blank)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_CONNECT_WEBHOOK_SECRET=
PLATFORM_FEE_PERCENT=10
# S3 (optional for MVP — local disk when USE_S3=false)
USE_S3=false
S3_BUCKET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
```

## File: `backend/app/__init__.py`

```python

```

## File: `backend/app/core/__init__.py`

```python

```

## File: `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "projectbidding"
    JWT_SECRET: str = "change-me-to-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:5173"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PLATFORM_FEE_PERCENT: float = 10.0
    USE_S3: bool = False
    S3_BUCKET: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

CATEGORIES = [
    "Web App",
    "Mobile App",
    "ML/AI Project",
    "Final Year Project",
    "Game",
    "Script/Tool",
    "Other",
]

LISTING_STATUSES = ["draft", "active", "sold", "removed"]
ORDER_STATUSES = ["pending", "paid", "delivered", "completed", "disputed"]
```

## File: `backend/app/core/deps.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.database import BLACKLISTED_JTIS, users

bearer = HTTPBearer(auto_error=False)


async def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    if payload.get("jti") in BLACKLISTED_JTIS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Logged out")
    user = await users().find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.get("banned"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
    user["id"] = user.pop("_id")
    return user


def require_roles(*roles: str):
    async def checker(user: dict = Depends(get_current_user)):
        # "both" can do everything buyer/seller can
        user_roles = {user.get("role", "buyer"), "both"} if user.get("role") == "both" else {user.get("role")}
        if user.get("role") == "both":
            return user
        if user.get("role") not in roles and "both" not in roles:
            # allow "both" users through regardless
            if not (set(roles) & user_roles):
                raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker


async def require_seller(user: dict = Depends(get_current_user)):
    if user.get("role") not in ("seller", "both", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers can perform this action")
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
```

## File: `backend/app/core/notify.py`

```python
"""In-app notifications + email stub (Resend/SendGrid when keys set)."""
import logging
import os
from app.core.security import new_id, utcnow
from app.db import database as db

log = logging.getLogger("app.notify")


async def notify(user_id: str, kind: str, title: str, link: str = ""):
    # respect prefs
    prefs = await db.col("prefs").find_one({"_id": f"prefs:{user_id}"})
    if prefs and prefs.get("opt_out", {}).get(kind):
        return
    await db.col("notifications").insert_one({
        "_id": new_id(), "user_id": user_id, "kind": kind, "title": title,
        "link": link, "read": False, "created_at": utcnow().isoformat(),
    })


async def notify_email(to: str, subject: str, body: str):
    key = os.environ.get("RESEND_API_KEY") or os.environ.get("SENDGRID_API_KEY")
    if key:
        log.info(f"[email via provider] to={to} subject={subject}")
        # wire Resend/SendGrid send here in prod
    else:
        log.info(f"[email mock] to={to} subject={subject} :: {body[:120]}")


async def update_listing_rating(listing_id: str):
    revs = await db.col("reviews").find_many({"listing_id": listing_id}, limit=500)
    if revs:
        avg = round(sum(r["rating"] for r in revs) / len(revs), 2)
        await db.col("listings").update_one({"_id": listing_id}, {"$set": {"rating": avg, "rating_count": len(revs),
                                                                           "rating_weighted": weighted_rating(revs)}})
    # denormalize seller rating onto all their listings (powers rating filter/sort on active listings)
    lst = await db.col("listings").find_one({"_id": listing_id})
    if lst:
        s_revs = await db.col("reviews").find_many({"seller_id": lst["seller_id"]}, limit=2000)
        if s_revs:
            s_avg = round(sum(r["rating"] for r in s_revs) / len(s_revs), 2)
            all_sell = await db.col("listings").find_many({"seller_id": lst["seller_id"]}, limit=2000)
            for l in all_sell:
                await db.col("listings").update_one({"_id": l["_id"]}, {"$set": {"seller_rating": s_avg,
                                                                                "seller_rating_count": len(s_revs)}})


def weighted_rating(revs: list) -> float:
    """Time-weighted avg: reviews from the last 90 days count 2x (recent reviews count more)."""
    from datetime import datetime, timedelta
    if not revs:
        return 0
    cutoff = (utcnow() - timedelta(days=90)).isoformat()
    num = den = 0
    for r in revs:
        w = 2 if r.get("created_at", "") >= cutoff else 1
        num += r["rating"] * w
        den += w
    return round(num / den, 2) if den else 0


async def seller_strikes(seller_id: str) -> int:
    """Reputation penalty input: reports filed against the seller or their listings/reviews."""
    lsts = await db.col("listings").find_many({"seller_id": seller_id}, limit=2000)
    lids = {l["_id"] for l in lsts}
    revs = await db.col("reviews").find_many({"seller_id": seller_id}, limit=2000)
    rids = {r["_id"] for r in revs}
    targets = {seller_id} | lids | rids
    all_reports = await db.col("reports").find_many({"type": {"$in": ["user", "listing", "review"]}}, limit=5000)
    return sum(1 for r in all_reports if r.get("target") in targets)
```

## File: `backend/app/core/ratelimit.py`

```python
"""Simple in-memory rate limiter for auth endpoints."""
import time
from fastapi import HTTPException

_BUCKETS: dict[str, list[float]] = {}


def rate_limit(key: str, max_hits: int = 20, window_s: int = 60):
    if len(_BUCKETS) > 5000:  # bound memory under key flood
        _BUCKETS.clear()
    now = time.time()
    hits = [t for t in _BUCKETS.get(key, []) if now - t < window_s]
    if len(hits) >= max_hits:
        raise HTTPException(429, "Too many requests, slow down")
    hits.append(now)
    _BUCKETS[key] = hits
```

## File: `backend/app/core/security.py`

```python
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def validate_password_rules(password: str) -> str | None:
    """Return error message if invalid, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password.encode()) > 72:
        return "Password must be at most 72 characters (bcrypt limit)"
    if not any(c.isdigit() for c in password):
        return "Password must contain a number"
    if not any(c.isalpha() for c in password):
        return "Password must contain a letter"
    return None


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _encode({"sub": user_id, "type": "access", "exp": exp, "jti": uuid.uuid4().hex})


def create_refresh_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _encode({"sub": user_id, "type": "refresh", "exp": exp, "jti": uuid.uuid4().hex})


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def new_id() -> str:
    return uuid.uuid4().hex[:24]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
```

## File: `backend/app/core/seed_data.py`

```python
"""Deterministic seed-data generator: 20 buyers + 40 sellers.

Each seller gets a social-style storefront: bio/avatar/skills/GitHub,
2-4 ongoing (active) projects and 1-3 sold projects with prices.
Pure data — no DB imports, so both seed.py (API mode) and tests can use it.
"""
import random

SEED_PASSWORD = "Seed1234"  # meets validation: 8+ chars, letter + number

FIRST = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Krishna", "Meera",
         "Nikhil", "Priya", "Rahul", "Riya", "Rohan", "Sanya", "Shreya", "Varun",
         "Aditya", "Neha", "Karan", "Pooja", "Vikram", "Simran", "Manav", "Tara",
         "Dev", "Aisha", "Kabir", "Navya", "Yash", "Zara", "Farhan", "Ira"]
LAST = ["Sharma", "Verma", "Patel", "Iyer", "Khan", "Gupta", "Mehta", "Nair",
        "Singh", "Reddy", "Joshi", "Das", "Kulkarni", "Chopra", "Bose", "Menon",
        "Agarwal", "Rao", "Malhotra", "Pillai", "Desai", "Kaur", "Ghosh", "Pandey"]

CATALOG = {
    "Web App": {
        "titles": ["SaaS Starter Kit", "E-commerce Storefront", "Blog CMS", "Admin Dashboard",
                   "Real-time Chat App", "Booking System", "Job Board", "Portfolio Template"],
        "tech": ["react", "nextjs", "nodejs", "tailwind", "typescript"],
        "base": 79,
    },
    "Mobile App": {
        "titles": ["Fitness Tracker", "Expense Manager", "Food Delivery UI", "Notes App", "Weather App"],
        "tech": ["flutter", "react-native", "firebase", "sqlite"],
        "base": 69,
    },
    "ML/AI Project": {
        "titles": ["Sentiment Analyzer", "Image Classifier", "RAG Chatbot", "Recommendation Engine", "Price Predictor"],
        "tech": ["python", "pytorch", "scikit-learn", "fastapi", "pandas"],
        "base": 129,
    },
    "Final Year Project": {
        "titles": ["Online Exam System", "Library Management", "Hospital Portal", "Attendance System", "Inventory Manager"],
        "tech": ["php", "mysql", "react", "nodejs", "mongodb"],
        "base": 99,
    },
    "Game": {
        "titles": ["2D Platformer", "Snake Game", "Puzzle Game", "Racing Game", "Tower Defense"],
        "tech": ["unity", "godot", "javascript", "c#", "pygame"],
        "base": 49,
    },
    "Script/Tool": {
        "titles": ["PDF Merger Tool", "Web Scraper", "Telegram Bot", "CSV Analyzer", "Backup Script"],
        "tech": ["python", "bash", "selenium", "nodejs"],
        "base": 29,
    },
    "Other": {
        "titles": ["API Boilerplate", "Auth Microservice", "Chrome Extension", "URL Shortener"],
        "tech": ["go", "docker", "redis", "postgres"],
        "base": 39,
    },
}

BIOS = [
    "CS undergrad selling side projects. Clean code, docs included.",
    "Full-stack dev. Every project ships with README + setup video.",
    "ML enthusiast. Final-year projects with report + PPT.",
    "Freelance web dev. Production-ready templates, quick support.",
    "Game dev hobbyist. Fun, documented, easy to reskin.",
    "Backend engineer. APIs with tests and Docker setup.",
]

COMMENTS = [
    "Exactly as described, setup took 10 minutes.",
    "Great docs, seller helped on chat. Recommended.",
    "Good value for money. Code is clean.",
    "Report + PPT saved my semester. Thanks!",
    "Minor bugs but seller fixed them fast.",
]


def _names(rng, n):
    picks = set()
    while len(picks) < n:
        picks.add(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
    return sorted(picks)


def build(seed: int = 42, n_buyers: int = 20, n_sellers: int = 40) -> dict:
    rng = random.Random(seed)
    buyer_names = _names(rng, n_buyers)
    seller_names = _names(rng, n_sellers)

    buyers = []
    for i, name in enumerate(buyer_names):
        slug = name.lower().replace(" ", ".")
        buyers.append({
            "email": f"{slug}.buyer{i}@example.com",
            "password": SEED_PASSWORD,
            "name": name,
            "role": "buyer",
        })

    sellers = []
    used_titles: set[str] = set()
    cats = list(CATALOG.keys())
    for i, name in enumerate(seller_names):
        slug = name.lower().replace(" ", "")
        handle = f"{slug}{rng.randint(1, 99)}"
        n_ongoing = rng.randint(2, 4)
        n_sold = rng.randint(1, 3)
        ongoing, sold = [], []
        for k in range(n_ongoing + n_sold):
            cat = cats[(i + k) % len(cats)]
            title_base = rng.choice(CATALOG[cat]["titles"])
            title = title_base
            suffix = 2
            while title in used_titles:
                title = f"{title_base} v{suffix}"
                suffix += 1
            used_titles.add(title)
            tech = rng.sample(CATALOG[cat]["tech"], k=min(3, len(CATALOG[cat]["tech"])))
            price = CATALOG[cat]["base"] + rng.choice([0, 10, 20, 30, 50, 70])
            lic = rng.choice(["personal", "personal", "resale", "exclusive"])
            seed_img = abs(hash(title)) % 10000
            item = {
                "title": title,
                "description": f"{title} — a complete {cat.lower()} project with source code, "
                               f"documentation and setup instructions. Built with {', '.join(tech)}.",
                "price": float(price),
                "category": cat,
                "tech_stack": tech,
                "images": [f"https://picsum.photos/seed/{seed_img}/640/360"],
                "demo_video": "",
                "license": lic,
                "accept_offers": rng.random() < 0.7,
                "status": "active",
            }
            (sold if k >= n_ongoing else ongoing).append(item)
        sellers.append({
            "email": f"{handle}@example.com",
            "password": SEED_PASSWORD,
            "name": name,
            "role": "seller",
            "bio": rng.choice(BIOS),
            "avatar": f"https://api.dicebear.com/9.x/thumbs/svg?seed={handle}",
            "skills": rng.sample(["react", "python", "nodejs", "flutter", "ml", "unity", "php", "go"], k=rng.randint(2, 4)),
            "github": handle,
            "portfolio": [f"https://github.com/{handle}"],
            "badges": ["developer"] if rng.random() < 0.5 else [],
            "ongoing": ongoing,
            "sold": sold,
        })
    return {"buyers": buyers, "sellers": sellers,
            "comments": COMMENTS, "password": SEED_PASSWORD}
```

## File: `backend/app/db/__init__.py`

```python

```

## File: `backend/app/db/database.py`

```python
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
```

## File: `backend/app/main.py`

```python
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import init_db
from app.routers import admin, auth, bidding, jobs, listings, messages, notifications, orders, reviews, uploads, users

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

if os.environ.get("SENTRY_DSN"):
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
        log.info("Sentry enabled")
    except Exception as e:
        log.warning(f"Sentry init failed: {e}")

# Redis cache hook (falls back to memory when REDIS_URL absent)
CACHE: dict = {}
if os.environ.get("REDIS_URL"):
    try:
        import redis
        _r = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        _r.ping()
        log.info("Redis enabled")
    except Exception as e:
        log.warning(f"Redis unavailable, using memory cache: {e}")

app = FastAPI(title="Project Bidding Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    if hasattr(exc, "status_code"):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def startup():
    await init_db()
    if settings.JWT_SECRET == "change-me-to-a-long-random-string":
        log.warning("JWT_SECRET is the default value — set a long random string in .env before any real use")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/")
async def root():
    return {"name": "Project Bidding API", "docs": "/docs", "health": "/health"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(bidding.router)
app.include_router(messages.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(jobs.router)
uploads.mount_static(app)
```

## File: `backend/app/models/__init__.py`

```python

```

## File: `backend/app/models/schemas.py`

```python
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

Role = Literal["buyer", "seller", "both", "admin"]
ListingStatus = Literal["draft", "active", "sold", "removed"]


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=80)
    role: Role = "both"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    bio: str = ""
    avatar: str = ""
    stripe_account_id: str = ""


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[Role] = None
    skills: Optional[list[str]] = None
    github: Optional[str] = None
    portfolio: Optional[list[str]] = None
    interests: Optional[list[str]] = None


class PriceTier(BaseModel):
    name: str
    price: float
    description: str = ""


class ListingIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10)
    price: float = Field(gt=0)
    category: str
    tech_stack: list[str] = []
    images: list[str] = []
    project_file: str = ""
    file_hash: str = ""
    status: ListingStatus = "active"
    demo_video: str = ""
    pricing_tiers: list[PriceTier] = []
    license: str = "personal"
    accept_offers: bool = True
    specs: dict = {}


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    images: Optional[list[str]] = None
    project_file: Optional[str] = None
    file_hash: Optional[str] = None
    status: Optional[ListingStatus] = None
    demo_video: Optional[str] = None
    pricing_tiers: Optional[list[PriceTier]] = None
    license: Optional[str] = None
    accept_offers: Optional[bool] = None
    featured: Optional[bool] = None
    specs: Optional[dict] = None


class OrderOut(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    amount: float
    fee: float
    status: str
    client_secret: str = ""
    download_token: str = ""
```

## File: `backend/app/routers/__init__.py`

```python

```

## File: `backend/app/routers/admin.py`

```python
"""Admin panel: users, listings, orders/disputes, analytics, moderation."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, require_admin
from app.core.security import utcnow
from app.db import database as db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def stats(_: dict = Depends(require_admin)):
    users_n = await db.users().count({})
    listings_n = await db.listings().count({})
    orders = await db.orders().find_many({}, limit=5000)
    gmv = round(sum(o["amount"] for o in orders if o.get("status") in ("paid", "delivered", "completed")), 2)
    by_status: dict[str, int] = {}
    for o in orders:
        by_status[o.get("status", "?")] = by_status.get(o.get("status", "?"), 0) + 1
    cats: dict[str, int] = {}
    lsts = await db.listings().find_many({}, limit=5000)
    for l in lsts:
        cats[l.get("category", "?")] = cats.get(l.get("category", "?"), 0) + 1
    return {"users": users_n, "listings": listings_n, "orders": len(orders),
            "gmv": gmv, "orders_by_status": by_status, "top_categories": cats}


@router.get("/users")
async def all_users(_: dict = Depends(require_admin)):
    from app.core.notify import seller_strikes
    items = await db.users().find_many({}, limit=500)
    out = []
    for u in items:
        strikes = await seller_strikes(u["_id"]) if u.get("role") in ("seller", "both") else 0
        out.append({"id": u["_id"], "email": u["email"], "name": u["name"], "role": u["role"],
                    "banned": u.get("banned", False), "strikes": strikes})
    return out


@router.post("/users/{uid}/ban")
async def ban(uid: str, body: dict, _: dict = Depends(require_admin)):
    await db.users().update_one({"_id": uid}, {"$set": {"banned": bool(body.get("banned", True))}})
    return {"ok": True}


@router.get("/listings")
async def all_listings(_: dict = Depends(require_admin)):
    return await db.listings().find_many({}, limit=500, sort=[("created_at", -1)])


@router.post("/listings/{lid}/remove")
async def remove_listing(lid: str, _: dict = Depends(require_admin)):
    await db.listings().update_one({"_id": lid}, {"$set": {"status": "removed"}})
    return {"ok": True}


@router.post("/listings/{lid}/feature")
async def feature_listing(lid: str, body: dict, _: dict = Depends(require_admin)):
    await db.listings().update_one({"_id": lid}, {"$set": {"featured": bool(body.get("featured", True))}})
    return {"ok": True}


@router.get("/orders")
async def all_orders(status: str = "", _: dict = Depends(require_admin)):
    flt = {"status": status} if status else {}
    return await db.orders().find_many(flt, limit=500, sort=[("created_at", -1)])


@router.post("/orders/{oid}/resolve")
async def resolve_dispute(oid: str, body: dict, _: dict = Depends(require_admin)):
    """action: refund | release"""
    o = await db.orders().find_one({"_id": oid})
    if not o:
        raise HTTPException(404, "Order not found")
    action = body.get("action")
    if action == "refund":
        await db.orders().update_one({"_id": oid}, {"$set": {"status": "refunded"}})
    elif action == "release":
        await db.orders().update_one({"_id": oid}, {"$set": {"status": "completed"}})
        await db.listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
    else:
        raise HTTPException(400, "action must be refund|release")
    return {"ok": True}


@router.get("/reports")
async def moderation_queue(_: dict = Depends(require_admin)):
    return await db.col("reports").find_many({}, limit=200, sort=[("created_at", -1)])


@router.post("/payouts/override")
async def payout_override(body: dict, user: dict = Depends(require_admin)):
    from app.core.security import new_id
    await db.col("payouts").insert_one({
        "_id": new_id(), "order_id": body.get("order_id", ""), "seller_id": body.get("seller_id", ""),
        "amount": float(body.get("amount", 0)), "note": body.get("note", "manual override"),
        "by": user["id"], "created_at": utcnow().isoformat(),
    })
    return {"ok": True}


@router.get("/analytics")
async def analytics(_: dict = Depends(require_admin)):
    revs = await db.reviews().find_many({}, limit=5000)
    avg = round(sum(r["rating"] for r in revs) / len(revs), 2) if revs else 0
    return {"total_reviews": len(revs), "avg_rating": avg}
```

## File: `backend/app/routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.deps import get_current_user
from app.core.ratelimit import rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    new_id,
    utcnow,
    validate_password_rules,
    verify_password,
)
from app.db import database as db
from app.db.database import BLACKLISTED_JTIS, users
from app.models.schemas import LoginIn, RefreshIn, SignupIn

router = APIRouter(prefix="/auth", tags=["auth"])


def _out(user: dict) -> dict:
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "bio": user.get("bio", ""),
        "avatar": user.get("avatar", ""),
        "stripe_account_id": user.get("stripe_account_id", ""),
        "email_verified": user.get("email_verified", False),
        "badges": user.get("badges", []),
        "skills": user.get("skills", []),
        "github": user.get("github", ""),
        "portfolio": user.get("portfolio", []),
        "interests": user.get("interests", []),
    }


@router.post("/signup")
async def signup(body: SignupIn, request: Request):
    rate_limit(f"signup:{request.client.host if request.client else 'x'}", 200, 300)
    err = validate_password_rules(body.password)
    if err:
        raise HTTPException(400, err)
    existing = await users().find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(400, "Email already registered")
    uid = new_id()
    user = {
        "_id": uid,
        "email": body.email.lower(),
        "password": hash_password(body.password),
        "name": body.name,
        "role": body.role,
        "bio": "",
        "avatar": "",
        "stripe_account_id": "",
        "email_verified": False,
        "badges": [],
        "skills": [],
        "github": "",
        "portfolio": [],
        "created_at": utcnow().isoformat(),
    }
    await users().insert_one(user)
    # email verification token (mock email in dev)
    token = new_id()
    await db.col("verifies").insert_one({"_id": token, "user_id": uid, "created_at": utcnow().isoformat()})
    from app.core.notify import notify_email
    await notify_email(user["email"], "Verify your email", f"Token: {token} (POST /auth/verify-email)")
    return {
        "user": _out(user),
        "access_token": create_access_token(uid),
        "refresh_token": create_refresh_token(uid),
        "verify_token_dev": token,
    }


@router.post("/login")
async def login(body: LoginIn, request: Request):
    rate_limit(f"login:{request.client.host if request.client else 'x'}", 200, 300)
    rate_limit(f"login-email:{body.email.lower()}", 15, 300)  # slow password-guessing per account
    user = await users().find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    if user.get("banned"):
        raise HTTPException(403, "Account suspended")
    uid = user["_id"]
    return {
        "user": _out(user),
        "access_token": create_access_token(uid),
        "refresh_token": create_refresh_token(uid),
    }


@router.post("/refresh")
async def refresh(body: RefreshIn):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(401, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    if payload.get("jti") in BLACKLISTED_JTIS:
        raise HTTPException(401, "Logged out")
    user = await users().find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(401, "User not found")
    return {
        "access_token": create_access_token(user["_id"]),
        "refresh_token": create_refresh_token(user["_id"]),
    }


@router.post("/logout")
async def logout(body: RefreshIn | None = None, user: dict = Depends(get_current_user)):
    # Blacklist the refresh token if provided; access token short-lived.
    if body and body.refresh_token:
        try:
            p = decode_token(body.refresh_token)
            if p.get("jti"):
                BLACKLISTED_JTIS.add(p["jti"])
        except Exception:
            pass
    return {"ok": True}


@router.post("/verify-email")
async def verify_email(body: dict):
    token = body.get("token", "")
    v = await db.col("verifies").find_one({"_id": token})
    if not v:
        raise HTTPException(400, "Invalid token")
    await users().update_one({"_id": v["user_id"]}, {"$set": {"email_verified": True}})
    await db.col("verifies").delete_one({"_id": token})
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(body: dict):
    u = await users().find_one({"email": (body.get("email") or "").lower()})
    token = new_id()
    if u:
        await db.col("resets").insert_one({"_id": token, "user_id": u["_id"], "created_at": utcnow().isoformat()})
        from app.core.notify import notify_email
        await notify_email(u["email"], "Reset password", f"Token: {token} (POST /auth/reset-password)")
    return {"ok": True, "reset_token_dev": token}


@router.post("/reset-password")
async def reset_password(body: dict):
    r = await db.col("resets").find_one({"_id": body.get("token", "")})
    if not r:
        raise HTTPException(400, "Invalid token")
    err = validate_password_rules(body.get("password", ""))
    if err:
        raise HTTPException(400, err)
    await users().update_one({"_id": r["user_id"]}, {"$set": {"password": hash_password(body["password"])}})
    await db.col("resets").delete_one({"_id": r["_id"]})
    return {"ok": True}


@router.get("/oauth/github")
async def oauth_github():
    from app.core.config import settings
    import os
    cid = os.environ.get("GITHUB_CLIENT_ID", "")
    if not cid:
        return {"mode": "mock", "note": "Set GITHUB_CLIENT_ID/SECRET for real OAuth; POST /auth/oauth/callback with email+name in mock mode"}
    return {"url": f"https://github.com/login/oauth/authorize?client_id={cid}"}


@router.post("/oauth/callback")
async def oauth_callback(body: dict):
    """Mock OAuth: pass email+name (dev). Real flow exchanges code via GitHub here."""
    email = (body.get("email") or "").lower()
    if not email:
        raise HTTPException(400, "email required in mock mode")
    u = await users().find_one({"email": email})
    if not u:
        uid = new_id()
        u = {"_id": uid, "email": email, "password": hash_password(new_id()), "name": body.get("name", email.split("@")[0]),
             "role": "both", "bio": "", "avatar": "", "stripe_account_id": "", "email_verified": True,
             "badges": ["developer"] if body.get("github") else [], "github": body.get("github", ""),
             "skills": [], "portfolio": [], "created_at": utcnow().isoformat()}
        await users().insert_one(u)
    return {"user": _out(u), "access_token": create_access_token(u["_id"]), "refresh_token": create_refresh_token(u["_id"])}


@router.post("/2fa/enable")
async def tfa_enable(user: dict = Depends(get_current_user)):
    secret = new_id()[:16]
    await users().update_one({"_id": user["id"]}, {"$set": {"tfa_secret": secret}})
    return {"otpauth_url": f"otpauth://totp/ProjectBidding:{user['id']}?secret={secret}&issuer=ProjectBidding",
            "note": "Confirm with POST /auth/2fa/verify {code}. Dev mock accepts any 6-digit code once."}


@router.post("/2fa/verify")
async def tfa_verify(body: dict, user: dict = Depends(get_current_user)):
    if len(str(body.get("code", ""))) != 6:
        raise HTTPException(400, "Invalid code")
    await users().update_one({"_id": user["id"]}, {"$set": {"tfa_enabled": True}})
    return {"ok": True}
```

## File: `backend/app/routers/bidding.py`

```python
"""Bidding system (Phase 2)."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.notify import notify, notify_email
from app.core.security import new_id, utcnow
from app.db import database as db

router = APIRouter(tags=["bids"])
BID_TTL_HOURS = 48


def _out(b: dict) -> dict:
    return {
        "id": b["_id"], "listing_id": b["listing_id"], "buyer_id": b["buyer_id"],
        "seller_id": b.get("seller_id", ""), "amount": b["amount"],
        "message": b.get("message", ""), "status": b.get("status", "pending"),
        "expires_at": b.get("expires_at"), "counter": b.get("counter"),
        "created_at": b.get("created_at"),
    }


@router.post("/listings/{listing_id}/bids")
async def place_bid(listing_id: str, body: dict, user: dict = Depends(get_current_user)):
    lst = await db.listings().find_one({"_id": listing_id})
    if not lst or lst.get("status") != "active":
        raise HTTPException(404, "Listing not available")
    if not lst.get("accept_offers", True):
        raise HTTPException(400, "Seller is not accepting offers on this listing")
    if lst["seller_id"] == user["id"]:
        raise HTTPException(400, "Cannot bid on your own listing")
    amount = float(body.get("amount", 0))
    if amount <= 0:
        raise HTTPException(400, "Invalid bid amount")
    bid = {
        "_id": new_id(), "listing_id": listing_id, "buyer_id": user["id"],
        "seller_id": lst["seller_id"], "amount": amount,
        "message": body.get("message", ""), "status": "pending",
        "expires_at": (utcnow() + timedelta(hours=BID_TTL_HOURS)).isoformat(),
        "created_at": utcnow().isoformat(),
    }
    await db.bids().insert_one(bid)
    await notify(lst["seller_id"], "bid", f"New bid ${amount} on {lst['title']}", f"/l/{listing_id}")
    return _out(bid)


@router.get("/listings/{listing_id}/bids")
async def list_bids(listing_id: str, user: dict = Depends(get_current_user)):
    lst = await db.listings().find_one({"_id": listing_id})
    if not lst:
        raise HTTPException(404, "Listing not found")
    if lst["seller_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only seller can view bids")
    items = await db.bids().find_many({"listing_id": listing_id}, limit=100, sort=[("amount", -1)])
    return [_out(b) for b in items]


@router.get("/bids/mine")
async def my_bids(user: dict = Depends(get_current_user)):
    items = await db.bids().find_many({"buyer_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [_out(b) for b in items]


@router.get("/bids/incoming")
async def incoming_bids(user: dict = Depends(get_current_user)):
    """Seller inbox: pending/countered bids across all my listings, newest first."""
    mine = await db.listings().find_many({"seller_id": user["id"]}, limit=500)
    titles = {m["_id"]: m["title"] for m in mine}
    items = await db.bids().find_many({"seller_id": user["id"]}, limit=200, sort=[("created_at", -1)])
    return [{**_out(b), "listing_title": titles.get(b["listing_id"], "")}
            for b in items if b.get("status") in ("pending", "countered")]


async def _get_bid(bid_id: str, user: dict, seller_only: bool = True) -> dict:
    b = await db.bids().find_one({"_id": bid_id})
    if not b:
        raise HTTPException(404, "Bid not found")
    if seller_only and b["seller_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only seller can do this")
    if b.get("status") != "pending":
        raise HTTPException(400, f"Bid already {b.get('status')}")
    if b.get("expires_at") and b["expires_at"] < utcnow().isoformat():
        await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "expired"}})
        raise HTTPException(400, "Bid expired")
    return b


@router.post("/bids/{bid_id}/reject")
async def reject_bid(bid_id: str, user: dict = Depends(get_current_user)):
    b = await _get_bid(bid_id, user)
    await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "rejected"}})
    await notify(b["buyer_id"], "bid", f"Your bid ${b['amount']} was rejected", f"/l/{b['listing_id']}")
    return {"ok": True}


@router.post("/bids/{bid_id}/counter")
async def counter_bid(bid_id: str, body: dict, user: dict = Depends(get_current_user)):
    b = await _get_bid(bid_id, user)
    amount = float(body.get("amount", 0))
    if amount <= 0:
        raise HTTPException(400, "Invalid amount")
    await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "countered", "counter": amount}})
    await notify(b["buyer_id"], "bid", f"Counter-offer ${amount} on your bid", f"/l/{b['listing_id']}")
    return {"ok": True, "counter": amount}


@router.post("/bids/{bid_id}/accept")
async def accept_bid(bid_id: str, user: dict = Depends(get_current_user)):
    from app.core.config import settings
    b = await _get_bid(bid_id, user)
    amount = float(b.get("counter") or b["amount"])
    fee = round(amount * settings.PLATFORM_FEE_PERCENT / 100, 2)
    oid = new_id()
    order = {
        "_id": oid, "listing_id": b["listing_id"], "buyer_id": b["buyer_id"],
        "seller_id": b["seller_id"], "amount": amount, "fee": fee,
        "status": "pending", "client_secret": f"mock_secret_bid_{oid[:8]}",
        "download_token": "", "bid_id": bid_id, "created_at": utcnow().isoformat(),
    }
    await db.orders().insert_one(order)
    await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "accepted"}})
    # reject other pending bids
    others = await db.bids().find_many({"listing_id": b["listing_id"]}, limit=200)
    for o in others:
        if o["_id"] != bid_id and o.get("status") == "pending":
            await db.bids().update_one({"_id": o["_id"]}, {"$set": {"status": "rejected"}})
    await notify(b["buyer_id"], "bid", f"Bid accepted at ${amount}! Complete payment.", "/dashboard")
    buyer = await db.users().find_one({"_id": b["buyer_id"]})
    if buyer:
        await notify_email(buyer["email"], "Bid accepted", f"Pay ${amount} for order {oid}")
    return {"ok": True, "order_id": oid, "amount": amount}


@router.get("/bids/analytics")
async def bid_analytics(user: dict = Depends(get_current_user)):
    mine = await db.listings().find_many({"seller_id": user["id"]}, limit=500)
    lids = {m["_id"] for m in mine}
    allb = await db.bids().find_many({}, limit=2000)
    rel = [b for b in allb if b["listing_id"] in lids]
    acc = [b["amount"] for b in rel if b.get("status") == "accepted"]
    return {
        "total_bids": len(rel),
        "accepted": len(acc),
        "avg_accepted": round(sum(acc) / len(acc), 2) if acc else 0,
    }
```

## File: `backend/app/routers/jobs.py`

```python
"""Scheduled/expiry jobs: bid expiry (48h), auto-complete (7d), auto-refund (7d no delivery)."""
from datetime import timedelta
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.notify import notify
from app.core.security import new_id, utcnow
from app.db import database as db

router = APIRouter(tags=["jobs"])


async def run_jobs() -> dict:
    now = utcnow().isoformat()
    expired = auto_completed = auto_refunded = 0
    bids = await db.bids().find_many({"status": "pending"}, limit=2000)
    for b in bids:
        if b.get("expires_at") and b["expires_at"] < now:
            await db.bids().update_one({"_id": b["_id"]}, {"$set": {"status": "expired"}})
            expired += 1
    orders = await db.orders().find_many({}, limit=5000)
    week_ago = (utcnow() - timedelta(days=7)).isoformat()
    for o in orders:
        if o.get("status") == "delivered" and o.get("created_at", "") < week_ago:
            payout = round(o["amount"] - o.get("fee", 0), 2)
            await db.orders().update_one({"_id": o["_id"]}, {"$set": {"status": "completed"}})
            await db.listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
            await db.col("payouts").insert_one({
                "_id": new_id(), "order_id": o["_id"], "seller_id": o["seller_id"],
                "amount": payout, "fee": o.get("fee", 0), "created_at": now, "auto": True})
            await notify(o["seller_id"], "order", f"Order {o['_id'][:8]} auto-completed — ${payout} payout", "/dashboard")
            auto_completed += 1
        elif o.get("status") == "paid" and o.get("created_at", "") < week_ago:
            await db.orders().update_one({"_id": o["_id"]}, {"$set": {"status": "refunded"}})
            auto_refunded += 1
    return {"expired_bids": expired, "auto_completed": auto_completed, "auto_refunded": auto_refunded}


@router.post("/jobs/run")
async def run(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        # allow cron without auth in dev via header? keep admin-only for safety
        from fastapi import HTTPException
        raise HTTPException(403, "Admin only")
    return await run_jobs()
```

## File: `backend/app/routers/listings.py`

```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import CATEGORIES
from app.core.deps import get_current_user, require_seller
from app.core.security import new_id, utcnow
from app.db import database as db
from app.db.database import listings, users
from app.models.schemas import ListingIn, ListingUpdate

router = APIRouter(prefix="/listings", tags=["listings"])

LICENSES = ["personal", "resale", "exclusive"]


def _out(d: dict, seller: dict | None = None) -> dict:
    return {
        "id": d["_id"],
        "title": d["title"],
        "description": d["description"],
        "price": d["price"],
        "category": d["category"],
        "tech_stack": d.get("tech_stack", []),
        "images": d.get("images", []),
        "status": d.get("status", "active"),
        "views": d.get("views", 0),
        "seller_id": d["seller_id"],
        "seller": seller,
        "demo_video": d.get("demo_video", ""),
        "pricing_tiers": d.get("pricing_tiers", []),
        "license": d.get("license", "personal"),
        "accept_offers": d.get("accept_offers", True),
        "featured": d.get("featured", False),
        "rating": d.get("rating", 0),
        "rating_count": d.get("rating_count", 0),
        "rating_weighted": d.get("rating_weighted", d.get("rating", 0)),
        "seller_rating": d.get("seller_rating", 0),
        "seller_rating_count": d.get("seller_rating_count", 0),
        "specs": d.get("specs", {}),
        "flagged_duplicate": d.get("flagged_duplicate", False),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
    }


async def _seller_info(seller_id: str):
    u = await users().find_one({"_id": seller_id})
    if not u:
        return None
    # email intentionally omitted: contact sellers via Ask-a-question chat
    return {"id": u["_id"], "name": u["name"], "bio": u.get("bio", "")}


@router.get("/categories")
async def categories():
    return {"categories": CATEGORIES}


@router.get("")
async def browse(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tech: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    open_to_bids: Optional[bool] = None,
    sort: str = "newest",
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
):
    flt: dict = {"status": "active"}
    if q:
        # full-text-ish: match title OR description (Atlas Search in prod).
        # re.escape so user input is treated literally (no regex injection).
        import re
        flt["$or"] = [{"title": {"$regex": re.escape(q), "$options": "i"}},
                      {"description": {"$regex": re.escape(q), "$options": "i"}}]
    if category:
        flt["category"] = category
    if tech:
        flt["tech_stack"] = {"$in": [tech]}
    price: dict = {}
    if min_price is not None:
        price["$gte"] = min_price
    if max_price is not None:
        price["$lte"] = max_price
    if price:
        flt["price"] = price
    if open_to_bids is not None:
        flt["accept_offers"] = open_to_bids
    if min_rating is not None:
        flt["seller_rating"] = {"$gte": min_rating}
    sort_map = {"newest": [("created_at", -1)], "price_asc": [("price", 1)], "price_desc": [("price", -1)],
                "popular": [("views", -1)], "rating": [("seller_rating", -1), ("rating", -1)]}
    items = await listings().find_many(flt, skip=(page - 1) * limit, limit=limit, sort=sort_map.get(sort, [("created_at", -1)]))
    total = await listings().count(flt)
    out = []
    for d in items:
        out.append(_out(d, await _seller_info(d["seller_id"])))
    return {"items": out, "total": total, "page": page, "limit": limit}


@router.get("/featured")
async def featured():
    items = await listings().find_many({"status": "active", "featured": True}, limit=10, sort=[("views", -1)])
    return [_out(d, await _seller_info(d["seller_id"])) for d in items]


@router.get("/trending")
async def trending():
    items = await listings().find_many({"status": "active"}, limit=10, sort=[("views", -1)])
    return [_out(d, await _seller_info(d["seller_id"])) for d in items]


@router.get("/tags")
async def all_tags():
    lsts = await listings().find_many({"status": "active"}, limit=2000)
    tags: dict[str, int] = {}
    for l in lsts:
        for t in l.get("tech_stack", []):
            tags[t] = tags.get(t, 0) + 1
    return {"tags": sorted(tags, key=tags.get, reverse=True)[:50]}


@router.get("/mine")
async def my_listings(user: dict = Depends(get_current_user)):
    items = await listings().find_many({"seller_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [_out(d) for d in items]


@router.post("")
async def create_listing(body: ListingIn, user: dict = Depends(require_seller)):
    if body.category not in CATEGORIES:
        raise HTTPException(400, f"Invalid category. Choose from {CATEGORIES}")
    if body.license not in LICENSES:
        raise HTTPException(400, f"Invalid license. Choose from {LICENSES}")
    if body.demo_video and not body.demo_video.startswith(("http://", "https://")):
        raise HTTPException(400, "Demo video must be an http(s) URL")
    flagged = False
    if body.file_hash:
        dup = await listings().find_one({"file_hash": body.file_hash})
        flagged = bool(dup)
    lid = new_id()
    now = utcnow().isoformat()
    doc = {
        "_id": lid,
        "title": body.title,
        "description": body.description,
        "price": body.price,
        "category": body.category,
        "tech_stack": body.tech_stack,
        "images": body.images,
        "project_file": body.project_file,
        "file_hash": body.file_hash,
        "flagged_duplicate": flagged,
        "status": body.status,
        "demo_video": body.demo_video,
        "pricing_tiers": [t.model_dump() for t in body.pricing_tiers],
        "license": body.license,
        "accept_offers": body.accept_offers,
        "specs": body.specs or {},
        "featured": False,
        "rating": 0,
        "rating_count": 0,
        "rating_weighted": 0,
        "seller_rating": 0,
        "seller_rating_count": 0,
        "views": 0,
        "seller_id": user["id"],
        "created_at": now,
        "updated_at": now,
    }
    await listings().insert_one(doc)
    return {**_out(doc, await _seller_info(user["id"])),
            "duplicate_warning": flagged or None}


@router.get("/{listing_id}/related")
async def related(listing_id: str):
    d = await listings().find_one({"_id": listing_id})
    if not d:
        raise HTTPException(404, "Listing not found")
    items = await listings().find_many({"status": "active", "category": d["category"]}, limit=20)
    items = [x for x in items if x["_id"] != listing_id]
    # rank by shared tech tags
    tags = set(d.get("tech_stack", []))
    items.sort(key=lambda x: len(tags & set(x.get("tech_stack", []))), reverse=True)
    return [_out(x, await _seller_info(x["seller_id"])) for x in items[:6]]


@router.post("/{listing_id}/report")
async def report_listing(listing_id: str, body: dict, user: dict = Depends(get_current_user)):
    from app.core.security import new_id as _nid
    await db.col("reports").insert_one({"_id": _nid(), "type": "listing", "by": user["id"],
                                        "target": listing_id, "reason": body.get("reason", "plagiarism"),
                                        "created_at": utcnow().isoformat()})
    return {"ok": True}


@router.get("/{listing_id}")
async def detail(listing_id: str):
    d = await listings().find_one({"_id": listing_id})
    if not d:
        raise HTTPException(404, "Listing not found")
    await listings().update_one({"_id": listing_id}, {"$inc": {"views": 1}})
    d["views"] = d.get("views", 0) + 1
    return _out(d, await _seller_info(d["seller_id"]))


@router.patch("/{listing_id}")
async def update_listing(listing_id: str, body: ListingUpdate, user: dict = Depends(get_current_user)):
    d = await listings().find_one({"_id": listing_id})
    if not d:
        raise HTTPException(404, "Listing not found")
    if d["seller_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Not your listing")
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if d.get("status") == "sold" and patch.get("status") == "active" and user.get("role") != "admin":
        raise HTTPException(400, "Sold listings can't be relisted (prevents double-sell)")
    if "category" in patch and patch["category"] not in CATEGORIES:
        raise HTTPException(400, "Invalid category")
    if "license" in patch and patch["license"] not in LICENSES:
        raise HTTPException(400, "Invalid license")
    if "demo_video" in patch and patch["demo_video"] and not patch["demo_video"].startswith(("http://", "https://")):
        raise HTTPException(400, "Demo video must be an http(s) URL")
    if "featured" in patch and user.get("role") != "admin":
        raise HTTPException(403, "Only admin can feature listings")
    if "pricing_tiers" in patch and patch["pricing_tiers"]:
        tiers = []
        for t in patch["pricing_tiers"]:
            tiers.append(t if isinstance(t, dict) else t.model_dump())
        patch["pricing_tiers"] = tiers
    if "file_hash" in patch and patch["file_hash"]:
        dup = await listings().find_one({"file_hash": patch["file_hash"]})
        if dup and dup["_id"] != listing_id:
            patch["flagged_duplicate"] = True
    if patch:
        patch["updated_at"] = utcnow().isoformat()
        await listings().update_one({"_id": listing_id}, {"$set": patch})
    fresh = await listings().find_one({"_id": listing_id})
    return _out(fresh, await _seller_info(fresh["seller_id"]))


@router.delete("/{listing_id}")
async def delete_listing(listing_id: str, user: dict = Depends(get_current_user)):
    d = await listings().find_one({"_id": listing_id})
    if not d:
        raise HTTPException(404, "Listing not found")
    if d["seller_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Not your listing")
    # Don't strand buyers: block removal while money/goods are in flight
    live = await db.orders().find_many(
        {"listing_id": listing_id, "status": {"$in": ["pending", "paid", "delivered", "disputed"]}}, limit=5)
    if live and user.get("role") != "admin":
        raise HTTPException(400, f"Can't delete: {len(live)} live order(s) on this project (fulfil or refund first)")
    await listings().update_one({"_id": listing_id}, {"$set": {"status": "removed", "updated_at": utcnow().isoformat()}})
    return {"ok": True}
```

## File: `backend/app/routers/messages.py`

```python
"""Messaging: threads tied to listing/order, polling + WebSocket realtime."""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.core.deps import get_current_user
from app.core.notify import notify
from app.core.security import new_id, utcnow
from app.db import database as db

router = APIRouter(tags=["messages"])
_sockets: dict[str, list[WebSocket]] = {}


def _tout(t: dict) -> dict:
    return {"id": t["_id"], "listing_id": t.get("listing_id", ""), "order_id": t.get("order_id", ""),
            "buyer_id": t["buyer_id"], "seller_id": t["seller_id"],
            "unread_buyer": t.get("unread_buyer", 0), "unread_seller": t.get("unread_seller", 0),
            "created_at": t.get("created_at")}


@router.post("/threads")
async def open_thread(body: dict, user: dict = Depends(get_current_user)):
    listing_id = body.get("listing_id", "")
    order_id = body.get("order_id", "")
    seller_id, buyer_id = "", ""
    if order_id:
        o = await db.orders().find_one({"_id": order_id})
        if not o:
            raise HTTPException(404, "Order not found")
        if user["id"] not in (o["buyer_id"], o["seller_id"]):
            raise HTTPException(403, "No access")
        seller_id, buyer_id = o["seller_id"], o["buyer_id"]
    elif listing_id:
        lst = await db.listings().find_one({"_id": listing_id})
        if not lst:
            raise HTTPException(404, "Listing not found")
        seller_id = lst["seller_id"]
        buyer_id = user["id"] if user["id"] != seller_id else body.get("buyer_id", user["id"])
    else:
        raise HTTPException(400, "listing_id or order_id required")
    # blocked check
    blocked = await db.col("reports").find_one({"type": "block", "by": seller_id, "target": buyer_id})
    blocked2 = await db.col("reports").find_one({"type": "block", "by": buyer_id, "target": seller_id})
    if blocked or blocked2:
        raise HTTPException(403, "Messaging blocked between these users")
    existing = await db.threads().find_one({"listing_id": listing_id, "order_id": order_id, "buyer_id": buyer_id, "seller_id": seller_id})
    if existing:
        return _tout(existing)
    t = {"_id": new_id(), "listing_id": listing_id, "order_id": order_id,
         "buyer_id": buyer_id, "seller_id": seller_id,
         "unread_buyer": 0, "unread_seller": 0, "created_at": utcnow().isoformat()}
    await db.threads().insert_one(t)
    return _tout(t)


@router.get("/threads")
async def my_threads(user: dict = Depends(get_current_user)):
    items = await db.threads().find_many({"$or": [{"buyer_id": user["id"]}, {"seller_id": user["id"]}]}, limit=100)
    unread = sum(t.get("unread_buyer", 0) if t["buyer_id"] == user["id"] else t.get("unread_seller", 0) for t in items)
    return {"threads": [_tout(t) for t in items], "unread_total": unread}


@router.get("/threads/{tid}/messages")
async def thread_messages(tid: str, user: dict = Depends(get_current_user)):
    t = await db.threads().find_one({"_id": tid})
    if not t or user["id"] not in (t["buyer_id"], t["seller_id"]):
        raise HTTPException(404, "Thread not found")
    msgs = await db.messages().find_many({"thread_id": tid}, limit=200, sort=[("created_at", 1)])
    field = "unread_buyer" if t["buyer_id"] == user["id"] else "unread_seller"
    await db.threads().update_one({"_id": tid}, {"$set": {field: 0}})
    return [{"id": m["_id"], "from": m["from_id"], "text": m["text"],
             "attachment": m.get("attachment", ""), "created_at": m.get("created_at")} for m in msgs]


@router.post("/threads/{tid}/messages")
async def send_message(tid: str, body: dict, user: dict = Depends(get_current_user)):
    t = await db.threads().find_one({"_id": tid})
    if not t or user["id"] not in (t["buyer_id"], t["seller_id"]):
        raise HTTPException(404, "Thread not found")
    text = (body.get("text") or "").strip()
    if not text and not body.get("attachment"):
        raise HTTPException(400, "Empty message")
    m = {"_id": new_id(), "thread_id": tid, "from_id": user["id"], "text": text,
         "attachment": body.get("attachment", ""), "created_at": utcnow().isoformat()}
    await db.messages().insert_one(m)
    other = t["seller_id"] if user["id"] == t["buyer_id"] else t["buyer_id"]
    field = "unread_seller" if user["id"] == t["buyer_id"] else "unread_buyer"
    cur = await db.threads().find_one({"_id": tid})
    await db.threads().update_one({"_id": tid}, {"$set": {field: cur.get(field, 0) + 1}})
    await notify(other, "message", f"New message from {user.get('name')}", "/messages")
    for ws in _sockets.get(tid, []):
        try:
            await ws.send_json({"from": user["id"], "text": text})
        except Exception:
            pass
    return {"id": m["_id"]}


@router.websocket("/ws/threads/{tid}")
async def thread_ws(ws: WebSocket, tid: str):
    await ws.accept()
    _sockets.setdefault(tid, []).append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _sockets[tid].remove(ws)


@router.post("/users/{uid}/block")
async def block_user(uid: str, user: dict = Depends(get_current_user)):
    await db.col("reports").insert_one({"_id": new_id(), "type": "block", "by": user["id"], "target": uid, "created_at": utcnow().isoformat()})
    return {"ok": True}


@router.post("/users/{uid}/report")
async def report_user(uid: str, body: dict, user: dict = Depends(get_current_user)):
    await db.col("reports").insert_one({"_id": new_id(), "type": "user", "by": user["id"], "target": uid,
                                        "reason": body.get("reason", ""), "created_at": utcnow().isoformat()})
    return {"ok": True}
```

## File: `backend/app/routers/notifications.py`

```python
"""Notifications: in-app list, read state, preferences."""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.security import utcnow
from app.db import database as db

router = APIRouter(tags=["notifications"])

KINDS = ["bid", "order", "message", "review", "system"]


@router.get("/notifications")
async def list_notifs(user: dict = Depends(get_current_user)):
    items = await db.col("notifications").find_many({"user_id": user["id"]}, limit=50, sort=[("created_at", -1)])
    unread = sum(1 for n in items if not n.get("read"))
    return {"items": [{"id": n["_id"], "kind": n["kind"], "title": n["title"],
                       "link": n.get("link", ""), "read": n.get("read", False),
                       "created_at": n.get("created_at")} for n in items],
            "unread": unread}


@router.post("/notifications/{nid}/read")
async def mark_read(nid: str, user: dict = Depends(get_current_user)):
    await db.col("notifications").update_one({"_id": nid}, {"$set": {"read": True}})
    return {"ok": True}


@router.post("/notifications/read-all")
async def mark_all(user: dict = Depends(get_current_user)):
    items = await db.col("notifications").find_many({"user_id": user["id"]}, limit=500)
    for n in items:
        await db.col("notifications").update_one({"_id": n["_id"]}, {"$set": {"read": True}})
    return {"ok": True}


@router.get("/notifications/prefs")
async def get_prefs(user: dict = Depends(get_current_user)):
    p = await db.col("prefs").find_one({"_id": f"prefs:{user['id']}"})
    return {"opt_out": (p or {}).get("opt_out", {}), "kinds": KINDS}


@router.post("/notifications/prefs")
async def set_prefs(body: dict, user: dict = Depends(get_current_user)):
    opt_out = body.get("opt_out", {})
    key = f"prefs:{user['id']}"
    existing = await db.col("prefs").find_one({"_id": key})
    if existing:
        await db.col("prefs").update_one({"_id": key}, {"$set": {"opt_out": opt_out, "updated_at": utcnow().isoformat()}})
    else:
        await db.col("prefs").insert_one({"_id": key, "user_id": user["id"], "opt_out": opt_out})
    return {"ok": True}


@router.post("/notifications/push-token")
async def push_token(body: dict, user: dict = Depends(get_current_user)):
    """Mobile push stub: store the FCM/APNs device token; delivery wired when apps ship."""
    await db.col("prefs").insert_one({"_id": f"push:{user['id']}:{body.get('token', '')[:32]}",
                                      "user_id": user["id"], "token": body.get("token", ""),
                                      "created_at": utcnow().isoformat()})
    return {"ok": True, "note": "Stored. Push delivery activates with the mobile app (FCM/APNs)."}
```

## File: `backend/app/routers/orders.py`

```python
"""Orders + payments MVP.

Real Stripe when STRIPE_SECRET_KEY is set, otherwise MOCK mode:
- POST /orders creates order + fake client_secret
- POST /orders/{id}/mock-pay simulates the webhook (marks paid)
Production: configure Stripe webhook -> POST /webhooks/stripe.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.notify import notify, notify_email
from app.core.security import new_id, utcnow
from app.db import database as db
from app.db.database import listings, orders

router = APIRouter(tags=["orders"])
STRIPE_MODE = bool(settings.STRIPE_SECRET_KEY)


def _out(o: dict) -> dict:
    return {
        "id": o["_id"],
        "listing_id": o["listing_id"],
        "buyer_id": o["buyer_id"],
        "seller_id": o["seller_id"],
        "amount": o["amount"],
        "fee": o.get("fee", 0),
        "status": o["status"],
        "client_secret": o.get("client_secret", ""),
        "download_token": o.get("download_token", ""),
        "created_at": o.get("created_at"),
    }


def _fee(amount: float) -> float:
    return round(amount * settings.PLATFORM_FEE_PERCENT / 100, 2)


@router.post("/orders")
async def buy_now(body: dict, user: dict = Depends(get_current_user)):
    listing_id = body.get("listing_id")
    lst = await listings().find_one({"_id": listing_id})
    if not lst or lst.get("status") != "active":
        raise HTTPException(404, "Listing not available")
    if lst["seller_id"] == user["id"]:
        raise HTTPException(400, "Cannot buy your own listing")
    oid = new_id()
    amount = float(lst["price"])
    client_secret = ""
    if STRIPE_MODE:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency="usd",
            metadata={"order_id": oid, "listing_id": listing_id},
        )
        client_secret = intent.client_secret
    else:
        client_secret = f"mock_secret_{uuid.uuid4().hex[:12]}"
    order = {
        "_id": oid,
        "listing_id": listing_id,
        "buyer_id": user["id"],
        "seller_id": lst["seller_id"],
        "amount": amount,
        "fee": _fee(amount),
        "status": "pending",
        "client_secret": client_secret,
        "download_token": "",
        "created_at": utcnow().isoformat(),
    }
    await orders().insert_one(order)
    await notify(order["seller_id"], "order", f"New order for {lst['title']} (${amount})", "/dashboard")
    buyer = await db.users().find_one({"_id": user["id"]})
    if buyer:
        await notify_email(buyer["email"], "Order placed", f"Order {oid} for {lst['title']} — complete payment.")
    return {**_out(order), "stripe_mode": "live" if STRIPE_MODE else "mock"}


@router.post("/orders/{order_id}/mock-pay")
async def mock_pay(order_id: str, user: dict = Depends(get_current_user)):
    """Dev-only: simulate successful payment when Stripe keys absent."""
    if STRIPE_MODE:
        raise HTTPException(400, "Stripe live mode — pay via Stripe, not mock")
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["buyer_id"] != user["id"]:
        raise HTTPException(403, "Not your order")
    await orders().update_one({"_id": order_id}, {"$set": {"status": "paid"}})
    o["status"] = "paid"
    await notify(o["seller_id"], "order", f"Order {order_id[:8]} paid — deliver files", "/dashboard")
    seller = await db.users().find_one({"_id": o["seller_id"]})
    if seller:
        await notify_email(seller["email"], "Payment received", f"Order {order_id} paid. Deliver files.")
    return _out(o)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    if STRIPE_MODE:
        import stripe
        sig = request.headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            raise HTTPException(400, f"Webhook error: {e}")
        if event["type"] == "payment_intent.succeeded":
            oid = event["data"]["object"]["metadata"].get("order_id")
            if oid:
                await orders().update_one({"_id": oid}, {"$set": {"status": "paid"}})
        return {"received": True}
    return {"ok": True, "mode": "mock"}


@router.get("/orders/purchases")
async def my_purchases(user: dict = Depends(get_current_user)):
    items = await orders().find_many({"buyer_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [await _enrich(o) for o in items]


@router.get("/orders/sales")
async def my_sales(user: dict = Depends(get_current_user)):
    items = await orders().find_many({"seller_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [await _enrich(o) for o in items]


async def _enrich(o: dict) -> dict:
    """Attach listing title/image so dashboards read like an order history, not IDs."""
    base = _out(o)
    try:
        lst = await listings().find_one({"_id": o["listing_id"]})
        if lst:
            base["listing_title"] = lst["title"]
            base["listing_image"] = (lst.get("images") or [""])[0]
    except Exception:
        pass
    return base


@router.post("/orders/{order_id}/deliver")
async def deliver(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["seller_id"] != user["id"]:
        raise HTTPException(403, "Only seller can deliver")
    if o["status"] != "paid":
        raise HTTPException(400, "Order must be paid before delivery")
    token = uuid.uuid4().hex
    await orders().update_one({"_id": order_id}, {"$set": {"status": "delivered", "download_token": token}})
    o["status"] = "delivered"
    o["download_token"] = token
    await notify(o["buyer_id"], "order", "Your files are ready to download", "/dashboard")
    return _out(o)


@router.get("/orders/{order_id}/download")
async def download(order_id: str, token: str = "", user: dict = Depends(get_current_user)):
    import os
    from fastapi.responses import FileResponse
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if user["id"] not in (o["buyer_id"], o["seller_id"]) and user.get("role") != "admin":
        raise HTTPException(403, "No access")
    if o["status"] not in ("delivered", "completed"):
        raise HTTPException(400, "Files available only after seller delivers")
    if user["id"] == o["buyer_id"] and o.get("download_token") != token:
        raise HTTPException(403, "Invalid download token")
    lst = await listings().find_one({"_id": o["listing_id"]})
    if not lst or not lst.get("project_file"):
        raise HTTPException(404, "No project file attached to this listing")
    key = lst["project_file"]
    name = ""
    if key.startswith("locked:files/"):
        name = os.path.basename(key.split("locked:files/", 1)[1])
    elif key.startswith("/uploads/files/"):
        name = os.path.basename(key)  # legacy key shape, same locked dir
    if name:
        from app.routers.uploads import FILES
        path = os.path.join(FILES, name)
        if os.path.isfile(path):
            return FileResponse(path, filename=f"{lst['title'][:40]}.zip")
        raise HTTPException(404, "Project file no longer on server")
    return {"file_url": key, "listing": lst["title"]}  # external/S3 URL case


@router.post("/orders/{order_id}/confirm")
async def confirm_receipt(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["buyer_id"] != user["id"]:
        raise HTTPException(403, "Only buyer can confirm")
    if o["status"] != "delivered":
        raise HTTPException(400, "Order must be delivered first")
    payout = round(o["amount"] - o.get("fee", 0), 2)
    # Real payout: Stripe transfer to seller's Connect account happens here.
    if STRIPE_MODE:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            seller = await db.users().find_one({"_id": o["seller_id"]})
            if seller and seller.get("stripe_account_id"):
                stripe.Transfer.create(amount=int(payout * 100), currency="usd",
                                       destination=seller["stripe_account_id"],
                                       metadata={"order_id": order_id})
        except Exception:
            pass
    await db.col("payouts").insert_one({
        "_id": new_id(), "order_id": order_id, "seller_id": o["seller_id"],
        "amount": payout, "fee": o.get("fee", 0), "created_at": utcnow().isoformat()})
    await listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
    await orders().update_one({"_id": order_id}, {"$set": {"status": "completed"}})
    o["status"] = "completed"
    await notify(o["seller_id"], "order", f"Order {order_id[:8]} completed — ${payout} payout", "/dashboard")
    return {**_out(o), "payout_to_seller": payout}


@router.post("/orders/{order_id}/refund")
async def refund(order_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if STRIPE_MODE:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Refund.create(payment_intent=o.get("client_secret", "").split("_secret")[0])
        except Exception:
            pass
    await orders().update_one({"_id": order_id}, {"$set": {"status": "refunded"}})
    return {"ok": True}


@router.get("/payments/payouts")
async def payout_history(user: dict = Depends(get_current_user)):
    items = await db.col("payouts").find_many({"seller_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    total = round(sum(p["amount"] for p in items), 2)
    return {"items": items, "total": total}


@router.get("/payments/tax-doc")
async def tax_doc(user: dict = Depends(get_current_user)):
    items = await db.col("payouts").find_many({"seller_id": user["id"]}, limit=5000)
    total = round(sum(p["amount"] for p in items), 2)
    return {"seller": user["id"], "year": 2026, "total_payouts": total,
            "note": "Stub — generate 1099 equivalent at real scale"}


@router.post("/orders/{order_id}/dispute")
async def dispute(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if user["id"] not in (o["buyer_id"], o["seller_id"]):
        raise HTTPException(403, "No access")
    await orders().update_one({"_id": order_id}, {"$set": {"status": "disputed"}})
    o["status"] = "disputed"
    return _out(o)


@router.get("/payments/connect-status")
async def connect_status(user: dict = Depends(get_current_user)):
    if STRIPE_MODE:
        return {"connected": bool(user.get("stripe_account_id")), "mode": "live"}
    return {"connected": True, "mode": "mock", "note": "Set STRIPE_SECRET_KEY for real Connect onboarding"}


@router.post("/payments/connect-onboard")
async def connect_onboard(user: dict = Depends(get_current_user)):
    from app.db.database import users
    if STRIPE_MODE:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        acct = stripe.Account.create(type="express")
        await users().update_one({"_id": user["id"]}, {"$set": {"stripe_account_id": acct.id}})
        link = stripe.AccountLink.create(account=acct.id, refresh_url=settings.FRONTEND_URL, return_url=settings.FRONTEND_URL, type="account_onboarding")
        return {"url": link.url, "mode": "live"}
    fake = f"acct_mock_{user['id'][:8]}"
    await users().update_one({"_id": user["id"]}, {"$set": {"stripe_account_id": fake}})
    return {"url": "", "mode": "mock", "account_id": fake}
```

## File: `backend/app/routers/reviews.py`

```python
"""Reviews & trust."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.notify import notify, update_listing_rating
from app.core.security import new_id, utcnow
from app.db import database as db

router = APIRouter(tags=["reviews"])


@router.post("/orders/{order_id}/reviews")
async def leave_review(order_id: str, body: dict, user: dict = Depends(get_current_user)):
    o = await db.orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["buyer_id"] != user["id"]:
        raise HTTPException(403, "Only buyer can review")
    if o.get("status") != "completed":
        raise HTTPException(400, "Can review only after order is completed")
    rating = int(body.get("rating", 0))
    if rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be 1-5")
    existing = await db.reviews().find_one({"order_id": order_id})
    if existing:
        raise HTTPException(400, "Already reviewed")
    r = {"_id": new_id(), "order_id": order_id, "listing_id": o["listing_id"],
         "buyer_id": user["id"], "seller_id": o["seller_id"], "rating": rating,
         "comment": body.get("comment", ""), "response": "",
         "created_at": utcnow().isoformat()}
    await db.reviews().insert_one(r)
    await update_listing_rating(o["listing_id"])
    await notify(o["seller_id"], "review", f"New {rating}-star review", f"/l/{o['listing_id']}")
    return {"id": r["_id"]}


@router.get("/listings/{listing_id}/reviews")
async def listing_reviews(listing_id: str):
    items = await db.reviews().find_many({"listing_id": listing_id}, limit=100, sort=[("created_at", -1)])
    return [{"id": r["_id"], "rating": r["rating"], "comment": r.get("comment", ""),
             "response": r.get("response", ""), "created_at": r.get("created_at")} for r in items]


@router.post("/reviews/{rid}/respond")
async def respond_review(rid: str, body: dict, user: dict = Depends(get_current_user)):
    r = await db.reviews().find_one({"_id": rid})
    if not r:
        raise HTTPException(404, "Review not found")
    if r["seller_id"] != user["id"]:
        raise HTTPException(403, "Only seller can respond")
    await db.reviews().update_one({"_id": rid}, {"$set": {"response": body.get("response", "")}})
    return {"ok": True}


@router.post("/reviews/{rid}/report")
async def report_review(rid: str, body: dict, user: dict = Depends(get_current_user)):
    await db.col("reports").insert_one({"_id": new_id(), "type": "review", "by": user["id"],
                                        "target": rid, "reason": body.get("reason", ""),
                                        "created_at": utcnow().isoformat()})
    return {"ok": True}
```

## File: `backend/app/routers/uploads.py`

```python
"""Uploads MVP: local disk storage; S3 presigned-URL path when USE_S3=true."""
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.deps import get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
PREVIEWS = os.path.join(BASE, "previews")
FILES = os.path.join(BASE, "files")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(FILES, exist_ok=True)


def mount_static(app):
    # Only previews are public. Project zips stay locked: served solely via
    # the token-gated /orders/{id}/download endpoint (FileResponse).
    app.mount("/uploads/previews", StaticFiles(directory=PREVIEWS), name="previews")


MAX_PREVIEW_BYTES = 5 * 1024 * 1024
MAX_ZIP_BYTES = 50 * 1024 * 1024


def _image_kind(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


@router.post("/preview")
async def upload_preview(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    data = await file.read()
    if len(data) > MAX_PREVIEW_BYTES:
        raise HTTPException(400, "Preview too large (max 5MB)")
    kind = _image_kind(data)
    if not kind:
        raise HTTPException(400, "Only real image files allowed for previews")
    ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp" }[kind]
    name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(PREVIEWS, name)
    with open(dest, "wb") as f:
        f.write(data)
    if settings.USE_S3 and settings.S3_BUCKET:
        import boto3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION,
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3.upload_file(dest, settings.S3_BUCKET, f"previews/{name}", ExtraArgs={"ContentType": file.content_type})
        url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/previews/{name}"
        return {"url": url}
    return {"url": f"/uploads/previews/{name}"}


@router.post("/project-file")
async def upload_project_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    import hashlib
    from app.db import database as db
    if user.get("role") not in ("seller", "both", "admin"):
        raise HTTPException(403, "Only sellers can upload project files")
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(400, "Project file must be a .zip")
    data = await file.read()
    if len(data) > MAX_ZIP_BYTES:
        raise HTTPException(400, "Project file too large (max 50MB)")
    if not data.startswith(b"PK"):
        raise HTTPException(400, "Project file must be a real .zip archive")
    digest = hashlib.sha256(data).hexdigest()
    name = f"{uuid.uuid4().hex}.zip"
    dest = os.path.join(FILES, name)
    with open(dest, "wb") as f:
        f.write(data)
    dup = await db.listings().find_one({"file_hash": digest})
    # Locked: served only via signed /orders/{id}/download, never listed publicly.
    return {"key": f"locked:files/{name}",
            "file_hash": digest,
            "duplicate_warning": bool(dup),
            "note": "Locked until purchase completes"}


@router.post("/similarity-check")
async def similarity_check(body: dict, user: dict = Depends(get_current_user)):
    """Code similarity stub (wire MOSS / plagiarism API in prod)."""
    return {"score": 0.0, "flagged": False,
            "note": "Stub — integrate MOSS or similar API for real code similarity"}


@router.get("/s3-presigned")
async def s3_presigned(filename: str, user: dict = Depends(get_current_user)):
    if not (settings.USE_S3 and settings.S3_BUCKET):
        return {"mode": "local", "note": "Set USE_S3=true + bucket for real presigned URLs"}
    import boto3
    s3 = boto3.client("s3", region_name=settings.AWS_REGION,
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    url = s3.generate_presigned_url("put_object", Params={"Bucket": settings.S3_BUCKET, "Key": f"uploads/{filename}"}, ExpiresIn=3600)
    return {"url": url}
```

## File: `backend/app/routers/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.security import new_id, utcnow
from app.db import database as db
from app.db.database import listings, users
from app.models.schemas import ProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _out(u: dict) -> dict:
    return {
        "id": u.get("_id", u.get("id")),
        "email": u["email"],
        "name": u["name"],
        "role": u["role"],
        "bio": u.get("bio", ""),
        "avatar": u.get("avatar", ""),
        "stripe_account_id": u.get("stripe_account_id", ""),
        "email_verified": u.get("email_verified", False),
        "badges": u.get("badges", []),
        "skills": u.get("skills", []),
        "github": u.get("github", ""),
        "portfolio": u.get("portfolio", []),
        "interests": u.get("interests", []),
    }


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _out({**user, "_id": user["id"]})


@router.patch("/me")
async def update_me(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if patch:
        await users().update_one({"_id": user["id"]}, {"$set": patch})
    fresh = await users().find_one({"_id": user["id"]})
    return _out(fresh)


@router.get("/sellers/top")
async def top_sellers(limit: int = 40):
    """Seller directory: every seller with social stats (followers, rating, ongoing/sold)."""
    sellers = await users().find_many({"role": {"$in": ["seller", "both", "admin"]}}, limit=500)
    out = []
    for u in sellers:
        if u.get("banned"):
            continue
        sid = u["_id"]
        revs = await db.reviews().find_many({"seller_id": sid}, limit=500)
        avg = round(sum(r["rating"] for r in revs) / len(revs), 2) if revs else 0
        followers = await db.col("follows").count({"target": sid})
        ongoing = await listings().count({"seller_id": sid, "status": {"$in": ["active", "draft"]}})
        sold = await listings().count({"seller_id": sid, "status": "sold"})
        pub = _out(u)
        pub.pop("email", None)  # no email harvesting from the directory
        out.append({**pub, "rating": avg, "rating_count": len(revs),
                    "followers": followers, "ongoing_count": ongoing, "sold_count": sold})
    out.sort(key=lambda s: (s["sold_count"], s["followers"], s["rating"]), reverse=True)
    return out[:limit]


@router.get("/{user_id}")
async def public_profile(user_id: str):
    u = await users().find_one({"_id": user_id})
    if not u:
        raise HTTPException(404, "User not found")
    ongoing = await listings().find_many(
        {"seller_id": user_id, "status": {"$in": ["active", "draft"]}}, limit=50, sort=[("created_at", -1)])
    sold_lsts = await listings().find_many(
        {"seller_id": user_id, "status": "sold"}, limit=50, sort=[("created_at", -1)])
    revs = await db.reviews().find_many({"seller_id": user_id}, limit=500)
    avg = round(sum(r["rating"] for r in revs) / len(revs), 2) if revs else 0
    from app.core.notify import seller_strikes, weighted_rating
    strikes = await seller_strikes(user_id)
    followers = await db.col("follows").count({"target": user_id})
    completed = await db.orders().find_many({"seller_id": user_id, "status": "completed"}, limit=5000)
    earned = round(sum(o["amount"] - o.get("fee", 0) for o in completed), 2)
    pub = _out(u)
    pub.pop("email", None)  # contact via chat, not scrapeable email
    return {
        **pub,
        "active_listings": len(ongoing),
        "ongoing_count": len(ongoing),
        "sold_count": len(sold_lsts),
        "total_earned": earned,
        "rating": avg, "rating_count": len(revs),
        "rating_weighted": weighted_rating(revs),
        "strikes": strikes,
        "flagged_seller": strikes >= 3,
        "followers": followers,
        # legacy field (active listings, id/title/price)
        "listings": [{"id": l["_id"], "title": l["title"], "price": l["price"]} for l in ongoing],
        "ongoing_projects": [
            {"id": l["_id"], "title": l["title"], "price": l["price"], "category": l.get("category", ""),
             "images": l.get("images", []), "views": l.get("views", 0), "rating": l.get("rating", 0),
             "status": l.get("status", "active")} for l in ongoing
        ],
        "sold_projects": [
            {"id": l["_id"], "title": l["title"], "price": l["price"], "category": l.get("category", ""),
             "images": l.get("images", []), "sold_at": l.get("updated_at", l.get("created_at"))} for l in sold_lsts
        ],
    }


@router.post("/{user_id}/follow")
async def follow(user_id: str, body: dict | None = None, user: dict = Depends(get_current_user)):
    if user_id == user["id"]:
        raise HTTPException(400, "Cannot follow yourself")
    ex = await db.col("follows").find_one({"by": user["id"], "target": user_id})
    want: bool | None = (body or {}).get("following")
    if want is True and ex:
        return {"following": True}
    if want is False and not ex:
        return {"following": False}
    if want is None:
        want = not ex  # legacy toggle
    if want and not ex:
        await db.col("follows").insert_one({"_id": new_id(), "by": user["id"], "target": user_id, "created_at": utcnow().isoformat()})
        return {"following": True}
    if not want and ex:
        await db.col("follows").delete_one({"_id": ex["_id"]})
    return {"following": bool(want)}


@router.post("/me/request-student-badge")
async def student_badge(body: dict, user: dict = Depends(get_current_user)):
    email = (body.get("edu_email") or user.get("email", ""))
    if not email.endswith(".edu") and ".ac." not in email:
        raise HTTPException(400, "Requires a student (.edu/.ac) email — mock check")
    u = await users().find_one({"_id": user["id"]})
    badges = list(set((u.get("badges") or []) + ["student"]))
    await users().update_one({"_id": user["id"]}, {"$set": {"badges": badges}})
    return {"ok": True, "badges": badges}


@router.post("/me/link-github")
async def link_github(body: dict, user: dict = Depends(get_current_user)):
    gh = body.get("github", "")
    if not gh:
        raise HTTPException(400, "github username required")
    u = await users().find_one({"_id": user["id"]})
    badges = list(set((u.get("badges") or []) + ["developer"]))
    await users().update_one({"_id": user["id"]}, {"$set": {"github": gh, "badges": badges}})
    return {"ok": True, "badges": badges}
```

## File: `backend/audit_features.py`

```python
"""Section 1-11 audit: exercises every prompt.txt subfeature. Run: python audit_features.py"""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
passed = []


def check(name, cond):
    assert cond, f"FAILED: {name}"
    passed.append(name)


def signup(email, role="both", name=None):
    r = c.post("/auth/signup", json={"email": email, "password": "Pass1234",
                                     "name": name or email.split("@")[0], "role": role})
    assert r.status_code == 200, (email, r.text)
    return r.json()


# ---------- 1. Auth ----------
s = signup("audit-seller@test.com", "seller")
b = signup("audit-buyer@test.com", "buyer")
hs = {"Authorization": f"Bearer {s['access_token']}"}
hb = {"Authorization": f"Bearer {b['access_token']}"}
check("1.1 signup", "access_token" in s)
r = c.post("/auth/login", json={"email": "audit-buyer@test.com", "password": "Pass1234"})
check("1.1 login JWT", r.status_code == 200 and "access_token" in r.json())
r = c.post("/auth/refresh", json={"refresh_token": b["refresh_token"]})
check("1.1 refresh", r.status_code == 200 and "access_token" in r.json())
check("1.1 logout", c.post("/auth/logout", json={"refresh_token": b["refresh_token"]}, headers=hb).status_code == 200)
check("1.1 pw rules", c.post("/auth/signup", json={"email": "x@t.com", "password": "short",
                                                   "name": "x", "role": "buyer"}).status_code in (400, 422))
tok = s["verify_token_dev"]
check("1.1 verify email", c.post("/auth/verify-email", json={"token": tok}).status_code == 200)
f = c.post("/auth/forgot-password", json={"email": "audit-buyer@test.com"})
check("1.1 forgot", f.status_code == 200)
check("1.1 reset", c.post("/auth/reset-password", json={"token": f.json()["reset_token_dev"],
                                                        "password": "Newpass123"}).status_code == 200)
check("1.1 oauth stub", c.post("/auth/oauth/callback", json={"email": "gh@test.com", "name": "GH"}).status_code == 200)
check("1.1 2fa", c.post("/auth/2fa/enable", headers=hb).status_code == 200)
check("1.2 roles/profile/edit", c.get("/users/me", headers=hb).status_code == 200)
check("1.2 seller fields", c.patch("/users/me", json={"skills": ["python"], "github": "gh",
                                                       "portfolio": ["https://x"]}, headers=hs).status_code == 200)
check("1.2 public profile", c.get(f"/users/{s['user']['id']}").status_code == 200)
check("1.2 badges", c.post("/users/me/link-github", json={"github": "gh"}, headers=hs).status_code == 200)
check("1.2 follow", c.post(f"/users/{s['user']['id']}/follow", json={"following": True}, headers=hb).status_code == 200)
check("1.3 buyer blocked from sell", c.post("/listings", json={"title": "Nope nope nope",
      "description": "should fail validation here", "price": 5, "category": "Other"}, headers=hb).status_code == 403)
check("1.3 unauth blocked", c.get("/users/me").status_code in (401, 403))

# ---------- 2. Listings ----------
lst = {"title": "Audit Web App", "description": "A complete audit test project with docs",
       "price": 50, "category": "Web App", "tech_stack": ["react"],
       "demo_video": "https://loom.test/x", "pricing_tiers": [{"name": "code", "price": 50}],
       "license": "resale", "accept_offers": True, "file_hash": "abc123audit"}
r = c.post("/listings", json=lst, headers=hs)
check("2.1 create full", r.status_code == 200)
lid = r.json()["id"]
check("2.1 edit", c.patch(f"/listings/{lid}", json={"price": 55}, headers=hs).status_code == 200)
check("2.2 feed/search/filter/sort", c.get("/listings?q=audit&category=Web+App&sort=price_asc").status_code == 200)
check("2.2 rating+bids filter", c.get("/listings?min_rating=0&open_to_bids=true").status_code == 200)
check("2.2 related/featured/trending/tags",
      c.get(f"/listings/{lid}/related").status_code == 200
      and c.get("/listings/featured").status_code == 200
      and c.get("/listings/trending").status_code == 200
      and c.get("/listings/tags").status_code == 200)
d1 = c.get(f"/listings/{lid}").json()
d2 = c.get(f"/listings/{lid}").json()
check("2.3 detail+views+buy", d2["views"] == d1["views"] + 1 and d2["license"] == "resale")
check("2.1 duplicate hash flag",
      c.post("/listings", json={**lst, "title": "Audit Clone Project"}, headers=hs).json().get("duplicate_warning") is True)
check("2.3 report", c.post(f"/listings/{lid}/report", json={"reason": "test"}, headers=hb).status_code == 200)
check("2.1 archive", c.delete(f"/listings/{lid}", headers=hs).status_code == 200)
dl = c.post("/listings", json={**lst, "title": "Audit Delete Me", "file_hash": "del1"}, headers=hs).json()
check("2.1 delete non-owner blocked", c.delete(f"/listings/{dl['id']}", headers=hb).status_code == 403)
check("2.1 seller delete", c.delete(f"/listings/{dl['id']}", headers=hs).status_code == 200
      and c.get(f"/listings/{dl['id']}").json()["status"] == "removed")
# fresh listing for order flow
r = c.post("/listings", json={**lst, "title": "Audit Buy Flow", "file_hash": "buyflow1"}, headers=hs)
buy_id = r.json()["id"]

# ---------- 3. Orders ----------
o = c.post("/orders", json={"listing_id": buy_id}, headers=hb).json()
check("3.1 buy+intent", o["status"] == "pending" and o["client_secret"])
oid = o["id"]
check("3.1 webhook mock", c.post("/webhooks/stripe", content=b"{}").status_code == 200)
check("3.1 mock-pay", c.post(f"/orders/{oid}/mock-pay", headers=hb).status_code == 200)
check("2.1 delete blocked w/ live order", c.delete(f"/listings/{buy_id}", headers=hs).status_code == 400)
check("3.1 dashboards", c.get("/orders/purchases", headers=hb).status_code == 200
      and c.get("/orders/sales", headers=hs).status_code == 200)
check("3.1 order titles", c.get("/orders/purchases", headers=hb).json()[0].get("listing_title") == "Audit Buy Flow")
dlv = c.post(f"/orders/{oid}/deliver", headers=hs).json()
check("3.2 deliver", dlv["status"] == "delivered")
check("3.2 token download", c.get(f"/orders/{oid}/download?token=" + dlv["download_token"], headers=hb).status_code in (200, 404))
check("3.2 bad token rejected", c.get(f"/orders/{oid}/download?token=wrong", headers=hb).status_code == 403)
check("3.2 confirm+payout", c.post(f"/orders/{oid}/confirm", headers=hb).json().get("payout_to_seller", 0) > 0)
check("3.2 dispute", c.post(f"/orders/{oid}/dispute", headers=hb).status_code == 200)
check("3.3 connect+commission+payouts",
      c.post("/payments/connect-onboard", headers=hs).status_code == 200
      and c.get("/payments/payouts", headers=hs).json()["total"] > 0
      and c.get("/payments/tax-doc", headers=hs).status_code == 200)
# admin for refund/resolve
a = signup("audit-admin@test.com", "both")
c.patch("/users/me", json={"role": "admin"}, headers={"Authorization": f"Bearer {a['access_token']}"})
ha = {"Authorization": f"Bearer {a['access_token']}"}
check("3.3 refund", c.post(f"/orders/{oid}/refund", headers=ha).status_code == 200)
check("3.4 admin orders+resolve", c.get("/admin/orders", headers=ha).status_code == 200
      and c.post(f"/admin/orders/{oid}/resolve", json={"action": "release"}, headers=ha).status_code == 200)
check("3.4 auto rules job", c.post("/jobs/run", headers=ha).status_code == 200)

# ---------- 4. Bidding ----------
bl = c.post("/listings", json={**lst, "title": "Audit Bid Item", "file_hash": "bid1"}, headers=hs).json()
bid = c.post(f"/listings/{bl['id']}/bids", json={"amount": 40, "message": "hi"}, headers=hb).json()
check("4 place+list", bid["id"] and len(c.get(f"/listings/{bl['id']}/bids", headers=hs).json()) >= 1)
check("4 counter", c.post(f"/bids/{bid['id']}/counter", json={"amount": 45}, headers=hs).status_code == 200)
bid2 = c.post(f"/listings/{bl['id']}/bids", json={"amount": 42}, headers=hb).json()
acc = c.post(f"/bids/{bid2['id']}/accept", headers=hs).json()
check("4 accept->order", acc.get("order_id"))
check("4 analytics", c.get("/bids/analytics", headers=hs).status_code == 200)
check("4 incoming inbox", any(b.get("listing_title") for b in c.get("/bids/incoming", headers=hs).json()))
check("4 reject", c.post(f"/bids/{bid['id']}/reject", headers=hs).status_code in (200, 400))

# ---------- 5. Messaging ----------
th = c.post("/threads", json={"listing_id": bl["id"]}, headers=hb).json()
check("5 thread", th["id"])
check("5 send+poll", c.post(f"/threads/{th['id']}/messages", json={"text": "hello?"}, headers=hb).status_code == 200
      and len(c.get(f"/threads/{th['id']}/messages", headers=hs).json()) >= 1)
check("5 unread+block/report", c.get("/threads", headers=hs).status_code == 200
      and c.post(f"/users/{b['user']['id']}/block", headers=hs).status_code == 200
      and c.post(f"/users/{b['user']['id']}/report", json={"reason": "spam"}, headers=hs).status_code == 200)

# ---------- 6. Reviews ----------
o2 = c.post("/orders", json={"listing_id": bl["id"]}, headers=hb).json()
c.post(f"/orders/{o2['id']}/mock-pay", headers=hb)
c.post(f"/orders/{o2['id']}/deliver", headers=hs)
c.post(f"/orders/{o2['id']}/confirm", headers=hb)
rv = c.post(f"/orders/{o2['id']}/reviews", json={"rating": 5, "comment": "great"}, headers=hb)
check("6 review+avg", rv.status_code == 200 and c.get(f"/listings/{bl['id']}/reviews").status_code == 200)
check("6 seller rating denormalized", c.get(f"/listings/{bl['id']}").json().get("seller_rating", 0) >= 5
      and len(c.get("/listings?min_rating=4&limit=50").json()["items"]) >= 1)
rid = rv.json()["id"]
check("6 respond+report", c.post(f"/reviews/{rid}/respond", json={"response": "ty"}, headers=hs).status_code == 200
      and c.post(f"/reviews/{rid}/report", json={"reason": "fake"}, headers=hb).status_code == 200)

# ---------- 7. Admin ----------
check("7 stats/users/ban", c.get("/admin/stats", headers=ha).status_code == 200
      and c.get("/admin/users", headers=ha).status_code == 200
      and c.post(f"/admin/users/{b['user']['id']}/ban", json={"banned": False}, headers=ha).status_code == 200)
check("7 listings mod", c.get("/admin/listings", headers=ha).status_code == 200
      and c.post(f"/admin/listings/{bl['id']}/feature", json={"featured": True}, headers=ha).status_code == 200
      and c.get("/admin/reports", headers=ha).status_code == 200
      and c.get("/admin/analytics", headers=ha).status_code == 200
      and c.post("/admin/payouts/override", json={"order_id": oid, "seller_id": s["user"]["id"],
                                                  "amount": 1}, headers=ha).status_code == 200)
check("7 non-admin blocked", c.get("/admin/stats", headers=hb).status_code == 403)

# ---------- 8. Notifications ----------
check("8 list+prefs", c.get("/notifications", headers=hs).status_code == 200
      and c.get("/notifications/prefs", headers=hs).status_code == 200
      and c.post("/notifications/prefs", json={"opt_out": {"system": True}}, headers=hs).status_code == 200)

# ---------- 9/10/11 ----------
check("9 categories", "Web App" in c.get("/listings/categories").json()["categories"])
check("9 category specs", c.post("/listings", json={**lst, "title": "Audit Specs Item",
      "file_hash": "specs1", "specs": {"dataset size": "10k rows", "accuracy": "94%"}}, headers=hs).json().get("specs", {}).get("accuracy") == "94%")
check("10 similarity stub", c.post("/uploads/similarity-check", json={}, headers=hs).status_code == 200)
check("10 strikes tracked", isinstance(c.get(f"/users/{s['user']['id']}").json().get("strikes"), int))
check("6 weighted rating", isinstance(c.get(f"/users/{s['user']['id']}").json().get("rating_weighted"), (int, float)))
check("8 push stub", c.post("/notifications/push-token", json={"token": "dev-token"}, headers=hs).status_code == 200)
check("11 health", c.get("/health").json() == {"ok": True})

print(f"\nAUDIT OK: {len(passed)}/{len(passed)} checks passed")
for p in passed:
    print("  [ok]", p)
```

## File: `backend/backfill_ratings.js`

```javascript
// One-off backfill: denormalize seller/listing ratings from reviews.
// Run: mongosh --quiet backfill_ratings.js
db = db.getSiblingDB('projectbidding');
var sag = db.reviews.aggregate([{$group: {_id: '$seller_id', avg: {$avg: '$rating'}, n: {$sum: 1}}}]).toArray();
sag.forEach(function (a) {
  var v = Math.round(a.avg * 100) / 100;
  db.listings.updateMany({seller_id: a._id}, {$set: {seller_rating: v, seller_rating_count: a.n}});
});
var lag = db.reviews.aggregate([{$group: {_id: '$listing_id', avg: {$avg: '$rating'}, n: {$sum: 1}}}]).toArray();
lag.forEach(function (a) {
  var v = Math.round(a.avg * 100) / 100;
  db.listings.updateOne({_id: a._id}, {$set: {rating: v, rating_count: a.n, rating_weighted: v}});
});
print('sellers updated: ' + sag.length + ', listings updated: ' + lag.length);
```

## File: `backend/cleanup_demo.js`

```javascript
db = db.getSiblingDB('projectbidding');
uids = db.users.find({email: /^demo-(seller|buyer)@test\.com$/}, {_id: 1}).toArray().map(u => u._id);
print('demo/test users: ' + uids.length);
uids.forEach(function (id) {
  db.listings.deleteMany({seller_id: id});
  db.orders.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.bids.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.reviews.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.users.deleteOne({_id: id});
});
print('after: users=' + db.users.countDocuments() + ' listings=' + db.listings.countDocuments());
```

## File: `backend/cleanup_seed.js`

```javascript
db = db.getSiblingDB('projectbidding');
uids = db.users.find({email: /@example\.com$/}, {_id: 1}).toArray().map(u => u._id);
print('seed users found: ' + uids.length);
if (uids.length > 0) {
  tids = db.threads.find({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]}, {_id: 1}).toArray().map(t => t._id);
  db.messages.deleteMany({thread_id: {$in: tids}});
  db.users.deleteMany({_id: {$in: uids}});
  db.listings.deleteMany({seller_id: {$in: uids}});
  db.orders.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.bids.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.reviews.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.threads.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.payouts.deleteMany({seller_id: {$in: uids}});
  db.notifications.deleteMany({user_id: {$in: uids}});
  db.follows.deleteMany({$or: [{by: {$in: uids}}, {target: {$in: uids}}]});
  db.reports.deleteMany({$or: [{by: {$in: uids}}, {target: {$in: uids}}]});
  db.resets.deleteMany({user_id: {$in: uids}});
  db.verifies.deleteMany({user_id: {$in: uids}});
}
print('after: users=' + db.users.countDocuments() + ' listings=' + db.listings.countDocuments());
```

## File: `backend/demo_delete.py`

```python
"""Live demo: seller project deletion (clean delete + live-order guard)."""
import httpx

B = "http://localhost:8000"
c = httpx.Client(base_url=B, timeout=20)


def signup(email, role):
    r = c.post("/auth/signup", json={"email": email, "password": "Pass1234", "name": email.split("@")[0], "role": role})
    if "already registered" in r.text:
        r = c.post("/auth/login", json={"email": email, "password": "Pass1234"})
    return r.json()


s = signup("demo-seller@test.com", "seller")
b = signup("demo-buyer@test.com", "buyer")
hs = {"Authorization": "Bearer " + s["access_token"]}
hb = {"Authorization": "Bearer " + b["access_token"]}

mk = lambda title: c.post("/listings", json={"title": title, "description": "demo delete flow project",
                                             "price": 25, "category": "Other"}, headers=hs).json()

# 1. clean delete
a = mk("Demo Delete Clean Project")
r = c.delete(f"/listings/{a['id']}", headers=hs)
print("1. clean delete:", r.status_code, r.json())
print("   status now:", c.get(f"/listings/{a['id']}").json()["status"])
print("   in browse:", any(x["id"] == a["id"] for x in c.get("/listings?q=Demo+Delete+Clean&limit=50").json()["items"]))

# 2. delete blocked with live order
d = mk("Demo Delete Guarded Project")
o = c.post("/orders", json={"listing_id": d["id"]}, headers=hb).json()
r = c.delete(f"/listings/{d['id']}", headers=hs)
print("2. delete w/ pending order:", r.status_code, "-", r.json().get("detail"))

# 3. after fulfilment, delete allowed
c.post(f"/orders/{o['id']}/mock-pay", headers=hb)
c.post(f"/orders/{o['id']}/deliver", headers=hs)
c.post(f"/orders/{o['id']}/confirm", headers=hb)
r = c.delete(f"/listings/{d['id']}", headers=hs)
print("3. delete after completed:", r.status_code, r.json())
print("DEMO OK")
```

## File: `backend/requirements.txt`

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
motor==3.6.0
pymongo==4.9.2
PyJWT==2.10.1
bcrypt==4.2.1
python-multipart==0.0.20
pydantic==2.10.4
pydantic-settings==2.7.0
email-validator==2.2.0
stripe==11.1.0
boto3==1.35.90
httpx==0.28.1
```

## File: `backend/seed.py`

```python
"""Seed the marketplace: 20 buyers + 40 sellers with ongoing/sold projects.

Usage (server must be running for --api mode):
    python seed.py --api http://localhost:8000 [--seed 42]
    python seed.py --direct   # insert straight into DB layer (dev/tests)

All seeded users share password: Seed1234
Idempotent in --api mode: existing emails are skipped.
"""
import argparse
import asyncio
import random
import sys

sys.path.insert(0, ".")
from app.core.seed_data import build


# ---------------- API mode (against a running server) ----------------
def _api(seed: int, base: str):
    import httpx

    data = build(seed=seed)
    c = httpx.Client(base_url=base, timeout=30.0)
    rng = random.Random(seed + 1)

    def signup(u: dict) -> dict | None:
        for attempt in range(5):
            r = c.post("/auth/signup", json={"email": u["email"], "password": u["password"],
                                             "name": u["name"], "role": u["role"]})
            if r.status_code == 200:
                return r.json()
            if "already registered" in r.text:
                r = c.post("/auth/login", json={"email": u["email"], "password": u["password"]})
                return r.json() if r.status_code == 200 else None
            if r.status_code == 429:
                import time
                time.sleep(5 * (attempt + 1))
                continue
            print("signup failed:", u["email"], r.text)
            return None
        print("signup rate-limited, giving up:", u["email"])
        return None

    print("Signing up buyers...")
    buyer_tokens = []
    for u in data["buyers"]:
        s = signup(u)
        if s:
            buyer_tokens.append((s["user"], s["access_token"]))
    print(f"  buyers: {len(buyer_tokens)}")

    print("Signing up sellers + publishing projects...")
    sellers = []  # (user, token, ongoing_ids, sold_ids)
    for u in data["sellers"]:
        s = signup(u)
        if not s:
            continue
        tok, user = s["access_token"], s["user"]
        h = {"Authorization": f"Bearer {tok}"}
        # storefront profile
        c.patch("/users/me", json={"bio": u["bio"], "avatar": u["avatar"], "skills": u["skills"],
                                   "github": u["github"], "portfolio": u["portfolio"]}, headers=h)
        if u["badges"]:
            c.post("/users/me/link-github", json={"github": u["github"]}, headers=h)
        ongoing_ids, sold_ids = [], []
        mine = c.get("/listings/mine", headers=h)
        existing_titles = {l["title"] for l in mine.json()} if mine.status_code == 200 else set()
        for item in u["ongoing"] + u["sold"]:
            if item["title"] in existing_titles:
                continue  # idempotent re-run
            r = c.post("/listings", json=item, headers=h)
            if r.status_code == 200:
                lid = r.json()["id"]
                (sold_ids if item in u["sold"] else ongoing_ids).append((lid, item["price"], item["title"]))
        sellers.append((user, tok, ongoing_ids, sold_ids))
    print(f"  sellers: {len(sellers)}")

    # Simulate sales: each sold listing bought by a rotating buyer, full flow
    print("Simulating purchases (paid -> delivered -> completed + reviews)...")
    n_orders = n_reviews = 0
    bi = 0
    if sellers and buyer_tokens:
        for user, stok, _, sold in sellers:
            sh = {"Authorization": f"Bearer {stok}"}
            for lid, price, title in sold:
                buser, btok = buyer_tokens[bi % len(buyer_tokens)]
                bi += 1
                bh = {"Authorization": f"Bearer {btok}"}
                o = c.post("/orders", json={"listing_id": lid}, headers=bh)
                if o.status_code != 200:
                    continue
                oid = o.json()["id"]
                c.post(f"/orders/{oid}/mock-pay", headers=bh)
                c.post(f"/orders/{oid}/deliver", headers=sh)
                c.post(f"/orders/{oid}/confirm", headers=bh)
                n_orders += 1
                if rng.random() < 0.7:
                    rv = c.post(f"/orders/{oid}/reviews",
                                json={"rating": rng.choice([4, 4, 5, 5, 5]), "comment": rng.choice(data["comments"])},
                                headers=bh)
                    if rv.status_code == 200 and rng.random() < 0.4:
                        c.post(f"/reviews/{rv.json()['id']}/respond", json={"response": "Thanks for buying!"}, headers=sh)
                    n_reviews += 1
    print(f"  completed orders: {n_orders}, reviews: {n_reviews}")

    # Bids on ~1 active listing per seller + follows
    print("Adding bids + follows...")
    n_bids = n_follows = 0
    if sellers and buyer_tokens:
        for idx, (user, stok, ongoing, _) in enumerate(sellers):
            if ongoing:
                lid, price, _ = ongoing[0]
                buser, btok = buyer_tokens[idx % len(buyer_tokens)]
                bh0 = {"Authorization": f"Bearer {btok}"}
                try:
                    mine_bids = c.get("/bids/mine", headers=bh0).json()
                    if any(b["listing_id"] == lid for b in mine_bids):
                        continue  # already bid (idempotent re-run)
                except Exception:
                    pass
                r = c.post(f"/listings/{lid}/bids", json={"amount": round(price * 0.85, 2), "message": "Student budget, please accept!"},
                           headers=bh0)
                if r.status_code == 200:
                    n_bids += 1
    for i, (buser, btok) in enumerate(buyer_tokens):
        for j in range(4):
            t = sellers[(i * 4 + j) % len(sellers)][0]["id"]
            if c.post(f"/users/{t}/follow", json={"following": True},
                      headers={"Authorization": f"Bearer {btok}"}).status_code == 200:
                n_follows += 1
    print(f"  bids: {n_bids}, follows: {n_follows}")
    print(f"\nDone. Login anywhere with password '{data['password']}', e.g. {data['sellers'][0]['email']}")


# ---------------- Direct mode (DB layer, same process) ----------------
async def _direct(seed: int):
    from app.core.security import hash_password, new_id, utcnow
    from app.db.database import init_db, col

    await init_db()
    data = build(seed=seed)
    rng = random.Random(seed + 1)
    now = utcnow().isoformat()

    buyer_ids = []
    for u in data["buyers"]:
        uid = new_id()
        await col("users").insert_one({"_id": uid, "email": u["email"], "password": hash_password(u["password"]),
                                       "name": u["name"], "role": "buyer", "bio": "", "avatar": "",
                                       "stripe_account_id": "", "email_verified": True, "badges": [],
                                       "skills": [], "github": "", "portfolio": [], "created_at": now})
        buyer_ids.append(uid)
    n_list = n_ord = 0
    for i, u in enumerate(data["sellers"]):
        uid = new_id()
        await col("users").insert_one({"_id": uid, "email": u["email"], "password": hash_password(u["password"]),
                                       "name": u["name"], "role": "seller", "bio": u["bio"], "avatar": u["avatar"],
                                       "stripe_account_id": "", "email_verified": True, "badges": u["badges"],
                                       "skills": u["skills"], "github": u["github"], "portfolio": u["portfolio"],
                                       "created_at": now})
        for item in u["ongoing"]:
            await col("listings").insert_one({"_id": new_id(), **item, "project_file": "", "file_hash": "",
                                              "flagged_duplicate": False, "featured": False, "rating": 0,
                                              "rating_count": 0, "views": rng.randint(5, 400),
                                              "seller_id": uid, "created_at": now, "updated_at": now})
            n_list += 1
        for item in u["sold"]:
            lid = new_id()
            await col("listings").insert_one({"_id": lid, **{k: v for k, v in item.items() if k != "status"},
                                              "status": "sold", "project_file": "", "file_hash": "",
                                              "flagged_duplicate": False, "featured": False,
                                              "rating": rng.choice([4, 4.5, 5]), "rating_count": rng.randint(1, 4),
                                              "views": rng.randint(50, 900),
                                              "seller_id": uid, "created_at": now, "updated_at": now})
            n_list += 1
            buy = buyer_ids[i % len(buyer_ids)]
            oid = new_id()
            fee = round(item["price"] * 0.10, 2)
            await col("orders").insert_one({"_id": oid, "listing_id": lid, "buyer_id": buy, "seller_id": uid,
                                            "amount": item["price"], "fee": fee, "status": "completed",
                                            "client_secret": "mock", "download_token": "mock",
                                            "created_at": now})
            await col("payouts").insert_one({"_id": new_id(), "order_id": oid, "seller_id": uid,
                                             "amount": round(item["price"] - fee, 2), "fee": fee, "created_at": now})
            n_ord += 1
    print(f"Direct-seeded: {len(buyer_ids)} buyers, {len(data['sellers'])} sellers, {n_list} listings, {n_ord} orders")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="", help="Base URL of running backend, e.g. http://localhost:8000")
    ap.add_argument("--direct", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.api:
        _api(a.seed, a.api.rstrip("/"))
    elif a.direct:
        asyncio.run(_direct(a.seed))
    else:
        ap.print_help()
```

## File: `backend/tests/__init__.py`

```python

```

## File: `backend/tests/test_phase2.py`

```python
"""Phase-2 flows: bidding, messaging, reviews, notifications, admin, jobs."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def _signup(email, role="both"):
    r = c.post("/auth/signup", json={"email": email, "password": "pass1234", "name": email.split("@")[0], "role": role})
    assert r.status_code == 200, r.text
    return r.json()


def test_full_phase2():
    s = _signup("s2@test.com", "seller")
    b = _signup("b2@test.com", "buyer")
    hs = {"Authorization": f"Bearer {s['access_token']}"}
    hb = {"Authorization": f"Bearer {b['access_token']}"}

    l = c.post("/listings", json={"title": "Bid Project", "description": "A project open to bids xyz",
                                  "price": 100, "category": "Web App", "tech_stack": ["react"]}, headers=hs)
    assert l.status_code == 200, l.text
    lid = l.json()["id"]

    # bidding
    bid = c.post(f"/listings/{lid}/bids", json={"amount": 80, "message": "offer"}, headers=hb)
    assert bid.status_code == 200, bid.text
    bid_id = bid.json()["id"]
    acc = c.post(f"/bids/{bid_id}/accept", headers=hs)
    assert acc.status_code == 200, acc.text
    oid = acc.json()["order_id"]

    # messaging
    th = c.post("/threads", json={"listing_id": lid}, headers=hb)
    assert th.status_code == 200, th.text
    tid = th.json()["id"]
    m = c.post(f"/threads/{tid}/messages", json={"text": "Is this available?"}, headers=hb)
    assert m.status_code == 200, m.text

    # complete order then review
    c.post(f"/orders/{oid}/mock-pay", headers=hb)
    c.post(f"/orders/{oid}/deliver", headers=hs)
    cf = c.post(f"/orders/{oid}/confirm", headers=hb)
    assert cf.status_code == 200, cf.text
    rv = c.post(f"/orders/{oid}/reviews", json={"rating": 5, "comment": "great"}, headers=hb)
    assert rv.status_code == 200, rv.text
    resp = c.post(f"/reviews/{rv.json()['id']}/respond", json={"response": "thanks!"}, headers=hs)
    assert resp.status_code == 200, resp.text

    # notifications + prefs
    n = c.get("/notifications", headers=hs)
    assert n.status_code == 200 and n.json()["unread"] >= 1

    # related/trending/featured/tags
    assert c.get(f"/listings/{lid}/related").status_code == 200
    assert c.get("/listings/trending").status_code == 200
    assert c.get("/listings/tags").status_code == 200

    # payouts
    p = c.get("/payments/payouts", headers=hs)
    assert p.status_code == 200 and p.json()["total"] > 0

    # follow
    f = c.post(f"/users/{s['user']['id']}/follow", headers=hb)
    assert f.status_code == 200


def test_auth_extras():
    u = _signup("extra@test.com")
    tok = u["verify_token_dev"]
    assert c.post("/auth/verify-email", json={"token": tok}).status_code == 200
    f = c.post("/auth/forgot-password", json={"email": "extra@test.com"})
    assert f.status_code == 200
    rt = f.json()["reset_token_dev"]
    assert c.post("/auth/reset-password", json={"token": rt, "password": "newpass123"}).status_code == 200
    lg = c.post("/auth/login", json={"email": "extra@test.com", "password": "newpass123"})
    assert lg.status_code == 200


def test_jobs_and_reports():
    assert c.get("/listings/categories").status_code == 200
    s = _signup("rep@test.com", "seller")
    hs = {"Authorization": f"Bearer {s['access_token']}"}
    l = c.post("/listings", json={"title": "Report me", "description": "report this project xyz",
                                  "price": 10, "category": "Other"}, headers=hs)
    lid = l.json()["id"]
    assert c.post(f"/listings/{lid}/report", json={"reason": "stolen"}, headers=hs).status_code == 200
```

## File: `backend/verify_seed.py`

```python
"""Quick check of seeded storefront data. Usage: python verify_seed.py --api http://localhost:8001"""
import argparse
import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--api", default="http://localhost:8000")
a = ap.parse_args()
c = httpx.Client(base_url=a.api.rstrip("/"), timeout=30)

sellers = c.get("/users/sellers/top?limit=50").json()
print("top_sellers:", len(sellers))
s0 = sellers[0]
print("top:", s0["name"], "| ongoing:", s0["ongoing_count"], "| sold:", s0["sold_count"],
      "| followers:", s0["followers"], "| rating:", s0["rating"])
p = c.get("/users/" + s0["id"]).json()
print("profile:", p["name"], "| ongoing_projects:", len(p["ongoing_projects"]),
      "| sold_projects:", len(p["sold_projects"]), "| earned:", p["total_earned"])
print("sold sample:", [(t["title"], t["price"]) for t in p["sold_projects"][:2]])
print("ongoing sample:", [(t["title"], t["price"]) for t in p["ongoing_projects"][:2]])
print("browse active total:", c.get("/listings?limit=1").json()["total"])
assert len(sellers) == 40, len(sellers)
assert p["sold_count"] > 0 and p["ongoing_count"] > 0
print("SEED VERIFY OK")
```

## File: `frontend/.env.example`

```text
# Point the frontend at your backend (default http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

## File: `frontend/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Project Bidding — MVP</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

## File: `frontend/package.json`

```json
{
  "name": "projectbidding-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.7"
  }
}
```

## File: `frontend/src/api.js`

```javascript
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function tokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

async function refreshAccess() {
  const { refresh } = tokens();
  if (!refresh) return null;
  const r = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!r.ok) return null;
  const data = await r.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data.access_token;
}

export async function api(path, opts = {}, retry = true) {
  const { access } = tokens();
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      ...(opts.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(opts.headers || {}),
      ...(access ? { Authorization: `Bearer ${access}` } : {}),
    },
  });
  if (res.status === 401 && retry) {
    const next = await refreshAccess();
    if (next) return api(path, opts, false);
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      msg = j.detail || JSON.stringify(j);
    } catch {}
    throw new Error(msg);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export const API_BASE = BASE;
```

## File: `frontend/src/App.jsx`

```jsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { Nav } from './Nav';
import { Browse } from './pages/Browse';
import { ListingDetail } from './pages/ListingDetail';
import { Login, Signup, Profile } from './pages/Auth';
import { Forgot, Reset, VerifyEmail } from './pages/Password';
import { NewListing } from './pages/NewListing';
import { EditListing } from './pages/EditListing';
import { Dashboard } from './pages/Dashboard';
import { Messages } from './pages/Messages';
import { Admin } from './pages/Admin';
import { Notifications } from './pages/Notifications';
import { SellerProfile } from './pages/SellerProfile';
import { Sellers } from './pages/Sellers';
import './styles.css';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Nav />
        <main className="container">
          <Routes>
            <Route path="/" element={<Browse />} />
            <Route path="/l/:id" element={<ListingDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot" element={<Forgot />} />
            <Route path="/reset" element={<Reset />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/new" element={<NewListing />} />
            <Route path="/edit/:id" element={<EditListing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/u/:id" element={<SellerProfile />} />
            <Route path="/sellers" element={<Sellers />} />
          </Routes>
        </main>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

## File: `frontend/src/AuthContext.jsx`

```jsx
import { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; }
  });

  async function load() {
    if (!localStorage.getItem('access_token')) return;
    try {
      const me = await api('/users/me');
      setUser(me);
      localStorage.setItem('user', JSON.stringify(me));
    } catch { /* logged out */ }
  }
  useEffect(() => { load(); }, []);

  async function signup(email, password, name, role) {
    const data = await api('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, name, role }) });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }
  async function login(email, password) {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }
  async function logout() {
    try {
      await api('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') }) });
    } catch {}
    localStorage.clear();
    setUser(null);
  }
  return <Ctx.Provider value={{ user, setUser, signup, login, logout }}>{children}</Ctx.Provider>;
}
```

## File: `frontend/src/main.jsx`

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

createRoot(document.getElementById('root')).render(<App />);
```

## File: `frontend/src/Nav.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { api } from './api';

export function Nav() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    if (!user) return;
    api('/notifications').then(n => setUnread(n.unread)).catch(() => {});
    const t = setInterval(() => api('/notifications').then(n => setUnread(n.unread)).catch(() => {}), 15000);
    return () => clearInterval(t);
  }, [user]);
  const role = user?.role;
  const canSell = role === 'seller' || role === 'both' || role === 'admin';
  const dashLabel = role === 'buyer' ? 'My Orders' : role === 'seller' ? 'My Shop' : 'Dashboard';
  return (
    <nav className="nav">
      <Link to="/" className="brand">ProjectBidding</Link>
      <div className="links">
        <Link to="/">Browse</Link>
        <Link to="/sellers">Sellers</Link>
        {user && canSell && <Link to="/new">Sell</Link>}
        {user && <Link to="/dashboard">{dashLabel}</Link>}
        {user && <Link to="/messages">Messages</Link>}
        {user && <Link to="/notifications">🔔{unread ? `(${unread})` : ''}</Link>}
        {user && <Link to="/profile">Profile</Link>}
        {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
        {!user && <Link to="/login">Login</Link>}
        {!user && <Link to="/signup" className="btn">Sign up</Link>}
        {user && <span className={`role-pill ${role}`}>{role}</span>}
        {user && <button onClick={async () => { await logout(); nav('/'); }}>Logout</button>}
      </div>
    </nav>
  );
}
```

## File: `frontend/src/pages/Admin.jsx`

```jsx
import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Admin() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [reports, setReports] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        setStats(await api('/admin/stats'));
        setUsers(await api('/admin/users'));
        setOrders(await api('/admin/orders'));
        setReports(await api('/admin/reports'));
      } catch {}
    })();
  }, []);
  if (!user) return <p>Login required.</p>;
  if (user.role !== 'admin') return <p>Admin only. (Set your role to "admin" via PATCH /users/me.)</p>;

  return (
    <div>
      <h2>Admin</h2>
      {stats && <p className="muted">Users {stats.users} · Listings {stats.listings} · Orders {stats.orders} · GMV ${stats.gmv} · {JSON.stringify(stats.orders_by_status)}</p>}
      <h3>Disputes / orders</h3>
      {orders.filter(o => o.status === 'disputed').map(o => (
        <div key={o._id} className="row-card">
          <span>{o._id.slice(0, 8)} · ${o.amount}</span>
          <span>
            <button onClick={async () => { await api(`/admin/orders/${o._id}/resolve`, { method: 'POST', body: JSON.stringify({ action: 'refund' }) }); alert('refunded'); }}>Refund buyer</button>
            <button onClick={async () => { await api(`/admin/orders/${o._id}/resolve`, { method: 'POST', body: JSON.stringify({ action: 'release' }) }); alert('released'); }}>Release to seller</button>
          </span>
        </div>
      ))}
      <h3>Users</h3>
      {users.map(u => (
        <div key={u.id} className="row-card">
          <span>{u.email} · {u.role} {u.banned ? '(banned)' : ''}</span>
          <button onClick={async () => { await api(`/admin/users/${u.id}/ban`, { method: 'POST', body: JSON.stringify({ banned: !u.banned }) }); }}>Toggle ban</button>
        </div>
      ))}
      <h3>Moderation queue ({reports.length})</h3>
      {reports.map((r, i) => <p key={i} className="muted">{r.type}: {r.target} — {r.reason} (by {r.by})</p>)}
      <button onClick={async () => { const r = await api('/jobs/run', { method: 'POST' }); alert(JSON.stringify(r)); }}>Run expiry jobs</button>
    </div>
  );
}
```

## File: `frontend/src/pages/Auth.jsx`

```jsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const { login } = useAuth();
  const nav = useNavigate();
  return (
    <div className="form">
      <h2>Login</h2>
      {err && <p className="error">{err}</p>}
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await login(email, password); nav('/'); } catch (e) { setErr(e.message); }
      }}>Login</button>
      <p className="muted"><Link to="/forgot">Forgot password?</Link> · <Link to="/verify-email">Verify email</Link></p>
      <button onClick={async () => {
        const r = await api('/auth/oauth/callback', { method: 'POST', body: JSON.stringify({ email: email || 'dev@test.com', name: 'GitHub User', github: 'octocat' }) });
        localStorage.setItem('access_token', r.access_token); localStorage.setItem('refresh_token', r.refresh_token);
        window.location.href = '/';
      }}>Continue with GitHub (mock)</button>
    </div>
  );
}

export function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('both');
  const [err, setErr] = useState('');
  const { signup } = useAuth();
  const nav = useNavigate();
  return (
    <div className="form">
      <h2>Sign up</h2>
      {err && <p className="error">{err}</p>}
      <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input placeholder="Password (8+ chars, letter+number)" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <select value={role} onChange={e => setRole(e.target.value)}>
        <option value="both">Buyer + Seller</option>
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
      </select>
      <button className="btn" onClick={async () => {
        try { await signup(email, password, name, role); nav('/'); } catch (e) { setErr(e.message); }
      }}>Create account</button>
    </div>
  );
}

export function Profile() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ name: user?.name || '', bio: user?.bio || '', role: user?.role || 'both', skills: (user?.skills || []).join(','), github: user?.github || '', portfolio: (user?.portfolio || []).join(','), interests: (user?.interests || []).join(',') });
  const [msg, setMsg] = useState('');
  if (!user) return <p>Login required.</p>;
  const isBuyer = form.role === 'buyer' || form.role === 'both';
  const isSeller = form.role === 'seller' || form.role === 'both';
  return (
    <div className="form">
      <h2>{isSeller && !isBuyer ? 'Seller profile' : isBuyer && !isSeller ? 'Buyer profile' : 'Edit profile'} {user.badges?.map(b => <small key={b}>✓{b}</small>)}</h2>
      <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
      <textarea placeholder="Bio" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />
      {isBuyer && (
        <input placeholder="Looking for (comma separated: ML projects, flutter apps)" value={form.interests} onChange={e => setForm({ ...form, interests: e.target.value })} />
      )}
      {isSeller && (<>
        <input placeholder="Skills (comma separated)" value={form.skills} onChange={e => setForm({ ...form, skills: e.target.value })} />
        <input placeholder="GitHub username" value={form.github} onChange={e => setForm({ ...form, github: e.target.value })} />
        <input placeholder="Portfolio links (comma separated)" value={form.portfolio} onChange={e => setForm({ ...form, portfolio: e.target.value })} />
      </>)}
      <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
        <option value="both">Buyer + Seller</option>
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
      </select>
      <button className="btn" onClick={async () => {
        const body = { ...form, skills: form.skills.split(',').map(s => s.trim()).filter(Boolean), portfolio: form.portfolio.split(',').map(s => s.trim()).filter(Boolean), interests: form.interests.split(',').map(s => s.trim()).filter(Boolean) };
        const me = await api('/users/me', { method: 'PATCH', body: JSON.stringify(body) });
        setUser(me); localStorage.setItem('user', JSON.stringify(me)); setMsg('Saved!');
      }}>Save</button>
      {msg && <p>{msg}</p>}
      {isSeller && (<>
      <button onClick={async () => {
        const r = await api('/payments/connect-onboard', { method: 'POST' });
        alert(`Connect: ${JSON.stringify(r)}`);
      }}>Connect Stripe payout account</button>
      <button onClick={async () => {
        const edu = prompt('Student email (.edu):'); if (!edu) return;
        const r = await api('/users/me/request-student-badge', { method: 'POST', body: JSON.stringify({ edu_email: edu }) });
        alert(JSON.stringify(r));
      }}>Verify student badge</button>
      <button onClick={async () => {
        const r = await api('/users/me/link-github', { method: 'POST', body: JSON.stringify({ github: form.github }) });
        alert(JSON.stringify(r));
      }}>Link GitHub (developer badge)</button>
      </>)}
      {isSeller && !isBuyer && (
        <p className="muted">Public storefront: <a href={`/u/${user.id}`}>view my shop</a></p>
      )}
      <button onClick={async () => {
        const r = await api('/auth/2fa/enable', { method: 'POST' });
        const code = prompt(`2FA setup: ${r.otpauth_url}\nEnter 6-digit code:`); if (!code) return;
        await api('/auth/2fa/verify', { method: 'POST', body: JSON.stringify({ code }) });
        alert('2FA enabled');
      }}>Enable 2FA</button>
    </div>
  );
}
```

## File: `frontend/src/pages/Bids.jsx`

```jsx
import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Bids({ listingId, sellerId }) {
  const { user } = useAuth();
  const [bids, setBids] = useState([]);
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');
  const [mine, setMine] = useState([]);
  const [stats, setStats] = useState(null);
  const isSeller = user && user.id === sellerId;

  async function load() {
    if (isSeller) {
      try { setBids(await api(`/listings/${listingId}/bids`)); } catch {}
      try { setStats(await api('/bids/analytics')); } catch {}
    }
    if (user) {
      try { setMine(await api('/bids/mine')); } catch {}
    }
  }
  useEffect(() => { load(); }, [listingId]);

  async function place() {
    await api(`/listings/${listingId}/bids`, { method: 'POST', body: JSON.stringify({ amount: Number(amount), message }) });
    setAmount(''); setMessage(''); load();
  }
  async function act(id, action, counter) {
    const body = action === 'counter' ? { amount: Number(prompt('Counter amount:')) } : {};
    await api(`/bids/${id}/${action}`, { method: 'POST', body: JSON.stringify(body) });
    load();
  }

  return (
    <div className="section">
      <h3>Offers {stats ? <small className="muted">({stats.total_bids} bids, {stats.accepted} accepted, avg ${stats.avg_accepted})</small> : null}</h3>
      {!isSeller && (
        <div className="row">
          <input type="number" placeholder="Your offer $" value={amount} onChange={e => setAmount(e.target.value)} />
          <input placeholder="Message (optional)" value={message} onChange={e => setMessage(e.target.value)} />
          <button onClick={place}>Place bid</button>
        </div>
      )}
      {isSeller && bids.map(b => (
        <div key={b.id} className="row-card">
          <span>${b.amount} {b.counter ? `(counter $${b.counter})` : ''} · {b.status} · {b.message}</span>
          <span>
            <button onClick={() => act(b.id, 'accept')}>Accept</button>
            <button onClick={() => act(b.id, 'reject')}>Reject</button>
            <button onClick={() => act(b.id, 'counter')}>Counter</button>
          </span>
        </div>
      ))}
      {!isSeller && mine.filter(b => b.listing_id === listingId).map(b => (
        <p key={b.id} className="muted">Your bid: ${b.amount} — {b.status}{b.counter ? ` (counter $${b.counter})` : ''}</p>
      ))}
    </div>
  );
}
```

## File: `frontend/src/pages/Browse.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

function img(u) {
  if (!u) return '';
  return u.startsWith('/') ? `${API_BASE}${u}` : u;
}

export function Browse() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [tech, setTech] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [sort, setSort] = useState('newest');
  const [cats, setCats] = useState([]);
  const [tags, setTags] = useState([]);
  const [minRating, setMinRating] = useState('');
  const [bidsOnly, setBidsOnly] = useState(false);
  const [featured, setFeatured] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  // "Picks for you": match buyer interests against category/tech (client-side, from loaded items)
  const picks = user && (user.interests || []).length
    ? items.filter(l => (user.interests || []).some(k => {
        const kw = k.toLowerCase();
        return l.category.toLowerCase().includes(kw) || (l.tech_stack || []).some(t => t.toLowerCase().includes(kw));
      })).slice(0, 4)
    : [];

  async function load(over = {}) {
    setLoading(true);
    setError('');
    try {
      const f = { q, category, tech, minPrice, maxPrice, sort, minRating, bidsOnly, ...over };
      const p = new URLSearchParams({ page: 1, limit: 24, sort: f.sort });
      if (f.q) p.set('q', f.q);
      if (f.category) p.set('category', f.category);
      if (f.tech) p.set('tech', f.tech);
      if (f.minPrice !== '') p.set('min_price', f.minPrice);
      if (f.maxPrice !== '') p.set('max_price', f.maxPrice);
      if (f.minRating) p.set('min_rating', f.minRating);
      if (f.bidsOnly) p.set('open_to_bids', 'true');
      const data = await api(`/listings?${p.toString()}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // initial data (static lists once)
  useEffect(() => {
    api('/listings/categories').then(d => setCats(d.categories)).catch(() => {});
    api('/listings/tags').then(d => setTags(d.tags)).catch(() => {});
    api('/listings/featured').then(setFeatured).catch(() => {});
    api('/listings/trending').then(setTrending).catch(() => {});
    load();
    // eslint-disable-next-line
  }, []);

  // auto-apply when dropdowns/checkbox change (pass fresh values explicitly)
  const auto = (patch) => {
    if (patch.category !== undefined) setCategory(patch.category);
    if (patch.sort !== undefined) setSort(patch.sort);
    if (patch.minRating !== undefined) setMinRating(patch.minRating);
    if (patch.bidsOnly !== undefined) setBidsOnly(patch.bidsOnly);
    if (patch.tech !== undefined) setTech(patch.tech);
    load(patch);
  };

  // debounce free-text search + price
  useEffect(() => {
    const t = setTimeout(() => load(), 450);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [q, minPrice, maxPrice]);

  function clear() {
    setQ(''); setCategory(''); setTech(''); setMinPrice(''); setMaxPrice('');
    setSort('newest'); setMinRating(''); setBidsOnly(false);
    load({ q: '', category: '', tech: '', minPrice: '', maxPrice: '', sort: 'newest', minRating: '', bidsOnly: false });
  }

  return (
    <div>
      {!user && (
        <div className="hero">
          <h2>Buy & sell student projects</h2>
          <p className="muted">Browse freely — login to bid, buy, or sell your own work.</p>
          <div className="row">
            <Link to="/login" className="btn">Login</Link>
            <Link to="/signup" className="btn secondary">Sign up free</Link>
          </div>
        </div>
      )}
      {user?.role === 'seller' && (
        <div className="hero seller">
          <h2>Your shop is open 🏪</h2>
          <p className="muted">List a new project or check incoming orders.</p>
          <div className="row">
            <Link to="/new" className="btn">+ Sell a project</Link>
            <Link to="/dashboard" className="btn secondary">My Shop</Link>
          </div>
        </div>
      )}
      {user?.role === 'buyer' && (
        <div className="hero buyer">
          <h2>Find your next project 🛒</h2>
          <p className="muted">Bid on open listings or buy instantly — track it all in My Orders.</p>
          <div className="row">
            <Link to="/dashboard" className="btn">My Orders</Link>
            <Link to="/sellers" className="btn secondary">Top sellers</Link>
          </div>
        </div>
      )}
      {!!featured.length && (
        <><h2>Featured</h2><div className="grid">
          {featured.map(l => (
            <Link key={l.id} to={`/l/${l.id}`} className="card feat">
              {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
              <h3>⭐ {l.title}</h3>
              <p className="muted">{l.category} · ★{l.rating} · ${l.price}</p>
            </Link>
          ))}
        </div></>
      )}
      <h2>Browse projects ({total})</h2>
      {!!picks.length && (
        <><h3>Picks for you</h3><div className="grid">
          {picks.map(l => (
            <Link key={l.id} to={`/l/${l.id}`} className="card feat">
              {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
              <h3>✨ {l.title}</h3>
              <p className="muted">{l.category} · ${l.price}</p>
            </Link>
          ))}
        </div></>
      )}
      <div className="filters">
        <input placeholder="Search title/description..." value={q} onChange={e => setQ(e.target.value)} />
        <select value={category} onChange={e => auto({ category: e.target.value })}>
          <option value="">All categories</option>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input placeholder="Tech (e.g. react)" list="taglist" value={tech} onChange={e => setTech(e.target.value)} onBlur={e => load({ tech: e.target.value })} />
        <datalist id="taglist">{tags.map(t => <option key={t} value={t} />)}</datalist>
        <input type="number" min={0} placeholder="Min $" value={minPrice} onChange={e => setMinPrice(e.target.value)} />
        <input type="number" min={0} placeholder="Max $" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} />
        <select value={sort} onChange={e => auto({ sort: e.target.value })}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price low-high</option>
          <option value="price_desc">Price high-low</option>
          <option value="popular">Most viewed</option>
          <option value="rating">Top rated</option>
        </select>
        <select value={minRating} onChange={e => auto({ minRating: e.target.value })}>
          <option value="">Any seller rating</option>
          <option value="4">Seller 4★+</option>
          <option value="3">Seller 3★+</option>
        </select>
        <label><input type="checkbox" checked={bidsOnly} onChange={e => auto({ bidsOnly: e.target.checked })} /> open to bids</label>
        <button onClick={() => load()}>Search</button>
        <button className="btn secondary" onClick={clear}>Clear</button>
      </div>
      {loading && <p className="muted">Loading…</p>}
      {error && <p className="error">{error} <button onClick={() => load()}>Retry</button></p>}
      {!loading && !error && items.length === 0 && <p className="muted">No projects match — try clearing filters.</p>}
      <div className="grid">
        {items.map(l => (
          <Link key={l.id} to={`/l/${l.id}`} className="card">
            {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
            <h3>{l.title}</h3>
            <p className="muted">{l.category} · {l.tech_stack?.join(', ')}</p>
            <strong>${l.price}</strong>
            <span className="muted"> · 👁 {l.views} · ★{l.seller_rating || l.rating || 0}</span>
          </Link>
        ))}
      </div>
      {!!trending.length && (
        <><h3>Trending this week</h3><p className="muted">{trending.slice(0, 5).map(t => t.title).join(' · ')}</p></>
      )}
    </div>
  );
}
```

## File: `frontend/src/pages/Dashboard.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

export function Dashboard() {
  const { user } = useAuth();
  const [listings, setListings] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [sales, setSales] = useState([]);
  const [bids, setBids] = useState([]);
  const [incoming, setIncoming] = useState([]);
  const [payouts, setPayouts] = useState({ items: [], total: 0 });
  const [profile, setProfile] = useState(null);
  const [connected, setConnected] = useState(null);

  const role = user?.role || 'buyer';
  const canBuy = role === 'buyer' || role === 'both';
  const canSell = role === 'seller' || role === 'both' || role === 'admin';

  async function load() {
    try { setListings(await api('/listings/mine')); } catch {}
    try { setPurchases(await api('/orders/purchases')); } catch {}
    try { setSales(await api('/orders/sales')); } catch {}
    try { setBids(await api('/bids/mine')); } catch {}
    try { setIncoming(await api('/bids/incoming')); } catch {}
    try { setPayouts(await api('/payments/payouts')); } catch {}
    try { setConnected(await api('/payments/connect-status')); } catch {}
    if (user) {
      try { setProfile(await api(`/users/${user.id}`)); } catch {}
    }
  }
  useEffect(() => { if (user) load(); }, [user]);
  if (!user) return <p>Login required.</p>;

  async function deliver(id) {
    const o = await api(`/orders/${id}/deliver`, { method: 'POST' });
    alert(`Delivered. Buyer token: ${o.download_token}`);
    load();
  }
  async function confirm(id) {
    const o = await api(`/orders/${id}/confirm`, { method: 'POST' });
    alert(`Completed. Seller payout: $${o.payout_to_seller}`);
    load();
  }
  async function download(order) {
    const token = prompt('Download token (from seller delivery):', order.download_token || '');
    if (token === null) return;
    try {
      const access = localStorage.getItem('access_token');
      const res = await fetch(`${API_BASE}/orders/${order.id}/download?token=${encodeURIComponent(token)}`, {
        headers: access ? { Authorization: `Bearer ${access}` } : {},
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try { msg = (await res.json()).detail || msg; } catch {}
        throw new Error(msg);
      }
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        const j = await res.json();
        const url = j.file_url.startsWith('/') ? `${API_BASE}${j.file_url}` : j.file_url;
        window.open(url, '_blank');
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `project-${order.id.slice(0, 8)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) { alert(e.message); }
  }

  const spent = purchases.filter(o => o.status !== 'refunded').reduce((a, o) => a + o.amount, 0);
  const activeBids = bids.filter(b => b.status === 'pending' || b.status === 'countered').length;
  const escrow = sales.filter(o => o.status === 'paid' || o.status === 'delivered')
                      .reduce((a, o) => a + (o.amount - (o.fee || 0)), 0);
  const needShip = sales.filter(o => o.status === 'paid').length;

  return (
    <div>
      <div className="dash-head">
        <div>
          <h2>{role === 'seller' ? 'Seller Studio' : role === 'buyer' ? 'My Orders' : 'Dashboard'}</h2>
          <p className="muted">Hey {user.name} <span className={`role-pill ${role}`}>{role}</span></p>
        </div>
        {canSell && <Link to="/new" className="btn">+ New listing</Link>}
      </div>

      <div className="stat-row">
        {canBuy && <><div><strong>${spent.toFixed(0)}</strong><span>spent</span></div>
        <div><strong>{purchases.length}</strong><span>orders</span></div>
        <div><strong>{activeBids}</strong><span>active bids</span></div></>}
        {canSell && <><div><strong>${payouts.total.toFixed(2)}</strong><span>earned</span></div>
        <div><strong>${escrow.toFixed(2)}</strong><span>in escrow</span></div>
        <div><strong>{sales.length}</strong><span>sales</span></div>
        <div><strong>{listings.filter(l => l.status === 'active').length}</strong><span>live listings</span></div>
        <div><strong>★{profile?.rating ?? 0}</strong><span>seller rating</span></div></>}
      </div>

      {canSell && connected && !connected.connected && (
        <p className="error">Payouts not connected — <button onClick={async () => {
          const r = await api('/payments/connect-onboard', { method: 'POST' });
          alert(`Connect: ${JSON.stringify(r)}`); load();
        }}>Connect Stripe payouts</button></p>
      )}
      {canSell && needShip > 0 && (
        <p className="error">📦 {needShip} order{needShip > 1 ? 's' : ''} paid — deliver files to unlock payouts.</p>
      )}

      {canBuy && (
        <div className="section">
          <h3>🛒 Buying</h3>
          <h4>My Purchases ({purchases.length})</h4>
          {purchases.length === 0 && <p className="muted">Nothing bought yet — <Link to="/">browse projects</Link>.</p>}
          {purchases.map(o => (
            <div key={o.id} className="row-card">
              <span><Link to={`/l/${o.listing_id}`}>{o.listing_title || o.listing_id.slice(0, 8)}</Link> · ${o.amount} · {o.status}</span>
              <span>
                {o.status === 'delivered' && <button onClick={() => download(o)}>Download</button>}
                {o.status === 'delivered' && <button onClick={() => confirm(o.id)}>Confirm receipt</button>}
                {o.status === 'pending' && <button onClick={async () => { await api(`/orders/${o.id}/mock-pay`, { method: 'POST' }); load(); }}>Pay (mock)</button>}
                {o.status === 'completed' && <Link to={`/l/${o.listing_id}`}>Review</Link>}
              </span>
            </div>
          ))}
          <h4>My Bids ({bids.length})</h4>
          {bids.length === 0 && <p className="muted">No offers placed — bid on any listing with “Accept offers”.</p>}
          {bids.map(b => (
            <div key={b.id} className="row-card">
              <Link to={`/l/${b.listing_id}`}>{b.listing_id.slice(0, 8)}</Link>
              <span>${b.amount} · {b.status}{b.counter ? ` (counter $${b.counter})` : ''}</span>
            </div>
          ))}
        </div>
      )}

      {canSell && (
        <div className="section">
          <h3>🏪 Selling</h3>
          <h4>My Listings ({listings.length})</h4>
          {listings.length === 0 && <p className="muted">No listings yet — <Link to="/new">publish your first project</Link>.</p>}
          {listings.map(l => (
            <div key={l.id} className="row-card">
              <Link to={`/l/${l.id}`}>{l.title}</Link>
              <span>${l.price} · {l.status} · 👁 {l.views} <Link to={`/edit/${l.id}`}>Edit</Link>
                {l.status !== 'removed' && <button onClick={async () => {
                  if (!window.confirm(`Delete "${l.title}"? It will be hidden from the marketplace.`)) return;
                  try { await api(`/listings/${l.id}`, { method: 'DELETE' }); load(); }
                  catch (e) { alert(e.message); }
                }}>Delete</button>}
              </span>
            </div>
          ))}
          <h4>Incoming Offers ({incoming.length})</h4>
          {incoming.length === 0 && <p className="muted">No pending offers. Buyers can bid on listings with “Accept offers” on.</p>}
          {incoming.map(b => (
            <div key={b.id} className="row-card">
              <Link to={`/l/${b.listing_id}`}>{b.listing_title || b.listing_id.slice(0, 8)}</Link>
              <span>
                ${b.amount} · {b.status}
                <button onClick={async () => { await api(`/bids/${b.id}/accept`, { method: 'POST' }); load(); }}>Accept</button>
                <button onClick={async () => { await api(`/bids/${b.id}/reject`, { method: 'POST' }); load(); }}>Reject</button>
              </span>
            </div>
          ))}
          <h4>Incoming Orders ({sales.length})</h4>
          {sales.map(o => (
            <div key={o.id} className="row-card">
              <span><Link to={`/l/${o.listing_id}`}>{o.listing_title || o.listing_id.slice(0, 8)}</Link> · ${o.amount} · {o.status}</span>
              <span>
                {o.status === 'paid' && <button onClick={() => deliver(o.id)}>Deliver files</button>}
                {(o.status === 'paid' || o.status === 'delivered') && <button onClick={async () => { await api(`/orders/${o.id}/dispute`, { method: 'POST' }); load(); }}>Dispute</button>}
              </span>
            </div>
          ))}
          <h4>Payouts (total ${payouts.total})</h4>
          {payouts.items.map((p, i) => <p key={i} className="muted">Order {p.order_id.slice(0, 8)}: ${p.amount} (fee ${p.fee})</p>)}
          <button onClick={async () => { const t = await api('/payments/tax-doc'); alert(JSON.stringify(t)); }}>Tax document</button>
        </div>
      )}
    </div>
  );
}
```

## File: `frontend/src/pages/EditListing.jsx`

```jsx
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';

export function EditListing() {
  const { id } = useParams();
  const nav = useNavigate();
  const [form, setForm] = useState(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api(`/listings/${id}`).then(l => setForm({
      title: l.title, description: l.description, price: l.price, category: l.category,
      tech_stack: (l.tech_stack || []).join(','), demo_video: l.demo_video || '',
      license: l.license || 'personal', accept_offers: l.accept_offers !== false,
      status: l.status,
    })).catch(e => setMsg(e.message));
  }, [id]);

  async function save() {
    try {
      await api(`/listings/${id}`, { method: 'PATCH', body: JSON.stringify({
        ...form, price: Number(form.price),
        tech_stack: form.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
      }) });
      nav(`/l/${id}`);
    } catch (e) { setMsg(e.message); }
  }

  if (!form) return <p>{msg || 'Loading...'}</p>;
  return (
    <div className="form wide">
      <h2>Edit listing</h2>
      {msg && <p className="error">{msg}</p>}
      <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
      <textarea rows={5} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
      <div className="row">
        <input type="number" min={1} value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="sold">Sold</option>
          <option value="removed">Removed</option>
        </select>
        <select value={form.license} onChange={e => setForm({ ...form, license: e.target.value })}>
          <option value="personal">personal use</option>
          <option value="resale">resale allowed</option>
          <option value="exclusive">exclusive</option>
        </select>
      </div>
      <input placeholder="Tech stack (comma separated)" value={form.tech_stack} onChange={e => setForm({ ...form, tech_stack: e.target.value })} />
      <input placeholder="Demo video URL" value={form.demo_video} onChange={e => setForm({ ...form, demo_video: e.target.value })} />
      <label><input type="checkbox" checked={form.accept_offers} onChange={e => setForm({ ...form, accept_offers: e.target.checked })} /> Accept offers</label>
      <div className="row">
        <button className="btn" onClick={save}>Save changes</button>
        <button onClick={async () => {
          if (!window.confirm(`Delete "${form.title}"? It will be hidden from the marketplace.`)) return;
          try { await api(`/listings/${id}`, { method: 'DELETE' }); nav('/dashboard'); }
          catch (e) { setMsg(e.message); }
        }}>Delete project</button>
      </div>
    </div>
  );
}
```

## File: `frontend/src/pages/ListingDetail.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';
import { Bids } from './Bids';
import { Reviews } from './Reviews';

function img(u) {
  if (!u) return '';
  return u.startsWith('/') ? `${API_BASE}${u}` : u;
}

export function ListingDetail() {
  const { id } = useParams();
  const [l, setL] = useState(null);
  const [related, setRelated] = useState([]);
  const [err, setErr] = useState('');
  const [myOrder, setMyOrder] = useState(null);
  const [pastOrder, setPastOrder] = useState(null);
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    api(`/listings/${id}`).then(setL).catch(e => setErr(String(e.message)));
    api(`/listings/${id}/related`).then(setRelated).catch(() => {});
    if (user) {
      // any prior order of mine for this listing → Purchased badge + review when completed
      api('/orders/purchases').then(os => {
        const mine = os.filter(o => o.listing_id === id).sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
        if (mine.length) setPastOrder(mine.find(o => o.status === 'completed') || mine[0]);
      }).catch(() => {});
    }
  }, [id, user]);

  async function buy() {
    if (!user) return nav('/login');
    if (!window.confirm(`Buy "${l.title}" for $${l.price}?`)) return;
    try {
      const order = await api('/orders', { method: 'POST', body: JSON.stringify({ listing_id: id }) });
      setMyOrder(order);
      // Mock mode: simulate payment immediately. Live mode: confirm with Stripe.js using client_secret.
      if (order.stripe_mode === 'mock') {
        await api(`/orders/${order.id}/mock-pay`, { method: 'POST' });
        alert('Payment successful (mock). See Dashboard > Purchases.');
        nav('/dashboard');
      } else {
        alert(`Stripe client_secret: ${order.client_secret}\nWire Stripe.js confirmCardPayment here.`);
      }
    } catch (e) { alert(e.message); }
  }

  async function ask() {
    if (!user) return nav('/login');
    const t = await api('/threads', { method: 'POST', body: JSON.stringify({ listing_id: id }) });
    nav(`/messages?thread=${t.id}`);
  }

  if (err) return <p className="error">{err}</p>;
  if (!l) return <p>Loading...</p>;
  return (
    <div>
      <h2>{l.title} {l.featured ? '⭐' : ''} {pastOrder ? <small className="badge">✓ purchased ({pastOrder.status})</small> : null} {l.flagged_duplicate ? <small className="error">(flagged: possible duplicate)</small> : null}</h2>
      <p className="muted">{l.category} · {l.tech_stack?.join(', ')} · 👁 {l.views} · seller ★{l.seller_rating || 0} ({l.seller_rating_count || 0}) · {l.status} · license: {l.license}</p>
      <div className="imgs">{l.images?.map((u, i) => <img key={i} src={img(u)} alt="" />)}</div>
      {l.demo_video && /^https?:\/\//.test(l.demo_video) && <p><a href={l.demo_video} target="_blank" rel="noreferrer">▶ Demo video</a></p>}
      <p>{l.description}</p>
      {!!l.pricing_tiers?.length && (
        <div>{l.pricing_tiers.map((t, i) => <p key={i} className="muted">{t.name}: ${t.price} — {t.description}</p>)}</div>
      )}
      {!!l.specs && Object.keys(l.specs).length > 0 && (
        <div className="specs">{Object.entries(l.specs).map(([k, v]) => <span key={k} className="spec">{k}: <strong>{v}</strong></span>)}</div>
      )}
      <h3>${l.price}</h3>
      {l.seller && <p>Seller: <Link to={`/u/${l.seller_id}`}>{l.seller.name}</Link></p>}
      <div className="row">
        {user && user.id === l.seller_id && <button className="btn" onClick={() => nav(`/edit/${id}`)}>Edit listing</button>}
        {(!user || user.id !== l.seller_id) && <button className="btn" onClick={buy}>Buy Now</button>}
        {(!user || user.id !== l.seller_id) && <button onClick={ask}>Ask a question</button>}
        <button onClick={async () => { const r = prompt('Reason (stolen/plagiarized?)'); if (r) { await api(`/listings/${id}/report`, { method: 'POST', body: JSON.stringify({ reason: r }) }); alert('Reported'); } }}>Report</button>
      </div>
      <Bids listingId={id} sellerId={l.seller_id} />
      <Reviews listingId={id} orderId={myOrder?.id || (pastOrder?.status === 'completed' ? pastOrder.id : null)} canReview={!!myOrder || pastOrder?.status === 'completed'} />
      {!!related.length && (
        <><h3>Related</h3><div className="grid">{related.map(r => (
          <Link key={r.id} to={`/l/${r.id}`} className="card"><h4>{r.title}</h4><p className="muted">${r.price}</p></Link>
        ))}</div></>
      )}
    </div>
  );
}
```

## File: `frontend/src/pages/Messages.jsx`

```jsx
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Messages() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const [threads, setThreads] = useState([]);
  const [unread, setUnread] = useState(0);
  const [active, setActive] = useState(() => params.get('thread'));
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState('');

  async function loadThreads() {
    const d = await api('/threads');
    setThreads(d.threads); setUnread(d.unread_total);
    const want = params.get('thread');
    if (want && d.threads.some(t => t.id === want)) { setActive(want); return; }
    if (!active && d.threads[0]) setActive(d.threads[0].id);
  }
  async function loadMsgs() {
    if (!active) return;
    setMsgs(await api(`/threads/${active}/messages`));
  }
  useEffect(() => { if (user) { loadThreads(); const t = setInterval(loadThreads, 8000); return () => clearInterval(t); } }, [user]);
  useEffect(() => { loadMsgs(); const t = setInterval(loadMsgs, 4000); return () => clearInterval(t); }, [active]);

  async function send() {
    await api(`/threads/${active}/messages`, { method: 'POST', body: JSON.stringify({ text }) });
    setText(''); loadMsgs();
  }
  if (!user) return <p>Login required.</p>;
  return (
    <div>
      <h2>Messages {unread ? `(${unread} unread)` : ''}</h2>
      <div className="msgs">
        <div className="thread-list">
          {threads.map(t => (
            <button key={t.id} className={t.id === active ? 'active' : ''} onClick={() => setActive(t.id)}>
              {(t.unread_buyer + t.unread_seller) > 0 ? '● ' : ''}{t.listing_id.slice(0, 8) || t.order_id.slice(0, 8)}
            </button>
          ))}
        </div>
        <div className="chat">
          {msgs.map((m, i) => <p key={i}><strong>{m.from === user.id ? 'You' : 'Them'}:</strong> {m.text}</p>)}
          {active && (
            <div className="row">
              <input placeholder="Message..." value={text} onChange={e => setText(e.target.value)} />
              <button onClick={send}>Send</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## File: `frontend/src/pages/NewListing.jsx`

```jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

export function NewListing() {
  const [cats, setCats] = useState([]);
  const [form, setForm] = useState({ title: '', description: '', price: 49, category: 'Web App', tech_stack: '', status: 'active', demo_video: '', license: 'personal', accept_offers: true, tiers: '', specs: '' });
  const [images, setImages] = useState([]);
  const [fileKey, setFileKey] = useState('');
  const [fileHash, setFileHash] = useState('');
  const [err, setErr] = useState('');
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => { api('/listings/categories').then(d => setCats(d.categories)).catch(() => {}); }, []);

  async function uploadPreview(e) {
    const f = e.target.files[0];
    if (!f) return;
    setErr('');
    try {
      const fd = new FormData();
      fd.append('file', f);
      const r = await api('/uploads/preview', { method: 'POST', body: fd });
      setImages([...images, r.url]);
    } catch (ex) { setErr(ex.message); }
  }

  async function uploadZip(e) {
    const f = e.target.files[0];
    if (!f) return;
    setErr('');
    try {
      const fd = new FormData();
      fd.append('file', f);
      const r = await api('/uploads/project-file', { method: 'POST', body: fd });
      setFileKey(r.key);
      setFileHash(r.file_hash || '');
      if (r.duplicate_warning) alert('Warning: identical file already exists (possible duplicate)');
    } catch (ex) { setErr(ex.message); }
  }

  async function submit() {
    setErr('');
    if (!user) { setErr('Login required.'); return; }
    if (user.role === 'buyer') { setErr('A seller account is required to publish. Change role in Profile.'); return; }
    if ((form.title || '').length < 3 || (form.description || '').length < 10) {
      setErr('Title (3+) and description (10+) are too short.');
      return;
    }
    const tiers = form.tiers.split(';').map(s => s.trim()).filter(Boolean).map(s => {
      const [name, price] = s.split(':');
      return { name: (name || '').trim(), price: Number(price || 0), description: '' };
    }).filter(t => t.name && t.price > 0);
    const specs = {};
    form.specs.split(';').map(s => s.trim()).filter(Boolean).forEach(s => {
      const i = s.indexOf(':');
      if (i > 0) specs[s.slice(0, i).trim()] = s.slice(i + 1).trim();
    });
    const body = {
      ...form,
      price: Number(form.price),
      tech_stack: form.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
      images,
      project_file: fileKey,
      file_hash: fileHash,
      pricing_tiers: tiers,
      specs,
    };
    delete body.tiers;
    try {
      const l = await api('/listings', { method: 'POST', body: JSON.stringify(body) });
      if (l.duplicate_warning) alert('Duplicate file detected — listing flagged for review');
      nav(`/l/${l.id}`);
    } catch (e) { setErr(e.message); }
  }

  const img = (u) => (u.startsWith('/') ? `${API_BASE}${u}` : u);

  return (
    <div className="form wide">
      <h2>Sell a project</h2>
      {user?.role === 'buyer' && <p className="error">Buyer accounts can't publish. Switch role to seller in Profile.</p>}
      {err && <p className="error">{err}</p>}
      <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
      <textarea placeholder="Description (min 10 chars)" rows={5} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
      <div className="row">
        <input type="number" min={1} value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} />
        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <input placeholder="Tech stack (comma separated: react, python)" value={form.tech_stack} onChange={e => setForm({ ...form, tech_stack: e.target.value })} />
      <input placeholder="Demo video URL (YouTube/Loom)" value={form.demo_video} onChange={e => setForm({ ...form, demo_video: e.target.value })} />
      <div className="row">
        <select value={form.license} onChange={e => setForm({ ...form, license: e.target.value })}>
          <option value="personal">License: personal use</option>
          <option value="resale">License: resale allowed</option>
          <option value="exclusive">License: exclusive one-time sale</option>
        </select>
        <label><input type="checkbox" checked={form.accept_offers} onChange={e => setForm({ ...form, accept_offers: e.target.checked })} /> Accept offers</label>
      </div>
      <input placeholder="Pricing tiers (name:price; ...) e.g. code only:29; code+docs:49" value={form.tiers} onChange={e => setForm({ ...form, tiers: e.target.value })} />
      <input placeholder="Category specs (key:value; ...) e.g. dataset size:10k rows; accuracy:94%" value={form.specs} onChange={e => setForm({ ...form, specs: e.target.value })} />
      <label>Screenshots: <input type="file" accept="image/*" onChange={uploadPreview} /></label>
      <div className="imgs">{images.map((u, i) => <img key={i} src={img(u)} alt="" />)}</div>
      <label>Project .zip (locked until purchase): <input type="file" accept=".zip" onChange={uploadZip} /></label>
      {fileKey && <p className="muted">Attached: {fileKey}</p>}
      <button className="btn" onClick={submit}>Publish listing</button>
    </div>
  );
}
```

## File: `frontend/src/pages/Notifications.jsx`

```jsx
import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Notifications() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [prefs, setPrefs] = useState({});
  async function load() {
    const n = await api('/notifications');
    setItems(n.items);
    const p = await api('/notifications/prefs');
    setPrefs(p.opt_out || {});
  }
  useEffect(() => { if (user) load(); }, [user]);
  if (!user) return <p>Login required.</p>;
  return (
    <div>
      <h2>Notifications</h2>
      <button onClick={async () => { await api('/notifications/read-all', { method: 'POST' }); load(); }}>Mark all read</button>
      {items.map(n => (
        <div key={n.id} className="row-card">
          <span>{n.read ? '' : '● '}[{n.kind}] {n.title}</span>
          {!n.read && <button onClick={async () => { await api(`/notifications/${n.id}/read`, { method: 'POST' }); load(); }}>Read</button>}
        </div>
      ))}
      <h3>Preferences</h3>
      {['bid', 'order', 'message', 'review', 'system'].map(k => (
        <label key={k}><input type="checkbox" checked={!prefs[k]} onChange={async () => {
          const next = { ...prefs, [k]: !prefs[k] ? true : false };
          if (next[k] === false) delete next[k];
          await api('/notifications/prefs', { method: 'POST', body: JSON.stringify({ opt_out: next }) });
          load();
        }} /> {k} </label>
      ))}
    </div>
  );
}
```

## File: `frontend/src/pages/Password.jsx`

```jsx
import { useState } from 'react';
import { api } from '../api';

export function Forgot() {
  const [email, setEmail] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Forgot password</h2>
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <button className="btn" onClick={async () => {
        const r = await api('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
        setMsg(`Reset token (dev): ${r.reset_token_dev} — use /reset page`);
      }}>Send reset link</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}

export function Reset() {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Reset password</h2>
      <input placeholder="Token" value={token} onChange={e => setToken(e.target.value)} />
      <input placeholder="New password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await api('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, password }) }); setMsg('Done — login now.'); }
        catch (e) { setMsg(e.message); }
      }}>Reset</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}

export function VerifyEmail() {
  const [token, setToken] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Verify email</h2>
      <input placeholder="Token from signup response / email" value={token} onChange={e => setToken(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await api('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) }); setMsg('Verified!'); }
        catch (e) { setMsg(e.message); }
      }}>Verify</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}
```

## File: `frontend/src/pages/Reviews.jsx`

```jsx
import { useEffect, useState } from 'react';
import { api } from '../api';

export function Reviews({ listingId, orderId, canReview }) {
  const [items, setItems] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');

  async function load() {
    try { setItems(await api(`/listings/${listingId}/reviews`)); } catch {}
  }
  useEffect(() => { load(); }, [listingId]);

  async function submit() {
    await api(`/orders/${orderId}/reviews`, { method: 'POST', body: JSON.stringify({ rating: Number(rating), comment }) });
    setComment(''); load();
  }

  return (
    <div className="section">
      <h3>Reviews ({items.length})</h3>
      {items.map(r => (
        <div key={r.id} className="row-card">
          <span>{'★'.repeat(r.rating)} — {r.comment}{r.response ? <><br /><em>Seller: {r.response}</em></> : null}</span>
        </div>
      ))}
      {canReview && orderId && (
        <div className="row">
          <select value={rating} onChange={e => setRating(e.target.value)}>{[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} stars</option>)}</select>
          <input placeholder="Comment" value={comment} onChange={e => setComment(e.target.value)} />
          <button onClick={submit}>Leave review</button>
        </div>
      )}
    </div>
  );
}
```

## File: `frontend/src/pages/SellerProfile.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

const img = (u) => (u && u.startsWith('/') ? `${API_BASE}${u}` : u);

function ProjectCard({ p, sold }) {
  return (
    <Link to={`/l/${p.id}`} className="card">
      {p.images?.[0] && <img src={img(p.images[0])} alt="" loading="lazy" />}
      <h4>{p.title}</h4>
      <p className="muted">{p.category}</p>
      <strong>${p.price}</strong>
      <span className={sold ? 'sold-tag' : 'muted'}>{sold ? ` · SOLD${p.sold_at ? ` · ${p.sold_at.slice(0, 10)}` : ''}` : ` · 👁 ${p.views ?? 0} · ★${p.rating ?? 0}`}</span>
    </Link>
  );
}

export function SellerProfile() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [following, setFollowing] = useState(false);
  const { user } = useAuth();

  useEffect(() => { api(`/users/${id}`).then(setP).catch(() => {}); }, [id]);
  if (!p) return <p>Loading...</p>;

  return (
    <div className="seller-page">
      <div className="seller-hero">
        {p.avatar
          ? <img src={p.avatar} alt="" className="seller-avatar" />
          : <div className="seller-avatar fallback">{p.name[0]}</div>}
        <div>
          <h2>{p.name} <span className={`role-pill ${p.role}`}>{p.role}</span> {p.badges?.map(b => <small key={b} className="badge">✓{b}</small>)} {p.flagged_seller ? <small className="badge warn">flagged ({p.strikes} reports)</small> : null}</h2>
      <p className="muted">{p.bio}</p>
      {!!(p.interests || []).length && <p className="muted">Looking for: {(p.interests || []).join(', ')}</p>}
          <p className="muted">Skills: {(p.skills || []).join(', ') || '—'}
            {p.github ? <span> · <a href={`https://github.com/${p.github}`} target="_blank" rel="noreferrer">GitHub: {p.github}</a></span> : null}
          </p>
          {user && user.id !== id && (
            <button onClick={async () => {
              const r = await api(`/users/${id}/follow`, { method: 'POST' });
              setFollowing(r.following);
              setP({ ...p, followers: p.followers + (r.following ? 1 : -1) });
            }}>{following ? 'Unfollow' : 'Follow'}</button>
          )}
        </div>
      </div>

      <div className="stat-row">
        <div><strong>{p.ongoing_count ?? 0}</strong><span>ongoing</span></div>
        <div><strong>{p.sold_count ?? 0}</strong><span>sold</span></div>
        <div><strong>${p.total_earned ?? 0}</strong><span>earned</span></div>
        <div><strong>★{p.rating ?? 0}</strong><span>({p.rating_count ?? 0} reviews{ p.rating_weighted ? `, weighted ${p.rating_weighted}` : ''})</span></div>
        <div><strong>{p.followers ?? 0}</strong><span>followers</span></div>
      </div>

      {p.role === 'buyer' ? (
        <p className="muted">Buyer account — no shop. {user && user.id === id ? 'Switch your role to seller in Profile to start selling.' : ''}</p>
      ) : (<>
      <h3>Ongoing projects ({(p.ongoing_projects || []).length})</h3>
      {(p.ongoing_projects || []).length === 0 && <p className="muted">No ongoing projects right now.</p>}
      <div className="grid">
        {(p.ongoing_projects || []).map(l => <ProjectCard key={l.id} p={l} />)}
      </div>

      <h3>Sold ({(p.sold_projects || []).length})</h3>
      {(p.sold_projects || []).length === 0 && <p className="muted">Nothing sold yet.</p>}
      <div className="grid">
        {(p.sold_projects || []).map(l => <ProjectCard key={l.id} p={l} sold />)}
      </div>
      </>)}
    </div>
  );
}
```

## File: `frontend/src/pages/Sellers.jsx`

```jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export function Sellers() {
  const [sellers, setSellers] = useState([]);
  useEffect(() => { api('/users/sellers/top?limit=40').then(setSellers).catch(() => {}); }, []);
  return (
    <div>
      <h2>Sellers ({sellers.length})</h2>
      <div className="grid">
        {sellers.map(s => (
          <Link key={s.id} to={`/u/${s.id}`} className="card seller-card">
            <div className="seller-mini">
              {s.avatar ? <img src={s.avatar} alt="" className="mini-avatar" /> : <div className="mini-avatar fallback">{s.name[0]}</div>}
              <div>
                <h4>{s.name} {s.badges?.map(b => <small key={b}>✓{b}</small>)}</h4>
                <p className="muted">★{s.rating} ({s.rating_count}) · {s.followers} followers</p>
              </div>
            </div>
            <p className="muted">{s.ongoing_count} ongoing · {s.sold_count} sold</p>
            <p className="muted skills">{(s.skills || []).slice(0, 4).join(' · ')}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

## File: `frontend/src/styles.css`

```css
:root {
  --wine: #800020;
  --cream: #F3E6D5;
  --paper: #FFF9F2;
  --rose: #D45060;
  --ink: #402020;
  --ink-soft: #8a6f5c;
  --card: #ffffff;
  --radius: 14px;
  --shadow-sm: 0 1px 3px rgba(128, 0, 32, 0.08);
  --shadow-md: 0 4px 14px rgba(128, 0, 32, 0.12);
  --shadow-lg: 0 8px 28px rgba(128, 0, 32, 0.16);
}
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; margin: 0; background: var(--paper); color: var(--ink); line-height: 1.55; }
h2 { font-size: 1.5rem; margin: 0.4em 0 0.6em; color: var(--wine); letter-spacing: -0.01em; }
h3 { font-size: 1.15rem; margin: 1.4em 0 0.6em; color: var(--wine); }
h4 { margin: 0.4em 0; }

/* ---------- nav ---------- */
.nav { position: sticky; top: 0; z-index: 50; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 12px 22px; background: var(--wine); color: var(--cream); box-shadow: var(--shadow-md); }
.nav a { color: var(--cream); margin-right: 14px; text-decoration: none; font-weight: 600; opacity: 0.92; }
.nav a:hover { opacity: 1; text-decoration: underline; text-underline-offset: 3px; }
.nav .links { display: flex; align-items: center; flex-wrap: wrap; gap: 2px; }
.brand { font-weight: 800; font-size: 1.3rem; letter-spacing: -0.01em; }
.nav button { background: rgba(255, 255, 255, 0.14); color: var(--cream); border: 1px solid rgba(255, 255, 255, 0.35); }

/* ---------- layout ---------- */
.container { max-width: 1024px; margin: 0 auto; padding: 24px 20px 60px; }
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.section { margin-top: 28px; padding-top: 14px; border-top: 2px solid var(--rose); }

/* ---------- buttons / inputs ---------- */
.btn, button { background: var(--wine); color: var(--cream); font-weight: 600; font-size: 0.95rem; padding: 9px 16px; border-radius: 10px; border: 0; cursor: pointer; text-decoration: none; display: inline-block; transition: transform 0.08s ease, box-shadow 0.15s ease, background 0.15s ease; box-shadow: var(--shadow-sm); }
button:hover, .btn:hover { background: var(--rose); box-shadow: var(--shadow-md); transform: translateY(-1px); }
button:active, .btn:active { transform: translateY(0); box-shadow: var(--shadow-sm); }
button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
button:focus-visible, .btn:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 3px solid var(--rose); outline-offset: 2px; }
.btn.secondary { background: var(--card); color: var(--wine); border: 1.5px solid var(--wine); box-shadow: none; }
.btn.secondary:hover { background: var(--cream); }
input, select, textarea { padding: 10px 12px; border-radius: 10px; border: 1.5px solid var(--cream); background: #fff; color: var(--ink); font-size: 0.95rem; transition: border-color 0.15s ease, box-shadow 0.15s ease; }
input:focus, select:focus, textarea:focus { border-color: var(--rose); box-shadow: 0 0 0 3px rgba(212, 80, 96, 0.15); outline: none; }
label { font-size: 0.9rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }

/* ---------- forms ---------- */
.form { display: flex; flex-direction: column; gap: 12px; max-width: 460px; background: var(--card); border: 1px solid var(--cream); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow-md); margin-top: 12px; }
.form.wide { max-width: 680px; }
.form h2 { margin-top: 0; }

/* ---------- filters / hero ---------- */
.filters { display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; align-items: center; background: var(--card); border: 1px solid var(--cream); border-radius: var(--radius); padding: 14px; box-shadow: var(--shadow-sm); }
.hero { background: linear-gradient(135deg, var(--wine) 0%, var(--rose) 100%); color: var(--cream); border-radius: 18px; padding: 28px 24px; margin-bottom: 20px; box-shadow: var(--shadow-lg); }
.hero h2 { color: var(--cream); margin-top: 0; font-size: 1.7rem; }
.hero .muted { color: var(--cream); opacity: 0.85; }
.hero .btn { background: var(--cream); color: var(--wine); }
.hero .btn:hover { background: #fff; }
.hero .btn.secondary { background: transparent; color: var(--cream); border: 1.5px solid var(--cream); }
.hero .btn.secondary:hover { background: rgba(255, 255, 255, 0.15); }

/* ---------- cards / grids ---------- */
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 16px; }
.card { background: var(--card); border-radius: var(--radius); padding: 14px; text-decoration: none; color: inherit; border: 1px solid var(--cream); box-shadow: var(--shadow-sm); transition: transform 0.12s ease, box-shadow 0.15s ease; overflow: hidden; }
a.card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.card h3, .card h4 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 10px; margin: 0 0 8px; }
.imgs { display: flex; flex-wrap: wrap; gap: 8px; }
.imgs img { max-width: 280px; border-radius: 10px; }
.card.feat { border: 2px solid var(--wine); }
.muted { color: var(--ink-soft); font-size: 0.83rem; }
.error { color: #b00020; background: #fdecea; border-radius: 8px; padding: 8px 12px; }
.row-card { background: var(--card); border: 1px solid var(--cream); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; box-shadow: var(--shadow-sm); }

/* ---------- messaging ---------- */
.msgs { display: flex; gap: 14px; align-items: flex-start; }
.thread-list { display: flex; flex-direction: column; gap: 8px; min-width: 160px; }
.thread-list button { background: var(--card); border: 1px solid var(--cream); color: var(--ink); text-align: left; }
.thread-list button.active { background: var(--wine); color: var(--cream); border-color: var(--wine); }
.chat { flex: 1; background: var(--card); border: 1px solid var(--cream); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow-sm); min-height: 200px; }

/* ---------- seller pages ---------- */
.seller-hero { display: flex; gap: 18px; align-items: flex-start; background: var(--card); border: 1px solid var(--cream); border-radius: 18px; padding: 20px; box-shadow: var(--shadow-md); }
.seller-avatar { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; border: 3px solid var(--cream); flex-shrink: 0; }
.seller-avatar.fallback { display: flex; align-items: center; justify-content: center; font-size: 2.5rem; background: var(--cream); color: var(--wine); }
.badge { background: var(--cream); color: var(--wine); border-radius: 999px; padding: 2px 10px; margin-left: 6px; font-size: 0.75rem; font-weight: 700; white-space: nowrap; }
.badge.warn { background: var(--rose); color: #fff; }
.stat-row { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
.stat-row div { background: var(--card); border: 1px solid var(--cream); border-radius: 12px; padding: 10px 18px; display: flex; flex-direction: column; align-items: center; box-shadow: var(--shadow-sm); min-width: 96px; }
.stat-row strong { font-size: 1.15rem; color: var(--wine); }
.stat-row span { font-size: 0.75rem; color: var(--ink-soft); }
.sold-tag { color: var(--wine); font-size: 0.83rem; font-weight: 700; }
.seller-mini { display: flex; gap: 10px; align-items: center; }
.mini-avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.mini-avatar.fallback { display: flex; align-items: center; justify-content: center; font-size: 1.4rem; background: var(--rose); color: var(--cream); flex-shrink: 0; }
.skills { font-size: 0.75rem; }
.specs { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.spec { background: var(--cream); border-radius: 999px; padding: 4px 12px; font-size: 0.83rem; }
a { color: var(--wine); }

/* ---------- responsive ---------- */
@media (max-width: 640px) {
  .container { padding: 16px 12px 48px; }
  .seller-hero { flex-direction: column; align-items: center; text-align: center; }
  .msgs { flex-direction: column; }
  .thread-list { flex-direction: row; flex-wrap: wrap; min-width: 0; }
  .grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .nav { padding: 10px 14px; }
}
@media (max-width: 420px) {
  .grid { grid-template-columns: 1fr; }
}
.role-pill { display: inline-block; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; border-radius: 999px; padding: 2px 10px; vertical-align: middle; }
.role-pill.buyer { background: var(--cream); color: var(--wine); }
.role-pill.seller { background: var(--wine); color: var(--cream); }
.role-pill.both { background: var(--rose); color: #fff; }
.role-pill.admin { background: var(--ink); color: #fff; }
.dash-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.dash-head h2 { margin-bottom: 0; }
.hero.seller { background: linear-gradient(135deg, var(--wine) 0%, #5c0016 100%); }
.hero.buyer { background: linear-gradient(135deg, var(--rose) 0%, var(--wine) 100%); }
```

## File: `frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 }
})
```

## File: `prompt.txt`

```text
https://github.com/vatsyashovardhan-sketch?tab=repositories
```

## File: `README.md`

````markdown
# Project Bidding Platform — Full build (MVP 🟢 + Phase 2 🟡 + Phase 3/4 🔴)

FARM stack (FastAPI + React + MongoDB). Covers everything in `prompt.txt`; external services run in mock/stub mode until keys are set.

## Run backend
```powershell
cd backend
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```
API: http://localhost:8000/docs · Health: http://localhost:8000/health · Tests: `python -m pytest -q`

MongoDB is used when reachable (`MONGO_URI`), else in-memory store.

## Seed demo data (20 buyers + 40 sellers)
```powershell
cd backend
# terminal 1: python -m uvicorn app.main:app --reload --port 8000
# terminal 2:
python seed.py --api http://localhost:8000
```
Each seller gets a storefront: avatar/bio/skills/GitHub, 2–4 ongoing projects + 1–3 sold projects with prices, plus simulated orders, reviews, bids and follows. All seeded logins use password `Seed1234`. Re-runs are idempotent (existing users/listings/bids/follows are skipped, not duplicated). To wipe seed data from Mongo: `mongosh --quiet cleanup_seed.js`. Browse sellers at `/sellers`, profiles at `/u/:id`.

## Run frontend
```powershell
cd frontend
npm install
npm run dev
```
App: http://localhost:5173.

## What's implemented
- Auth: signup/login/JWT+refresh/logout, password rules, rate-limit, email verify, forgot/reset, GitHub OAuth (mock→real), 2FA stub
- Users: roles, profiles (skills/GitHub/portfolio), follow, student/developer badges, public profiles with rating
- Listings: CRUD + draft/active/sold/removed, categories, tags, demo video, pricing tiers, license, accept-offers toggle, file-hash duplicate flag, full-text-ish search, rating/bids filters, sort (incl. popular/rating), featured/trending/related/tags, view counts, plagiarism report
- Orders/payments: Buy Now (Stripe live or mock), webhook, dashboards, deliver→token download, confirm→payout+commission record, disputes, refunds, payout history, tax-doc stub, Connect onboarding
- Bidding: place/view/accept/reject/counter, 48h expiry job, accept→order, analytics
- Messaging: threads (listing/order), polling + WebSocket realtime, unread badge, block/report
- Reviews: post-completion 1-5 + comment, avg on listing/seller, seller response, report
- Admin: stats/GMV, users ban, listings remove/feature, disputes resolve (refund/release), moderation queue, payout override, analytics
- Notifications: in-app + unread bell, email stub (Resend/SendGrid hook), per-kind prefs
- Jobs: POST /admin… no — POST /jobs/run (admin): expire bids, auto-complete 7d, auto-refund 7d
- Infra: .env, CORS, Pydantic, error shape, logging, rate-limit, pytest, GitHub Actions CI, Sentry hook (SENTRY_DSN), Redis hook (REDIS_URL), S3 presigned hook (USE_S3)

## Security notes
- Banned users are rejected at login and on every authenticated request
- Login rate-limited per IP (200/5min) + per email (15/5min); buckets memory-capped
- Passwords: 8–72 chars (bcrypt limit), letter + number
- Search input regex-escaped; uploads capped (5MB images, 50MB zips) with magic-byte checks
- Project zips are never publicly served — token-gated `FileResponse` only; demo-video URLs must be http(s)
- Public APIs never expose emails (contact via in-app chat); sold listings can't be relisted (double-sell guard)
- Set a real `JWT_SECRET` in `backend/.env` (startup warns on default); keep `.env` out of git
````
