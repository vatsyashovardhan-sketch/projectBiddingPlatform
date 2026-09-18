# """Bidding system (Phase 2)."""
# from datetime import timedelta
# from fastapi import APIRouter, Depends, HTTPException

# from app.core.deps import get_current_user
# from app.core.notify import notify, notify_email
# from app.core.security import new_id, utcnow
# from app.db import database as db

# router = APIRouter(tags=["bids"])
# BID_TTL_HOURS = 48


# def _out(b: dict) -> dict:
#     return {
#         "id": b["_id"], "listing_id": b["listing_id"], "buyer_id": b["buyer_id"],
#         "seller_id": b.get("seller_id", ""), "amount": b["amount"],
#         "message": b.get("message", ""), "status": b.get("status", "pending"),
#         "expires_at": b.get("expires_at"), "counter": b.get("counter"),
#         "created_at": b.get("created_at"),
#     }


# @router.post("/listings/{listing_id}/bids")
# async def place_bid(listing_id: str, body: dict, user: dict = Depends(get_current_user)):
#     lst = await db.listings().find_one({"_id": listing_id})
#     if not lst or lst.get("status") != "active":
#         raise HTTPException(404, "Listing not available")
#     if not lst.get("accept_offers", True):
#         raise HTTPException(400, "Seller is not accepting offers on this listing")
#     if lst["seller_id"] == user["id"]:
#         raise HTTPException(400, "Cannot bid on your own listing")
#     amount = float(body.get("amount", 0))
#     if amount <= 0:
#         raise HTTPException(400, "Invalid bid amount")
#     bid = {
#         "_id": new_id(), "listing_id": listing_id, "buyer_id": user["id"],
#         "seller_id": lst["seller_id"], "amount": amount,
#         "message": body.get("message", ""), "status": "pending",
#         "expires_at": (utcnow() + timedelta(hours=BID_TTL_HOURS)).isoformat(),
#         "created_at": utcnow().isoformat(),
#     }
#     await db.bids().insert_one(bid)
#     await notify(lst["seller_id"], "bid", f"New bid ${amount} on {lst['title']}", f"/l/{listing_id}")
#     return _out(bid)


# @router.get("/listings/{listing_id}/bids")
# async def list_bids(listing_id: str, user: dict = Depends(get_current_user)):
#     lst = await db.listings().find_one({"_id": listing_id})
#     if not lst:
#         raise HTTPException(404, "Listing not found")
#     if lst["seller_id"] != user["id"] and user.get("role") != "admin":
#         raise HTTPException(403, "Only seller can view bids")
#     items = await db.bids().find_many({"listing_id": listing_id}, limit=100, sort=[("amount", -1)])
#     return [_out(b) for b in items]


# @router.get("/bids/mine")
# async def my_bids(user: dict = Depends(get_current_user)):
#     items = await db.bids().find_many({"buyer_id": user["id"]}, limit=100, sort=[("created_at", -1)])
#     return [_out(b) for b in items]


# @router.get("/bids/incoming")
# async def incoming_bids(user: dict = Depends(get_current_user)):
#     """Seller inbox: pending/countered bids across all my listings, newest first."""
#     mine = await db.listings().find_many({"seller_id": user["id"]}, limit=500)
#     titles = {m["_id"]: m["title"] for m in mine}
#     items = await db.bids().find_many({"seller_id": user["id"]}, limit=200, sort=[("created_at", -1)])
#     return [{**_out(b), "listing_title": titles.get(b["listing_id"], "")}
#             for b in items if b.get("status") in ("pending", "countered")]


# async def _get_bid(bid_id: str, user: dict, seller_only: bool = True) -> dict:
#     b = await db.bids().find_one({"_id": bid_id})
#     if not b:
#         raise HTTPException(404, "Bid not found")
#     if seller_only and b["seller_id"] != user["id"] and user.get("role") != "admin":
#         raise HTTPException(403, "Only seller can do this")
#     if b.get("status") != "pending":
#         raise HTTPException(400, f"Bid already {b.get('status')}")
#     if b.get("expires_at") and b["expires_at"] < utcnow().isoformat():
#         await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "expired"}})
#         raise HTTPException(400, "Bid expired")
#     return b


# @router.post("/bids/{bid_id}/reject")
# async def reject_bid(bid_id: str, user: dict = Depends(get_current_user)):
#     b = await _get_bid(bid_id, user)
#     await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "rejected"}})
#     await notify(b["buyer_id"], "bid", f"Your bid ${b['amount']} was rejected", f"/l/{b['listing_id']}")
#     return {"ok": True}


# @router.post("/bids/{bid_id}/counter")
# async def counter_bid(bid_id: str, body: dict, user: dict = Depends(get_current_user)):
#     b = await _get_bid(bid_id, user)
#     amount = float(body.get("amount", 0))
#     if amount <= 0:
#         raise HTTPException(400, "Invalid amount")
#     await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "countered", "counter": amount}})
#     await notify(b["buyer_id"], "bid", f"Counter-offer ${amount} on your bid", f"/l/{b['listing_id']}")
#     return {"ok": True, "counter": amount}


# @router.post("/bids/{bid_id}/accept")
# async def accept_bid(bid_id: str, user: dict = Depends(get_current_user)):
#     from app.core.config import settings
#     b = await _get_bid(bid_id, user)
#     amount = float(b.get("counter") or b["amount"])
#     fee = round(amount * settings.PLATFORM_FEE_PERCENT / 100, 2)
#     oid = new_id()
#     order = {
#         "_id": oid, "listing_id": b["listing_id"], "buyer_id": b["buyer_id"],
#         "seller_id": b["seller_id"], "amount": amount, "fee": fee,
#         "status": "pending", "client_secret": f"mock_secret_bid_{oid[:8]}",
#         "download_token": "", "bid_id": bid_id, "created_at": utcnow().isoformat(),
#     }
#     await db.orders().insert_one(order)
#     await db.bids().update_one({"_id": bid_id}, {"$set": {"status": "accepted"}})
#     # reject other pending bids
#     others = await db.bids().find_many({"listing_id": b["listing_id"]}, limit=200)
#     for o in others:
#         if o["_id"] != bid_id and o.get("status") == "pending":
#             await db.bids().update_one({"_id": o["_id"]}, {"$set": {"status": "rejected"}})
#     await notify(b["buyer_id"], "bid", f"Bid accepted at ${amount}! Complete payment.", "/dashboard")
#     buyer = await db.users().find_one({"_id": b["buyer_id"]})
#     if buyer:
#         await notify_email(buyer["email"], "Bid accepted", f"Pay ${amount} for order {oid}")
#     return {"ok": True, "order_id": oid, "amount": amount}


# @router.get("/bids/analytics")
# async def bid_analytics(user: dict = Depends(get_current_user)):
#     mine = await db.listings().find_many({"seller_id": user["id"]}, limit=500)
#     lids = {m["_id"] for m in mine}
#     allb = await db.bids().find_many({}, limit=2000)
#     rel = [b for b in allb if b["listing_id"] in lids]
#     acc = [b["amount"] for b in rel if b.get("status") == "accepted"]
#     return {
#         "total_bids": len(rel),
#         "accepted": len(acc),
#         "avg_accepted": round(sum(acc) / len(acc), 2) if acc else 0,
#     }


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
