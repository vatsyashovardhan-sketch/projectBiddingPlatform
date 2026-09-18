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
