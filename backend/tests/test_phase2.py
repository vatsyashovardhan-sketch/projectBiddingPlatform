"""Phase-2 flows: bidding, messaging, reviews, notifications, admin, jobs."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def _signup(email, role="both"):
    r = c.post("/auth/signup", json={"email": email, "password": "pass1234", "name": email.split("@")[0], "role": role})
    assert r.status_code == 200, r.text
    return r.json()


def test_full_phase2():
    s = _signup("s2@test.com", "seller")
    b = _signup("b2@test.com", "buyer")
    hs = {"Authorization": f"Bearer {s['access_token']}"}
    hb = {"Authorization": f"Bearer {b['access_token']}"}

    l = c.post("/listings", json={"title": "Bid Project", "description": "A project open to bids xyz",
                                  "price": 100, "category": "Web App", "tech_stack": ["react"]}, headers=hs)
    assert l.status_code == 200, l.text
    lid = l.json()["id"]

    # bidding
    bid = c.post(f"/listings/{lid}/bids", json={"amount": 80, "message": "offer"}, headers=hb)
    assert bid.status_code == 200, bid.text
    bid_id = bid.json()["id"]
    acc = c.post(f"/bids/{bid_id}/accept", headers=hs)
    assert acc.status_code == 200, acc.text
    oid = acc.json()["order_id"]

    # messaging
    th = c.post("/threads", json={"listing_id": lid}, headers=hb)
    assert th.status_code == 200, th.text
    tid = th.json()["id"]
    m = c.post(f"/threads/{tid}/messages", json={"text": "Is this available?"}, headers=hb)
    assert m.status_code == 200, m.text

    # complete order then review
    c.post(f"/orders/{oid}/mock-pay", headers=hb)
    c.post(f"/orders/{oid}/deliver", headers=hs)
    cf = c.post(f"/orders/{oid}/confirm", headers=hb)
    assert cf.status_code == 200, cf.text
    rv = c.post(f"/orders/{oid}/reviews", json={"rating": 5, "comment": "great"}, headers=hb)
    assert rv.status_code == 200, rv.text
    resp = c.post(f"/reviews/{rv.json()['id']}/respond", json={"response": "thanks!"}, headers=hs)
    assert resp.status_code == 200, resp.text

    # notifications + prefs
    n = c.get("/notifications", headers=hs)
    assert n.status_code == 200 and n.json()["unread"] >= 1

    # related/trending/featured/tags
    assert c.get(f"/listings/{lid}/related").status_code == 200
    assert c.get("/listings/trending").status_code == 200
    assert c.get("/listings/tags").status_code == 200

    # payouts
    p = c.get("/payments/payouts", headers=hs)
    assert p.status_code == 200 and p.json()["total"] > 0

    # follow
    f = c.post(f"/users/{s['user']['id']}/follow", headers=hb)
    assert f.status_code == 200


def test_auth_extras():
    u = _signup("extra@test.com")
    tok = u["verify_token_dev"]
    assert c.post("/auth/verify-email", json={"token": tok}).status_code == 200
    f = c.post("/auth/forgot-password", json={"email": "extra@test.com"})
    assert f.status_code == 200
    rt = f.json()["reset_token_dev"]
    assert c.post("/auth/reset-password", json={"token": rt, "password": "newpass123"}).status_code == 200
    lg = c.post("/auth/login", json={"email": "extra@test.com", "password": "newpass123"})
    assert lg.status_code == 200


def test_jobs_and_reports():
    assert c.get("/listings/categories").status_code == 200
    s = _signup("rep@test.com", "seller")
    hs = {"Authorization": f"Bearer {s['access_token']}"}
    l = c.post("/listings", json={"title": "Report me", "description": "report this project xyz",
                                  "price": 10, "category": "Other"}, headers=hs)
    lid = l.json()["id"]
    assert c.post(f"/listings/{lid}/report", json={"reason": "stolen"}, headers=hs).status_code == 200
