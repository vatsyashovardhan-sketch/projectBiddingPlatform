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
