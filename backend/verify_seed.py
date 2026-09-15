"""Quick check of seeded storefront data. Usage: python verify_seed.py --api http://localhost:8001"""
import argparse
import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--api", default="http://localhost:8000")
a = ap.parse_args()
c = httpx.Client(base_url=a.api.rstrip("/"), timeout=30)

sellers = c.get("/users/sellers/top?limit=50").json()
print("top_sellers:", len(sellers))
s0 = sellers[0]
print("top:", s0["name"], "| ongoing:", s0["ongoing_count"], "| sold:", s0["sold_count"],
      "| followers:", s0["followers"], "| rating:", s0["rating"])
p = c.get("/users/" + s0["id"]).json()
print("profile:", p["name"], "| ongoing_projects:", len(p["ongoing_projects"]),
      "| sold_projects:", len(p["sold_projects"]), "| earned:", p["total_earned"])
print("sold sample:", [(t["title"], t["price"]) for t in p["sold_projects"][:2]])
print("ongoing sample:", [(t["title"], t["price"]) for t in p["ongoing_projects"][:2]])
print("browse active total:", c.get("/listings?limit=1").json()["total"])
assert len(sellers) == 40, len(sellers)
assert p["sold_count"] > 0 and p["ongoing_count"] > 0
print("SEED VERIFY OK")
