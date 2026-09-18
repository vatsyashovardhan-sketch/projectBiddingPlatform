from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.deps import get_current_user
from app.core.ratelimit import rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    new_id,
    utcnow,
    validate_password_rules,
    verify_password,
)
from app.db import database as db
from app.db.database import BLACKLISTED_JTIS, users
from app.models.schemas import LoginIn, RefreshIn, SignupIn

router = APIRouter(prefix="/auth", tags=["auth"])


def _out(user: dict) -> dict:
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "bio": user.get("bio", ""),
        "avatar": user.get("avatar", ""),
        "stripe_account_id": user.get("stripe_account_id", ""),
        "email_verified": user.get("email_verified", False),
        "badges": user.get("badges", []),
        "skills": user.get("skills", []),
        "github": user.get("github", ""),
        "portfolio": user.get("portfolio", []),
        "interests": user.get("interests", []),
    }


@router.post("/signup")
async def signup(body: SignupIn, request: Request):
    rate_limit(f"signup:{request.client.host if request.client else 'x'}", 200, 300)
    err = validate_password_rules(body.password)
    if err:
        raise HTTPException(400, err)
    existing = await users().find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(400, "Email already registered")
    uid = new_id()
    user = {
        "_id": uid,
        "email": body.email.lower(),
        "password": hash_password(body.password),
        "name": body.name,
        "role": body.role,
        "bio": "",
        "avatar": "",
        "stripe_account_id": "",
        "email_verified": False,
        "badges": [],
        "skills": [],
        "github": "",
        "portfolio": [],
        "created_at": utcnow().isoformat(),
    }
    await users().insert_one(user)
    # email verification token (mock email in dev)
    token = new_id()
    await db.col("verifies").insert_one({"_id": token, "user_id": uid, "created_at": utcnow().isoformat()})
    from app.core.notify import notify_email
    await notify_email(user["email"], "Verify your email", f"Token: {token} (POST /auth/verify-email)")
    return {
        "user": _out(user),
        "access_token": create_access_token(uid),
        "refresh_token": create_refresh_token(uid),
        "verify_token_dev": token,
    }


@router.post("/login")
async def login(body: LoginIn, request: Request):
    rate_limit(f"login:{request.client.host if request.client else 'x'}", 200, 300)
    rate_limit(f"login-email:{body.email.lower()}", 15, 300)  # slow password-guessing per account
    user = await users().find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    if user.get("banned"):
        raise HTTPException(403, "Account suspended")
    uid = user["_id"]
    return {
        "user": _out(user),
        "access_token": create_access_token(uid),
        "refresh_token": create_refresh_token(uid),
    }


@router.post("/refresh")
async def refresh(body: RefreshIn):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(401, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    if payload.get("jti") in BLACKLISTED_JTIS:
        raise HTTPException(401, "Logged out")
    user = await users().find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(401, "User not found")
    return {
        "access_token": create_access_token(user["_id"]),
        "refresh_token": create_refresh_token(user["_id"]),
    }


@router.post("/logout")
async def logout(body: RefreshIn | None = None, user: dict = Depends(get_current_user)):
    # Blacklist the refresh token if provided; access token short-lived.
    if body and body.refresh_token:
        try:
            p = decode_token(body.refresh_token)
            if p.get("jti"):
                BLACKLISTED_JTIS.add(p["jti"])
        except Exception:
            pass
    return {"ok": True}


@router.post("/verify-email")
async def verify_email(body: dict):
    token = body.get("token", "")
    v = await db.col("verifies").find_one({"_id": token})
    if not v:
        raise HTTPException(400, "Invalid token")
    await users().update_one({"_id": v["user_id"]}, {"$set": {"email_verified": True}})
    await db.col("verifies").delete_one({"_id": token})
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(body: dict):
    u = await users().find_one({"email": (body.get("email") or "").lower()})
    token = new_id()
    if u:
        await db.col("resets").insert_one({"_id": token, "user_id": u["_id"], "created_at": utcnow().isoformat()})
        from app.core.notify import notify_email
        await notify_email(u["email"], "Reset password", f"Token: {token} (POST /auth/reset-password)")
    return {"ok": True, "reset_token_dev": token}


@router.post("/reset-password")
async def reset_password(body: dict):
    r = await db.col("resets").find_one({"_id": body.get("token", "")})
    if not r:
        raise HTTPException(400, "Invalid token")
    err = validate_password_rules(body.get("password", ""))
    if err:
        raise HTTPException(400, err)
    await users().update_one({"_id": r["user_id"]}, {"$set": {"password": hash_password(body["password"])}})
    await db.col("resets").delete_one({"_id": r["_id"]})
    return {"ok": True}


@router.get("/oauth/github")
async def oauth_github():
    from app.core.config import settings
    import os
    cid = os.environ.get("GITHUB_CLIENT_ID", "")
    if not cid:
        return {"mode": "mock", "note": "Set GITHUB_CLIENT_ID/SECRET for real OAuth; POST /auth/oauth/callback with email+name in mock mode"}
    return {"url": f"https://github.com/login/oauth/authorize?client_id={cid}"}


@router.post("/oauth/callback")
async def oauth_callback(body: dict):
    """Mock OAuth: pass email+name (dev). Real flow exchanges code via GitHub here."""
    email = (body.get("email") or "").lower()
    if not email:
        raise HTTPException(400, "email required in mock mode")
    u = await users().find_one({"email": email})
    if not u:
        uid = new_id()
        u = {"_id": uid, "email": email, "password": hash_password(new_id()), "name": body.get("name", email.split("@")[0]),
             "role": "both", "bio": "", "avatar": "", "stripe_account_id": "", "email_verified": True,
             "badges": ["developer"] if body.get("github") else [], "github": body.get("github", ""),
             "skills": [], "portfolio": [], "created_at": utcnow().isoformat()}
        await users().insert_one(u)
    return {"user": _out(u), "access_token": create_access_token(u["_id"]), "refresh_token": create_refresh_token(u["_id"])}


@router.post("/2fa/enable")
async def tfa_enable(user: dict = Depends(get_current_user)):
    secret = new_id()[:16]
    await users().update_one({"_id": user["id"]}, {"$set": {"tfa_secret": secret}})
    return {"otpauth_url": f"otpauth://totp/ProjectBidding:{user['id']}?secret={secret}&issuer=ProjectBidding",
            "note": "Confirm with POST /auth/2fa/verify {code}. Dev mock accepts any 6-digit code once."}


@router.post("/2fa/verify")
async def tfa_verify(body: dict, user: dict = Depends(get_current_user)):
    if len(str(body.get("code", ""))) != 6:
        raise HTTPException(400, "Invalid code")
    await users().update_one({"_id": user["id"]}, {"$set": {"tfa_enabled": True}})
    return {"ok": True}
