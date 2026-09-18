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
