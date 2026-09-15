"""Orders + payments MVP.

Real Stripe when STRIPE_SECRET_KEY is set, otherwise MOCK mode:
- POST /orders creates order + fake client_secret
- POST /orders/{id}/mock-pay simulates the webhook (marks paid)
Production: configure Stripe webhook -> POST /webhooks/stripe.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.notify import notify, notify_email
from app.core.security import new_id, utcnow
from app.db import database as db
from app.db.database import listings, orders

router = APIRouter(tags=["orders"])
STRIPE_MODE = bool(settings.STRIPE_SECRET_KEY)


def _out(o: dict) -> dict:
    return {
        "id": o["_id"],
        "listing_id": o["listing_id"],
        "buyer_id": o["buyer_id"],
        "seller_id": o["seller_id"],
        "amount": o["amount"],
        "fee": o.get("fee", 0),
        "status": o["status"],
        "client_secret": o.get("client_secret", ""),
        "download_token": o.get("download_token", ""),
        "created_at": o.get("created_at"),
    }


def _fee(amount: float) -> float:
    return round(amount * settings.PLATFORM_FEE_PERCENT / 100, 2)


@router.post("/orders")
async def buy_now(body: dict, user: dict = Depends(get_current_user)):
    listing_id = body.get("listing_id")
    lst = await listings().find_one({"_id": listing_id})
    if not lst or lst.get("status") != "active":
        raise HTTPException(404, "Listing not available")
    if lst["seller_id"] == user["id"]:
        raise HTTPException(400, "Cannot buy your own listing")
    oid = new_id()
    amount = float(lst["price"])
    client_secret = ""
    if STRIPE_MODE:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency="usd",
            metadata={"order_id": oid, "listing_id": listing_id},
        )
        client_secret = intent.client_secret
    else:
        client_secret = f"mock_secret_{uuid.uuid4().hex[:12]}"
    order = {
        "_id": oid,
        "listing_id": listing_id,
        "buyer_id": user["id"],
        "seller_id": lst["seller_id"],
        "amount": amount,
        "fee": _fee(amount),
        "status": "pending",
        "client_secret": client_secret,
        "download_token": "",
        "created_at": utcnow().isoformat(),
    }
    await orders().insert_one(order)
    await notify(order["seller_id"], "order", f"New order for {lst['title']} (${amount})", "/dashboard")
    buyer = await db.users().find_one({"_id": user["id"]})
    if buyer:
        await notify_email(buyer["email"], "Order placed", f"Order {oid} for {lst['title']} — complete payment.")
    return {**_out(order), "stripe_mode": "live" if STRIPE_MODE else "mock"}


@router.post("/orders/{order_id}/mock-pay")
async def mock_pay(order_id: str, user: dict = Depends(get_current_user)):
    """Dev-only: simulate successful payment when Stripe keys absent."""
    if STRIPE_MODE:
        raise HTTPException(400, "Stripe live mode — pay via Stripe, not mock")
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["buyer_id"] != user["id"]:
        raise HTTPException(403, "Not your order")
    await orders().update_one({"_id": order_id}, {"$set": {"status": "paid"}})
    o["status"] = "paid"
    await notify(o["seller_id"], "order", f"Order {order_id[:8]} paid — deliver files", "/dashboard")
    seller = await db.users().find_one({"_id": o["seller_id"]})
    if seller:
        await notify_email(seller["email"], "Payment received", f"Order {order_id} paid. Deliver files.")
    return _out(o)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    if STRIPE_MODE:
        import stripe
        sig = request.headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            raise HTTPException(400, f"Webhook error: {e}")
        if event["type"] == "payment_intent.succeeded":
            oid = event["data"]["object"]["metadata"].get("order_id")
            if oid:
                await orders().update_one({"_id": oid}, {"$set": {"status": "paid"}})
        return {"received": True}
    return {"ok": True, "mode": "mock"}


@router.get("/orders/purchases")
async def my_purchases(user: dict = Depends(get_current_user)):
    items = await orders().find_many({"buyer_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [await _enrich(o) for o in items]


@router.get("/orders/sales")
async def my_sales(user: dict = Depends(get_current_user)):
    items = await orders().find_many({"seller_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    return [await _enrich(o) for o in items]


async def _enrich(o: dict) -> dict:
    """Attach listing title/image so dashboards read like an order history, not IDs."""
    base = _out(o)
    try:
        lst = await listings().find_one({"_id": o["listing_id"]})
        if lst:
            base["listing_title"] = lst["title"]
            base["listing_image"] = (lst.get("images") or [""])[0]
    except Exception:
        pass
    return base


@router.post("/orders/{order_id}/deliver")
async def deliver(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["seller_id"] != user["id"]:
        raise HTTPException(403, "Only seller can deliver")
    if o["status"] != "paid":
        raise HTTPException(400, "Order must be paid before delivery")
    token = uuid.uuid4().hex
    await orders().update_one({"_id": order_id}, {"$set": {"status": "delivered", "download_token": token}})
    o["status"] = "delivered"
    o["download_token"] = token
    await notify(o["buyer_id"], "order", "Your files are ready to download", "/dashboard")
    return _out(o)


@router.get("/orders/{order_id}/download")
async def download(order_id: str, token: str = "", user: dict = Depends(get_current_user)):
    import os
    from fastapi.responses import FileResponse
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if user["id"] not in (o["buyer_id"], o["seller_id"]) and user.get("role") != "admin":
        raise HTTPException(403, "No access")
    if o["status"] not in ("delivered", "completed"):
        raise HTTPException(400, "Files available only after seller delivers")
    if user["id"] == o["buyer_id"] and o.get("download_token") != token:
        raise HTTPException(403, "Invalid download token")
    lst = await listings().find_one({"_id": o["listing_id"]})
    if not lst or not lst.get("project_file"):
        raise HTTPException(404, "No project file attached to this listing")
    key = lst["project_file"]
    name = ""
    if key.startswith("locked:files/"):
        name = os.path.basename(key.split("locked:files/", 1)[1])
    elif key.startswith("/uploads/files/"):
        name = os.path.basename(key)  # legacy key shape, same locked dir
    if name:
        from app.routers.uploads import FILES
        path = os.path.join(FILES, name)
        if os.path.isfile(path):
            return FileResponse(path, filename=f"{lst['title'][:40]}.zip")
        raise HTTPException(404, "Project file no longer on server")
    return {"file_url": key, "listing": lst["title"]}  # external/S3 URL case


@router.post("/orders/{order_id}/confirm")
async def confirm_receipt(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["buyer_id"] != user["id"]:
        raise HTTPException(403, "Only buyer can confirm")
    if o["status"] != "delivered":
        raise HTTPException(400, "Order must be delivered first")
    payout = round(o["amount"] - o.get("fee", 0), 2)
    # Real payout: Stripe transfer to seller's Connect account happens here.
    if STRIPE_MODE:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            seller = await db.users().find_one({"_id": o["seller_id"]})
            if seller and seller.get("stripe_account_id"):
                stripe.Transfer.create(amount=int(payout * 100), currency="usd",
                                       destination=seller["stripe_account_id"],
                                       metadata={"order_id": order_id})
        except Exception:
            pass
    await db.col("payouts").insert_one({
        "_id": new_id(), "order_id": order_id, "seller_id": o["seller_id"],
        "amount": payout, "fee": o.get("fee", 0), "created_at": utcnow().isoformat()})
    await listings().update_one({"_id": o["listing_id"]}, {"$set": {"status": "sold"}})
    await orders().update_one({"_id": order_id}, {"$set": {"status": "completed"}})
    o["status"] = "completed"
    await notify(o["seller_id"], "order", f"Order {order_id[:8]} completed — ${payout} payout", "/dashboard")
    return {**_out(o), "payout_to_seller": payout}


@router.post("/orders/{order_id}/refund")
async def refund(order_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if STRIPE_MODE:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Refund.create(payment_intent=o.get("client_secret", "").split("_secret")[0])
        except Exception:
            pass
    await orders().update_one({"_id": order_id}, {"$set": {"status": "refunded"}})
    return {"ok": True}


@router.get("/payments/payouts")
async def payout_history(user: dict = Depends(get_current_user)):
    items = await db.col("payouts").find_many({"seller_id": user["id"]}, limit=100, sort=[("created_at", -1)])
    total = round(sum(p["amount"] for p in items), 2)
    return {"items": items, "total": total}


@router.get("/payments/tax-doc")
async def tax_doc(user: dict = Depends(get_current_user)):
    items = await db.col("payouts").find_many({"seller_id": user["id"]}, limit=5000)
    total = round(sum(p["amount"] for p in items), 2)
    return {"seller": user["id"], "year": 2026, "total_payouts": total,
            "note": "Stub — generate 1099 equivalent at real scale"}


@router.post("/orders/{order_id}/dispute")
async def dispute(order_id: str, user: dict = Depends(get_current_user)):
    o = await orders().find_one({"_id": order_id})
    if not o:
        raise HTTPException(404, "Order not found")
    if user["id"] not in (o["buyer_id"], o["seller_id"]):
        raise HTTPException(403, "No access")
    await orders().update_one({"_id": order_id}, {"$set": {"status": "disputed"}})
    o["status"] = "disputed"
    return _out(o)


@router.get("/payments/connect-status")
async def connect_status(user: dict = Depends(get_current_user)):
    if STRIPE_MODE:
        return {"connected": bool(user.get("stripe_account_id")), "mode": "live"}
    return {"connected": True, "mode": "mock", "note": "Set STRIPE_SECRET_KEY for real Connect onboarding"}


@router.post("/payments/connect-onboard")
async def connect_onboard(user: dict = Depends(get_current_user)):
    from app.db.database import users
    if STRIPE_MODE:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        acct = stripe.Account.create(type="express")
        await users().update_one({"_id": user["id"]}, {"$set": {"stripe_account_id": acct.id}})
        link = stripe.AccountLink.create(account=acct.id, refresh_url=settings.FRONTEND_URL, return_url=settings.FRONTEND_URL, type="account_onboarding")
        return {"url": link.url, "mode": "live"}
    fake = f"acct_mock_{user['id'][:8]}"
    await users().update_one({"_id": user["id"]}, {"$set": {"stripe_account_id": fake}})
    return {"url": "", "mode": "mock", "account_id": fake}
