# from pydantic_settings import BaseSettings


# class Settings(BaseSettings):
#     MONGO_URI: str = "mongodb://localhost:27017"
#     MONGO_DB: str = "projectbidding"
#     JWT_SECRET: str = "change-me-to-a-long-random-string"
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7
#     FRONTEND_URL: str = "http://localhost:5173"
#     STRIPE_SECRET_KEY: str = ""
#     STRIPE_WEBHOOK_SECRET: str = ""
#     PLATFORM_FEE_PERCENT: float = 10.0
#     USE_S3: bool = False
#     S3_BUCKET: str = ""
#     AWS_ACCESS_KEY_ID: str = ""
#     AWS_SECRET_ACCESS_KEY: str = ""
#     AWS_REGION: str = "us-east-1"

#     class Config:
#         env_file = ".env"
#         extra = "ignore"


# settings = Settings()

# CATEGORIES = [
#     "Web App",
#     "Mobile App",
#     "ML/AI Project",
#     "Final Year Project",
#     "Game",
#     "Script/Tool",
#     "Other",
# ]

# LISTING_STATUSES = ["draft", "active", "sold", "removed"]
# ORDER_STATUSES = ["pending", "paid", "delivered", "completed", "disputed"]
