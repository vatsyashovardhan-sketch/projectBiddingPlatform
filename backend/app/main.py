import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import init_db
from app.routers import admin, auth, bidding, jobs, listings, messages, notifications, orders, reviews, uploads, users

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

if os.environ.get("SENTRY_DSN"):
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
        log.info("Sentry enabled")
    except Exception as e:
        log.warning(f"Sentry init failed: {e}")

# Redis cache hook (falls back to memory when REDIS_URL absent)
CACHE: dict = {}
if os.environ.get("REDIS_URL"):
    try:
        import redis
        _r = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        _r.ping()
        log.info("Redis enabled")
    except Exception as e:
        log.warning(f"Redis unavailable, using memory cache: {e}")

app = FastAPI(title="Project Bidding Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    if hasattr(exc, "status_code"):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def startup():
    await init_db()
    if settings.JWT_SECRET == "change-me-to-a-long-random-string":
        log.warning("JWT_SECRET is the default value — set a long random string in .env before any real use")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/")
async def root():
    return {"name": "Project Bidding API", "docs": "/docs", "health": "/health"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(bidding.router)
app.include_router(messages.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(jobs.router)
uploads.mount_static(app)
