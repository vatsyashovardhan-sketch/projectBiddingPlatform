import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.db.database import init_db
from app.routers import admin, auth, bidding, jobs, listings, messages, notifications, orders, reviews, uploads, users

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

# Optional Redis cache client. Stays None when REDIS_URL is absent or
# unreachable (or the optional `redis` package isn't installed).
redis_client = None


def _init_sentry() -> None:
    if not os.environ.get("SENTRY_DSN"):
        return
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
        log.info("Sentry enabled")
    except Exception as e:
        log.warning(f"Sentry init failed: {e}")


def _init_redis() -> None:
    global redis_client
    url = os.environ.get("REDIS_URL")
    if not url:
        return
    try:
        import redis
        client = redis.from_url(url, decode_responses=True)
        client.ping()
        redis_client = client
        log.info("Redis enabled")
    except Exception as e:
        redis_client = None
        log.warning(f"Redis unavailable, using memory fallback: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_sentry()
    _init_redis()
    await init_db()
    if settings.JWT_SECRET == "change-me-to-a-long-random-string":
        log.warning("JWT_SECRET is the default value — set a long random string in .env before any real use")
    yield
    if redis_client is not None:
        try:
            redis_client.close()
        except Exception as e:
            log.warning(f"Redis close failed: {e}")


app = FastAPI(title="Project Bidding Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
