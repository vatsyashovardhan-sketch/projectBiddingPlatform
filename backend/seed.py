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
