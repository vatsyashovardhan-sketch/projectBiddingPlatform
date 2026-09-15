"""Live demo: seller project deletion (clean delete + live-order guard)."""
import httpx

B = "http://localhost:8000"
c = httpx.Client(base_url=B, timeout=20)


def signup(email, role):
    r = c.post("/auth/signup", json={"email": email, "password": "Pass1234", "name": email.split("@")[0], "role": role})
    if "already registered" in r.text:
        r = c.post("/auth/login", json={"email": email, "password": "Pass1234"})
    return r.json()


s = signup("demo-seller@test.com", "seller")
b = signup("demo-buyer@test.com", "buyer")
hs = {"Authorization": "Bearer " + s["access_token"]}
hb = {"Authorization": "Bearer " + b["access_token"]}

mk = lambda title: c.post("/listings", json={"title": title, "description": "demo delete flow project",
                                             "price": 25, "category": "Other"}, headers=hs).json()

# 1. clean delete
a = mk("Demo Delete Clean Project")
r = c.delete(f"/listings/{a['id']}", headers=hs)
print("1. clean delete:", r.status_code, r.json())
print("   status now:", c.get(f"/listings/{a['id']}").json()["status"])
print("   in browse:", any(x["id"] == a["id"] for x in c.get("/listings?q=Demo+Delete+Clean&limit=50").json()["items"]))

# 2. delete blocked with live order
d = mk("Demo Delete Guarded Project")
o = c.post("/orders", json={"listing_id": d["id"]}, headers=hb).json()
r = c.delete(f"/listings/{d['id']}", headers=hs)
print("2. delete w/ pending order:", r.status_code, "-", r.json().get("detail"))

# 3. after fulfilment, delete allowed
c.post(f"/orders/{o['id']}/mock-pay", headers=hb)
c.post(f"/orders/{o['id']}/deliver", headers=hs)
c.post(f"/orders/{o['id']}/confirm", headers=hb)
r = c.delete(f"/listings/{d['id']}", headers=hs)
print("3. delete after completed:", r.status_code, r.json())
print("DEMO OK")
