"""Section 1-11 audit: exercises every prompt.txt subfeature. Run: python audit_features.py"""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
passed = []


def check(name, cond):
    assert cond, f"FAILED: {name}"
    passed.append(name)


def signup(email, role="both", name=None):
    r = c.post("/auth/signup", json={"email": email, "password": "Pass1234",
                                     "name": name or email.split("@")[0], "role": role})
    assert r.status_code == 200, (email, r.text)
    return r.json()


# ---------- 1. Auth ----------
s = signup("audit-seller@test.com", "seller")
b = signup("audit-buyer@test.com", "buyer")
hs = {"Authorization": f"Bearer {s['access_token']}"}
hb = {"Authorization": f"Bearer {b['access_token']}"}
check("1.1 signup", "access_token" in s)
r = c.post("/auth/login", json={"email": "audit-buyer@test.com", "password": "Pass1234"})
check("1.1 login JWT", r.status_code == 200 and "access_token" in r.json())
r = c.post("/auth/refresh", json={"refresh_token": b["refresh_token"]})
check("1.1 refresh", r.status_code == 200 and "access_token" in r.json())
check("1.1 logout", c.post("/auth/logout", json={"refresh_token": b["refresh_token"]}, headers=hb).status_code == 200)
check("1.1 pw rules", c.post("/auth/signup", json={"email": "x@t.com", "password": "short",
                                                   "name": "x", "role": "buyer"}).status_code in (400, 422))
tok = s["verify_token_dev"]
check("1.1 verify email", c.post("/auth/verify-email", json={"token": tok}).status_code == 200)
f = c.post("/auth/forgot-password", json={"email": "audit-buyer@test.com"})
check("1.1 forgot", f.status_code == 200)
check("1.1 reset", c.post("/auth/reset-password", json={"token": f.json()["reset_token_dev"],
                                                        "password": "Newpass123"}).status_code == 200)
check("1.1 oauth stub", c.post("/auth/oauth/callback", json={"email": "gh@test.com", "name": "GH"}).status_code == 200)
check("1.1 2fa", c.post("/auth/2fa/enable", headers=hb).status_code == 200)
check("1.2 roles/profile/edit", c.get("/users/me", headers=hb).status_code == 200)
check("1.2 seller fields", c.patch("/users/me", json={"skills": ["python"], "github": "gh",
                                                       "portfolio": ["https://x"]}, headers=hs).status_code == 200)
check("1.2 public profile", c.get(f"/users/{s['user']['id']}").status_code == 200)
check("1.2 badges", c.post("/users/me/link-github", json={"github": "gh"}, headers=hs).status_code == 200)
check("1.2 follow", c.post(f"/users/{s['user']['id']}/follow", json={"following": True}, headers=hb).status_code == 200)
check("1.3 buyer blocked from sell", c.post("/listings", json={"title": "Nope nope nope",
      "description": "should fail validation here", "price": 5, "category": "Other"}, headers=hb).status_code == 403)
check("1.3 unauth blocked", c.get("/users/me").status_code in (401, 403))

# ---------- 2. Listings ----------
lst = {"title": "Audit Web App", "description": "A complete audit test project with docs",
       "price": 50, "category": "Web App", "tech_stack": ["react"],
       "demo_video": "https://loom.test/x", "pricing_tiers": [{"name": "code", "price": 50}],
       "license": "resale", "accept_offers": True, "file_hash": "abc123audit"}
r = c.post("/listings", json=lst, headers=hs)
check("2.1 create full", r.status_code == 200)
lid = r.json()["id"]
check("2.1 edit", c.patch(f"/listings/{lid}", json={"price": 55}, headers=hs).status_code == 200)
check("2.2 feed/search/filter/sort", c.get("/listings?q=audit&category=Web+App&sort=price_asc").status_code == 200)
check("2.2 rating+bids filter", c.get("/listings?min_rating=0&open_to_bids=true").status_code == 200)
check("2.2 related/featured/trending/tags",
      c.get(f"/listings/{lid}/related").status_code == 200
      and c.get("/listings/featured").status_code == 200
      and c.get("/listings/trending").status_code == 200
      and c.get("/listings/tags").status_code == 200)
d1 = c.get(f"/listings/{lid}").json()
d2 = c.get(f"/listings/{lid}").json()
check("2.3 detail+views+buy", d2["views"] == d1["views"] + 1 and d2["license"] == "resale")
check("2.1 duplicate hash flag",
      c.post("/listings", json={**lst, "title": "Audit Clone Project"}, headers=hs).json().get("duplicate_warning") is True)
check("2.3 report", c.post(f"/listings/{lid}/report", json={"reason": "test"}, headers=hb).status_code == 200)
check("2.1 archive", c.delete(f"/listings/{lid}", headers=hs).status_code == 200)
dl = c.post("/listings", json={**lst, "title": "Audit Delete Me", "file_hash": "del1"}, headers=hs).json()
check("2.1 delete non-owner blocked", c.delete(f"/listings/{dl['id']}", headers=hb).status_code == 403)
check("2.1 seller delete", c.delete(f"/listings/{dl['id']}", headers=hs).status_code == 200
      and c.get(f"/listings/{dl['id']}").json()["status"] == "removed")
# fresh listing for order flow
r = c.post("/listings", json={**lst, "title": "Audit Buy Flow", "file_hash": "buyflow1"}, headers=hs)
buy_id = r.json()["id"]

# ---------- 3. Orders ----------
o = c.post("/orders", json={"listing_id": buy_id}, headers=hb).json()
check("3.1 buy+intent", o["status"] == "pending" and o["client_secret"])
oid = o["id"]
check("3.1 webhook mock", c.post("/webhooks/stripe", content=b"{}").status_code == 200)
check("3.1 mock-pay", c.post(f"/orders/{oid}/mock-pay", headers=hb).status_code == 200)
check("2.1 delete blocked w/ live order", c.delete(f"/listings/{buy_id}", headers=hs).status_code == 400)
check("3.1 dashboards", c.get("/orders/purchases", headers=hb).status_code == 200
      and c.get("/orders/sales", headers=hs).status_code == 200)
check("3.1 order titles", c.get("/orders/purchases", headers=hb).json()[0].get("listing_title") == "Audit Buy Flow")
dlv = c.post(f"/orders/{oid}/deliver", headers=hs).json()
check("3.2 deliver", dlv["status"] == "delivered")
check("3.2 token download", c.get(f"/orders/{oid}/download?token=" + dlv["download_token"], headers=hb).status_code in (200, 404))
check("3.2 bad token rejected", c.get(f"/orders/{oid}/download?token=wrong", headers=hb).status_code == 403)
check("3.2 confirm+payout", c.post(f"/orders/{oid}/confirm", headers=hb).json().get("payout_to_seller", 0) > 0)
check("3.2 dispute", c.post(f"/orders/{oid}/dispute", headers=hb).status_code == 200)
check("3.3 connect+commission+payouts",
      c.post("/payments/connect-onboard", headers=hs).status_code == 200
      and c.get("/payments/payouts", headers=hs).json()["total"] > 0
      and c.get("/payments/tax-doc", headers=hs).status_code == 200)
# admin for refund/resolve
a = signup("audit-admin@test.com", "both")
c.patch("/users/me", json={"role": "admin"}, headers={"Authorization": f"Bearer {a['access_token']}"})
ha = {"Authorization": f"Bearer {a['access_token']}"}
check("3.3 refund", c.post(f"/orders/{oid}/refund", headers=ha).status_code == 200)
check("3.4 admin orders+resolve", c.get("/admin/orders", headers=ha).status_code == 200
      and c.post(f"/admin/orders/{oid}/resolve", json={"action": "release"}, headers=ha).status_code == 200)
check("3.4 auto rules job", c.post("/jobs/run", headers=ha).status_code == 200)

# ---------- 4. Bidding ----------
bl = c.post("/listings", json={**lst, "title": "Audit Bid Item", "file_hash": "bid1"}, headers=hs).json()
bid = c.post(f"/listings/{bl['id']}/bids", json={"amount": 40, "message": "hi"}, headers=hb).json()
check("4 place+list", bid["id"] and len(c.get(f"/listings/{bl['id']}/bids", headers=hs).json()) >= 1)
check("4 counter", c.post(f"/bids/{bid['id']}/counter", json={"amount": 45}, headers=hs).status_code == 200)
bid2 = c.post(f"/listings/{bl['id']}/bids", json={"amount": 42}, headers=hb).json()
acc = c.post(f"/bids/{bid2['id']}/accept", headers=hs).json()
check("4 accept->order", acc.get("order_id"))
check("4 analytics", c.get("/bids/analytics", headers=hs).status_code == 200)
check("4 incoming inbox", any(b.get("listing_title") for b in c.get("/bids/incoming", headers=hs).json()))
check("4 reject", c.post(f"/bids/{bid['id']}/reject", headers=hs).status_code in (200, 400))

# ---------- 5. Messaging ----------
th = c.post("/threads", json={"listing_id": bl["id"]}, headers=hb).json()
check("5 thread", th["id"])
check("5 send+poll", c.post(f"/threads/{th['id']}/messages", json={"text": "hello?"}, headers=hb).status_code == 200
      and len(c.get(f"/threads/{th['id']}/messages", headers=hs).json()) >= 1)
check("5 unread+block/report", c.get("/threads", headers=hs).status_code == 200
      and c.post(f"/users/{b['user']['id']}/block", headers=hs).status_code == 200
      and c.post(f"/users/{b['user']['id']}/report", json={"reason": "spam"}, headers=hs).status_code == 200)

# ---------- 6. Reviews ----------
o2 = c.post("/orders", json={"listing_id": bl["id"]}, headers=hb).json()
c.post(f"/orders/{o2['id']}/mock-pay", headers=hb)
c.post(f"/orders/{o2['id']}/deliver", headers=hs)
c.post(f"/orders/{o2['id']}/confirm", headers=hb)
rv = c.post(f"/orders/{o2['id']}/reviews", json={"rating": 5, "comment": "great"}, headers=hb)
check("6 review+avg", rv.status_code == 200 and c.get(f"/listings/{bl['id']}/reviews").status_code == 200)
check("6 seller rating denormalized", c.get(f"/listings/{bl['id']}").json().get("seller_rating", 0) >= 5
      and len(c.get("/listings?min_rating=4&limit=50").json()["items"]) >= 1)
rid = rv.json()["id"]
check("6 respond+report", c.post(f"/reviews/{rid}/respond", json={"response": "ty"}, headers=hs).status_code == 200
      and c.post(f"/reviews/{rid}/report", json={"reason": "fake"}, headers=hb).status_code == 200)

# ---------- 7. Admin ----------
check("7 stats/users/ban", c.get("/admin/stats", headers=ha).status_code == 200
      and c.get("/admin/users", headers=ha).status_code == 200
      and c.post(f"/admin/users/{b['user']['id']}/ban", json={"banned": False}, headers=ha).status_code == 200)
check("7 listings mod", c.get("/admin/listings", headers=ha).status_code == 200
      and c.post(f"/admin/listings/{bl['id']}/feature", json={"featured": True}, headers=ha).status_code == 200
      and c.get("/admin/reports", headers=ha).status_code == 200
      and c.get("/admin/analytics", headers=ha).status_code == 200
      and c.post("/admin/payouts/override", json={"order_id": oid, "seller_id": s["user"]["id"],
                                                  "amount": 1}, headers=ha).status_code == 200)
check("7 non-admin blocked", c.get("/admin/stats", headers=hb).status_code == 403)

# ---------- 8. Notifications ----------
check("8 list+prefs", c.get("/notifications", headers=hs).status_code == 200
      and c.get("/notifications/prefs", headers=hs).status_code == 200
      and c.post("/notifications/prefs", json={"opt_out": {"system": True}}, headers=hs).status_code == 200)

# ---------- 9/10/11 ----------
check("9 categories", "Web App" in c.get("/listings/categories").json()["categories"])
check("9 category specs", c.post("/listings", json={**lst, "title": "Audit Specs Item",
      "file_hash": "specs1", "specs": {"dataset size": "10k rows", "accuracy": "94%"}}, headers=hs).json().get("specs", {}).get("accuracy") == "94%")
check("10 similarity stub", c.post("/uploads/similarity-check", json={}, headers=hs).status_code == 200)
check("10 strikes tracked", isinstance(c.get(f"/users/{s['user']['id']}").json().get("strikes"), int))
check("6 weighted rating", isinstance(c.get(f"/users/{s['user']['id']}").json().get("rating_weighted"), (int, float)))
check("8 push stub", c.post("/notifications/push-token", json={"token": "dev-token"}, headers=hs).status_code == 200)
check("11 health", c.get("/health").json() == {"ok": True})

print(f"\nAUDIT OK: {len(passed)}/{len(passed)} checks passed")
for p in passed:
    print("  [ok]", p)
