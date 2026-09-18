# import uuid
# from datetime import datetime, timedelta, timezone

# import bcrypt
# import jwt

# from app.core.config import settings


# def hash_password(password: str) -> str:
#     return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# def verify_password(password: str, hashed: str) -> bool:
#     try:
#         return bcrypt.checkpw(password.encode(), hashed.encode())
#     except Exception:
#         return False


# def validate_password_rules(password: str) -> str | None:
#     """Return error message if invalid, else None."""
#     if len(password) < 8:
#         return "Password must be at least 8 characters"
#     if len(password.encode()) > 72:
#         return "Password must be at most 72 characters (bcrypt limit)"
#     if not any(c.isdigit() for c in password):
#         return "Password must contain a number"
#     if not any(c.isalpha() for c in password):
#         return "Password must contain a letter"
#     return None


# def _encode(payload: dict) -> str:
#     return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# def create_access_token(user_id: str) -> str:
#     exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     return _encode({"sub": user_id, "type": "access", "exp": exp, "jti": uuid.uuid4().hex})


# def create_refresh_token(user_id: str) -> str:
#     exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#     return _encode({"sub": user_id, "type": "refresh", "exp": exp, "jti": uuid.uuid4().hex})


# def decode_token(token: str) -> dict:
#     return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# def new_id() -> str:
#     return uuid.uuid4().hex[:24]


# def utcnow() -> datetime:
#     return datetime.now(timezone.utc)
