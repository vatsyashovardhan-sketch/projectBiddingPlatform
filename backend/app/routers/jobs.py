# """Scheduled/expiry jobs: bid expiry (48h), auto-complete (7d), auto-refund (7d no delivery)."""
# from datetime import timedelta
# from fastapi import APIRouter, Depends

# from app.core.deps import get_current_user
# from app.core.notify import notify
# from app.core.security import new_id, utcnow
# from app.db import database as db

# router = APIRouter(tags=["jobs"])


# async def run_jobs() -> dict:
#     now = utcnow().isoformat()
#     expired = auto_completed = auto_refunded = 0
#     bids = await db.bids().find_many({"status": "pending"}, limit=2000)
#     for b in bids:
#         if b.get("expires_at") and b["expires_at"] < now:
#             await db.bids().update_one({"_id": b["_id"]}, {"$set": {"status": "expired"}})
#             expired += 1
#     orders = await db.orders().find_many({}, limit=5000)
#     week_ago = (utcnow() - timedelta(days=7)).isoformat()
#     for o in orders:
#         if o.get("status") == "delivered" and o.get("created_at", "") < week_ago:
#             payout = round(o["amount"] - o.get("fee", 0), 2)
#             await db.orders().update_one({"_id": o["_id"]}, {"$set": {"status": "completed"}})
#             await db.listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
#             await db.col("payouts").insert_one({
#                 "_id": new_id(), "order_id": o["_id"], "seller_id": o["seller_id"],
#                 "amount": payout, "fee": o.get("fee", 0), "created_at": now, "auto": True})
#             await notify(o["seller_id"], "order", f"Order {o['_id'][:8]} auto-completed — ${payout} payout", "/dashboard")
#             auto_completed += 1
#         elif o.get("status") == "paid" and o.get("created_at", "") < week_ago:
#             await db.orders().update_one({"_id": o["_id"]}, {"$set": {"status": "refunded"}})
#             auto_refunded += 1
#     return {"expired_bids": expired, "auto_completed": auto_completed, "auto_refunded": auto_refunded}


# @router.post("/jobs/run")
# async def run(user: dict = Depends(get_current_user)):
#     if user.get("role") != "admin":
#         # allow cron without auth in dev via header? keep admin-only for safety
#         from fastapi import HTTPException
#         raise HTTPException(403, "Admin only")
#     return await run_jobs()
