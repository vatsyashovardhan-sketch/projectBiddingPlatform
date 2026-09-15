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
