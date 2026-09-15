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
