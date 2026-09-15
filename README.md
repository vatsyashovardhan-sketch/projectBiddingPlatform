# Project Bidding Platform — Full build (MVP 🟢 + Phase 2 🟡 + Phase 3/4 🔴)

FARM stack (FastAPI + React + MongoDB). Covers everything in `prompt.txt`; external services run in mock/stub mode until keys are set.

## Run backend
```powershell
cd backend
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```
API: http://localhost:8000/docs · Health: http://localhost:8000/health · Tests: `python -m pytest -q`

MongoDB is used when reachable (`MONGO_URI`), else in-memory store.

## Seed demo data (20 buyers + 40 sellers)
```powershell
cd backend
# terminal 1: python -m uvicorn app.main:app --reload --port 8000
# terminal 2:
python seed.py --api http://localhost:8000
```
Each seller gets a storefront: avatar/bio/skills/GitHub, 2–4 ongoing projects + 1–3 sold projects with prices, plus simulated orders, reviews, bids and follows. All seeded logins use password `Seed1234`. Re-runs are idempotent (existing users/listings/bids/follows are skipped, not duplicated). To wipe seed data from Mongo: `mongosh --quiet cleanup_seed.js`. Browse sellers at `/sellers`, profiles at `/u/:id`.

## Run frontend
```powershell
cd frontend
npm install
npm run dev
```
App: http://localhost:5173.

## What's implemented
- Auth: signup/login/JWT+refresh/logout, password rules, rate-limit, email verify, forgot/reset, GitHub OAuth (mock→real), 2FA stub
- Users: roles, profiles (skills/GitHub/portfolio), follow, student/developer badges, public profiles with rating
- Listings: CRUD + draft/active/sold/removed, categories, tags, demo video, pricing tiers, license, accept-offers toggle, file-hash duplicate flag, full-text-ish search, rating/bids filters, sort (incl. popular/rating), featured/trending/related/tags, view counts, plagiarism report
- Orders/payments: Buy Now (Stripe live or mock), webhook, dashboards, deliver→token download, confirm→payout+commission record, disputes, refunds, payout history, tax-doc stub, Connect onboarding
- Bidding: place/view/accept/reject/counter, 48h expiry job, accept→order, analytics
- Messaging: threads (listing/order), polling + WebSocket realtime, unread badge, block/report
- Reviews: post-completion 1-5 + comment, avg on listing/seller, seller response, report
- Admin: stats/GMV, users ban, listings remove/feature, disputes resolve (refund/release), moderation queue, payout override, analytics
- Notifications: in-app + unread bell, email stub (Resend/SendGrid hook), per-kind prefs
- Jobs: POST /admin… no — POST /jobs/run (admin): expire bids, auto-complete 7d, auto-refund 7d
- Infra: .env, CORS, Pydantic, error shape, logging, rate-limit, pytest, GitHub Actions CI, Sentry hook (SENTRY_DSN), Redis hook (REDIS_URL), S3 presigned hook (USE_S3)

## Security notes
- Banned users are rejected at login and on every authenticated request
- Login rate-limited per IP (200/5min) + per email (15/5min); buckets memory-capped
- Passwords: 8–72 chars (bcrypt limit), letter + number
- Search input regex-escaped; uploads capped (5MB images, 50MB zips) with magic-byte checks
- Project zips are never publicly served — token-gated `FileResponse` only; demo-video URLs must be http(s)
- Public APIs never expose emails (contact via in-app chat); sold listings can't be relisted (double-sell guard)
- Set a real `JWT_SECRET` in `backend/.env` (startup warns on default); keep `.env` out of git
