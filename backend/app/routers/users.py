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
