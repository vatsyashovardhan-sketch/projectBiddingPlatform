# """Deterministic seed-data generator: 20 buyers + 40 sellers.

# Each seller gets a social-style storefront: bio/avatar/skills/GitHub,
# 2-4 ongoing (active) projects and 1-3 sold projects with prices.
# Pure data — no DB imports, so both seed.py (API mode) and tests can use it.
# """
# import random

# SEED_PASSWORD = "Seed1234"  # meets validation: 8+ chars, letter + number

# FIRST = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Krishna", "Meera",
#          "Nikhil", "Priya", "Rahul", "Riya", "Rohan", "Sanya", "Shreya", "Varun",
#          "Aditya", "Neha", "Karan", "Pooja", "Vikram", "Simran", "Manav", "Tara",
#          "Dev", "Aisha", "Kabir", "Navya", "Yash", "Zara", "Farhan", "Ira"]
# LAST = ["Sharma", "Verma", "Patel", "Iyer", "Khan", "Gupta", "Mehta", "Nair",
#         "Singh", "Reddy", "Joshi", "Das", "Kulkarni", "Chopra", "Bose", "Menon",
#         "Agarwal", "Rao", "Malhotra", "Pillai", "Desai", "Kaur", "Ghosh", "Pandey"]

# CATALOG = {
#     "Web App": {
#         "titles": ["SaaS Starter Kit", "E-commerce Storefront", "Blog CMS", "Admin Dashboard",
#                    "Real-time Chat App", "Booking System", "Job Board", "Portfolio Template"],
#         "tech": ["react", "nextjs", "nodejs", "tailwind", "typescript"],
#         "base": 79,
#     },
#     "Mobile App": {
#         "titles": ["Fitness Tracker", "Expense Manager", "Food Delivery UI", "Notes App", "Weather App"],
#         "tech": ["flutter", "react-native", "firebase", "sqlite"],
#         "base": 69,
#     },
#     "ML/AI Project": {
#         "titles": ["Sentiment Analyzer", "Image Classifier", "RAG Chatbot", "Recommendation Engine", "Price Predictor"],
#         "tech": ["python", "pytorch", "scikit-learn", "fastapi", "pandas"],
#         "base": 129,
#     },
#     "Final Year Project": {
#         "titles": ["Online Exam System", "Library Management", "Hospital Portal", "Attendance System", "Inventory Manager"],
#         "tech": ["php", "mysql", "react", "nodejs", "mongodb"],
#         "base": 99,
#     },
#     "Game": {
#         "titles": ["2D Platformer", "Snake Game", "Puzzle Game", "Racing Game", "Tower Defense"],
#         "tech": ["unity", "godot", "javascript", "c#", "pygame"],
#         "base": 49,
#     },
#     "Script/Tool": {
#         "titles": ["PDF Merger Tool", "Web Scraper", "Telegram Bot", "CSV Analyzer", "Backup Script"],
#         "tech": ["python", "bash", "selenium", "nodejs"],
#         "base": 29,
#     },
#     "Other": {
#         "titles": ["API Boilerplate", "Auth Microservice", "Chrome Extension", "URL Shortener"],
#         "tech": ["go", "docker", "redis", "postgres"],
#         "base": 39,
#     },
# }

# BIOS = [
#     "CS undergrad selling side projects. Clean code, docs included.",
#     "Full-stack dev. Every project ships with README + setup video.",
#     "ML enthusiast. Final-year projects with report + PPT.",
#     "Freelance web dev. Production-ready templates, quick support.",
#     "Game dev hobbyist. Fun, documented, easy to reskin.",
#     "Backend engineer. APIs with tests and Docker setup.",
# ]

# COMMENTS = [
#     "Exactly as described, setup took 10 minutes.",
#     "Great docs, seller helped on chat. Recommended.",
#     "Good value for money. Code is clean.",
#     "Report + PPT saved my semester. Thanks!",
#     "Minor bugs but seller fixed them fast.",
# ]


# def _names(rng, n):
#     picks = set()
#     while len(picks) < n:
#         picks.add(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
#     return sorted(picks)


# def build(seed: int = 42, n_buyers: int = 20, n_sellers: int = 40) -> dict:
#     rng = random.Random(seed)
#     buyer_names = _names(rng, n_buyers)
#     seller_names = _names(rng, n_sellers)

#     buyers = []
#     for i, name in enumerate(buyer_names):
#         slug = name.lower().replace(" ", ".")
#         buyers.append({
#             "email": f"{slug}.buyer{i}@example.com",
#             "password": SEED_PASSWORD,
#             "name": name,
#             "role": "buyer",
#         })

#     sellers = []
#     used_titles: set[str] = set()
#     cats = list(CATALOG.keys())
#     for i, name in enumerate(seller_names):
#         slug = name.lower().replace(" ", "")
#         handle = f"{slug}{rng.randint(1, 99)}"
#         n_ongoing = rng.randint(2, 4)
#         n_sold = rng.randint(1, 3)
#         ongoing, sold = [], []
#         for k in range(n_ongoing + n_sold):
#             cat = cats[(i + k) % len(cats)]
#             title_base = rng.choice(CATALOG[cat]["titles"])
#             title = title_base
#             suffix = 2
#             while title in used_titles:
#                 title = f"{title_base} v{suffix}"
#                 suffix += 1
#             used_titles.add(title)
#             tech = rng.sample(CATALOG[cat]["tech"], k=min(3, len(CATALOG[cat]["tech"])))
#             price = CATALOG[cat]["base"] + rng.choice([0, 10, 20, 30, 50, 70])
#             lic = rng.choice(["personal", "personal", "resale", "exclusive"])
#             seed_img = abs(hash(title)) % 10000
#             item = {
#                 "title": title,
#                 "description": f"{title} — a complete {cat.lower()} project with source code, "
#                                f"documentation and setup instructions. Built with {', '.join(tech)}.",
#                 "price": float(price),
#                 "category": cat,
#                 "tech_stack": tech,
#                 "images": [f"https://picsum.photos/seed/{seed_img}/640/360"],
#                 "demo_video": "",
#                 "license": lic,
#                 "accept_offers": rng.random() < 0.7,
#                 "status": "active",
#             }
#             (sold if k >= n_ongoing else ongoing).append(item)
#         sellers.append({
#             "email": f"{handle}@example.com",
#             "password": SEED_PASSWORD,
#             "name": name,
#             "role": "seller",
#             "bio": rng.choice(BIOS),
#             "avatar": f"https://api.dicebear.com/9.x/thumbs/svg?seed={handle}",
#             "skills": rng.sample(["react", "python", "nodejs", "flutter", "ml", "unity", "php", "go"], k=rng.randint(2, 4)),
#             "github": handle,
#             "portfolio": [f"https://github.com/{handle}"],
#             "badges": ["developer"] if rng.random() < 0.5 else [],
#             "ongoing": ongoing,
#             "sold": sold,
#         })
#     return {"buyers": buyers, "sellers": sellers,
#             "comments": COMMENTS, "password": SEED_PASSWORD}


"""Deterministic seed-data generator: 20 buyers + 40 sellers.

Each seller gets a social-style storefront: bio/avatar/skills/GitHub,
2-4 ongoing (active) projects and 1-3 sold projects with prices.
Pure data — no DB imports, so both seed.py (API mode) and tests can use it.
"""
import random

SEED_PASSWORD = "Seed1234"  # meets validation: 8+ chars, letter + number

FIRST = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Krishna", "Meera",
         "Nikhil", "Priya", "Rahul", "Riya", "Rohan", "Sanya", "Shreya", "Varun",
         "Aditya", "Neha", "Karan", "Pooja", "Vikram", "Simran", "Manav", "Tara",
         "Dev", "Aisha", "Kabir", "Navya", "Yash", "Zara", "Farhan", "Ira"]
LAST = ["Sharma", "Verma", "Patel", "Iyer", "Khan", "Gupta", "Mehta", "Nair",
        "Singh", "Reddy", "Joshi", "Das", "Kulkarni", "Chopra", "Bose", "Menon",
        "Agarwal", "Rao", "Malhotra", "Pillai", "Desai", "Kaur", "Ghosh", "Pandey"]

CATALOG = {
    "Web App": {
        "titles": ["SaaS Starter Kit", "E-commerce Storefront", "Blog CMS", "Admin Dashboard",
                   "Real-time Chat App", "Booking System", "Job Board", "Portfolio Template"],
        "tech": ["react", "nextjs", "nodejs", "tailwind", "typescript"],
        "base": 79,
    },
    "Mobile App": {
        "titles": ["Fitness Tracker", "Expense Manager", "Food Delivery UI", "Notes App", "Weather App"],
        "tech": ["flutter", "react-native", "firebase", "sqlite"],
        "base": 69,
    },
    "ML/AI Project": {
        "titles": ["Sentiment Analyzer", "Image Classifier", "RAG Chatbot", "Recommendation Engine", "Price Predictor"],
        "tech": ["python", "pytorch", "scikit-learn", "fastapi", "pandas"],
        "base": 129,
    },
    "Final Year Project": {
        "titles": ["Online Exam System", "Library Management", "Hospital Portal", "Attendance System", "Inventory Manager"],
        "tech": ["php", "mysql", "react", "nodejs", "mongodb"],
        "base": 99,
    },
    "Game": {
        "titles": ["2D Platformer", "Snake Game", "Puzzle Game", "Racing Game", "Tower Defense"],
        "tech": ["unity", "godot", "javascript", "c#", "pygame"],
        "base": 49,
    },
    "Script/Tool": {
        "titles": ["PDF Merger Tool", "Web Scraper", "Telegram Bot", "CSV Analyzer", "Backup Script"],
        "tech": ["python", "bash", "selenium", "nodejs"],
        "base": 29,
    },
    "Other": {
        "titles": ["API Boilerplate", "Auth Microservice", "Chrome Extension", "URL Shortener"],
        "tech": ["go", "docker", "redis", "postgres"],
        "base": 39,
    },
}

BIOS = [
    "CS undergrad selling side projects. Clean code, docs included.",
    "Full-stack dev. Every project ships with README + setup video.",
    "ML enthusiast. Final-year projects with report + PPT.",
    "Freelance web dev. Production-ready templates, quick support.",
    "Game dev hobbyist. Fun, documented, easy to reskin.",
    "Backend engineer. APIs with tests and Docker setup.",
]

COMMENTS = [
    "Exactly as described, setup took 10 minutes.",
    "Great docs, seller helped on chat. Recommended.",
    "Good value for money. Code is clean.",
    "Report + PPT saved my semester. Thanks!",
    "Minor bugs but seller fixed them fast.",
]


def _names(rng, n):
    picks = set()
    while len(picks) < n:
        picks.add(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
    return sorted(picks)


def build(seed: int = 42, n_buyers: int = 20, n_sellers: int = 40) -> dict:
    rng = random.Random(seed)
    buyer_names = _names(rng, n_buyers)
    seller_names = _names(rng, n_sellers)

    buyers = []
    for i, name in enumerate(buyer_names):
        slug = name.lower().replace(" ", ".")
        buyers.append({
            "email": f"{slug}.buyer{i}@example.com",
            "password": SEED_PASSWORD,
            "name": name,
            "role": "buyer",
        })

    sellers = []
    used_titles: set[str] = set()
    cats = list(CATALOG.keys())
    for i, name in enumerate(seller_names):
        slug = name.lower().replace(" ", "")
        handle = f"{slug}{rng.randint(1, 99)}"
        n_ongoing = rng.randint(2, 4)
        n_sold = rng.randint(1, 3)
        ongoing, sold = [], []
        for k in range(n_ongoing + n_sold):
            cat = cats[(i + k) % len(cats)]
            title_base = rng.choice(CATALOG[cat]["titles"])
            title = title_base
            suffix = 2
            while title in used_titles:
                title = f"{title_base} v{suffix}"
                suffix += 1
            used_titles.add(title)
            tech = rng.sample(CATALOG[cat]["tech"], k=min(3, len(CATALOG[cat]["tech"])))
            price = CATALOG[cat]["base"] + rng.choice([0, 10, 20, 30, 50, 70])
            lic = rng.choice(["personal", "personal", "resale", "exclusive"])
            seed_img = abs(hash(title)) % 10000
            item = {
                "title": title,
                "description": f"{title} — a complete {cat.lower()} project with source code, "
                               f"documentation and setup instructions. Built with {', '.join(tech)}.",
                "price": float(price),
                "category": cat,
                "tech_stack": tech,
                "images": [f"https://picsum.photos/seed/{seed_img}/640/360"],
                "demo_video": "",
                "license": lic,
                "accept_offers": rng.random() < 0.7,
                "status": "active",
            }
            (sold if k >= n_ongoing else ongoing).append(item)
        sellers.append({
            "email": f"{handle}@example.com",
            "password": SEED_PASSWORD,
            "name": name,
            "role": "seller",
            "bio": rng.choice(BIOS),
            "avatar": f"https://api.dicebear.com/9.x/thumbs/svg?seed={handle}",
            "skills": rng.sample(["react", "python", "nodejs", "flutter", "ml", "unity", "php", "go"], k=rng.randint(2, 4)),
            "github": handle,
            "portfolio": [f"https://github.com/{handle}"],
            "badges": ["developer"] if rng.random() < 0.5 else [],
            "ongoing": ongoing,
            "sold": sold,
        })
    return {"buyers": buyers, "sellers": sellers,
            "comments": COMMENTS, "password": SEED_PASSWORD}
