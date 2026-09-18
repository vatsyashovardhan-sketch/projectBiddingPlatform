from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.database import BLACKLISTED_JTIS, users

bearer = HTTPBearer(auto_error=False)


async def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    if payload.get("jti") in BLACKLISTED_JTIS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Logged out")
    user = await users().find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.get("banned"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
    user["id"] = user.pop("_id")
    return user


def require_roles(*roles: str):
    async def checker(user: dict = Depends(get_current_user)):
        # "both" can do everything buyer/seller can
        user_roles = {user.get("role", "buyer"), "both"} if user.get("role") == "both" else {user.get("role")}
        if user.get("role") == "both":
            return user
        if user.get("role") not in roles and "both" not in roles:
            # allow "both" users through regardless
            if not (set(roles) & user_roles):
                raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker


async def require_seller(user: dict = Depends(get_current_user)):
    if user.get("role") not in ("seller", "both", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers can perform this action")
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
