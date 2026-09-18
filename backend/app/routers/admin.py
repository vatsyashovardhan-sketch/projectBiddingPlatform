# """Admin panel: users, listings, orders/disputes, analytics, moderation."""
# from fastapi import APIRouter, Depends, HTTPException

# from app.core.deps import get_current_user, require_admin
# from app.core.security import utcnow
# from app.db import database as db

# router = APIRouter(prefix="/admin", tags=["admin"])


# @router.get("/stats")
# async def stats(_: dict = Depends(require_admin)):
#     users_n = await db.users().count({})
#     listings_n = await db.listings().count({})
#     orders = await db.orders().find_many({}, limit=5000)
#     gmv = round(sum(o["amount"] for o in orders if o.get("status") in ("paid", "delivered", "completed")), 2)
#     by_status: dict[str, int] = {}
#     for o in orders:
#         by_status[o.get("status", "?")] = by_status.get(o.get("status", "?"), 0) + 1
#     cats: dict[str, int] = {}
#     lsts = await db.listings().find_many({}, limit=5000)
#     for l in lsts:
#         cats[l.get("category", "?")] = cats.get(l.get("category", "?"), 0) + 1
#     return {"users": users_n, "listings": listings_n, "orders": len(orders),
#             "gmv": gmv, "orders_by_status": by_status, "top_categories": cats}


# @router.get("/users")
# async def all_users(_: dict = Depends(require_admin)):
#     from app.core.notify import seller_strikes
#     items = await db.users().find_many({}, limit=500)
#     out = []
#     for u in items:
#         strikes = await seller_strikes(u["_id"]) if u.get("role") in ("seller", "both") else 0
#         out.append({"id": u["_id"], "email": u["email"], "name": u["name"], "role": u["role"],
#                     "banned": u.get("banned", False), "strikes": strikes})
#     return out


# @router.post("/users/{uid}/ban")
# async def ban(uid: str, body: dict, _: dict = Depends(require_admin)):
#     await db.users().update_one({"_id": uid}, {"$set": {"banned": bool(body.get("banned", True))}})
#     return {"ok": True}


# @router.get("/listings")
# async def all_listings(_: dict = Depends(require_admin)):
#     return await db.listings().find_many({}, limit=500, sort=[("created_at", -1)])


# @router.post("/listings/{lid}/remove")
# async def remove_listing(lid: str, _: dict = Depends(require_admin)):
#     await db.listings().update_one({"_id": lid}, {"$set": {"status": "removed"}})
#     return {"ok": True}


# @router.post("/listings/{lid}/feature")
# async def feature_listing(lid: str, body: dict, _: dict = Depends(require_admin)):
#     await db.listings().update_one({"_id": lid}, {"$set": {"featured": bool(body.get("featured", True))}})
#     return {"ok": True}


# @router.get("/orders")
# async def all_orders(status: str = "", _: dict = Depends(require_admin)):
#     flt = {"status": status} if status else {}
#     return await db.orders().find_many(flt, limit=500, sort=[("created_at", -1)])


# @router.post("/orders/{oid}/resolve")
# async def resolve_dispute(oid: str, body: dict, _: dict = Depends(require_admin)):
#     """action: refund | release"""
#     o = await db.orders().find_one({"_id": oid})
#     if not o:
#         raise HTTPException(404, "Order not found")
#     action = body.get("action")
#     if action == "refund":
#         await db.orders().update_one({"_id": oid}, {"$set": {"status": "refunded"}})
#     elif action == "release":
#         await db.orders().update_one({"_id": oid}, {"$set": {"status": "completed"}})
#         await db.listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
#     else:
#         raise HTTPException(400, "action must be refund|release")
#     return {"ok": True}


# @router.get("/reports")
# async def moderation_queue(_: dict = Depends(require_admin)):
#     return await db.col("reports").find_many({}, limit=200, sort=[("created_at", -1)])


# @router.post("/payouts/override")
# async def payout_override(body: dict, user: dict = Depends(require_admin)):
#     from app.core.security import new_id
#     await db.col("payouts").insert_one({
#         "_id": new_id(), "order_id": body.get("order_id", ""), "seller_id": body.get("seller_id", ""),
#         "amount": float(body.get("amount", 0)), "note": body.get("note", "manual override"),
#         "by": user["id"], "created_at": utcnow().isoformat(),
#     })
#     return {"ok": True}


# @router.get("/analytics")
# async def analytics(_: dict = Depends(require_admin)):
#     revs = await db.reviews().find_many({}, limit=5000)
#     avg = round(sum(r["rating"] for r in revs) / len(revs), 2) if revs else 0
#     return {"total_reviews": len(revs), "avg_rating": avg}


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
