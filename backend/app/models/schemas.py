from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

Role = Literal["buyer", "seller", "both", "admin"]
ListingStatus = Literal["draft", "active", "sold", "removed"]


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=80)
    role: Role = "both"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    bio: str = ""
    avatar: str = ""
    stripe_account_id: str = ""


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[Role] = None
    skills: Optional[list[str]] = None
    github: Optional[str] = None
    portfolio: Optional[list[str]] = None
    interests: Optional[list[str]] = None


class PriceTier(BaseModel):
    name: str
    price: float
    description: str = ""


class ListingIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10)
    price: float = Field(gt=0)
    category: str
    tech_stack: list[str] = []
    images: list[str] = []
    project_file: str = ""
    file_hash: str = ""
    status: ListingStatus = "active"
    demo_video: str = ""
    pricing_tiers: list[PriceTier] = []
    license: str = "personal"
    accept_offers: bool = True
    specs: dict = {}


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    images: Optional[list[str]] = None
    project_file: Optional[str] = None
    file_hash: Optional[str] = None
    status: Optional[ListingStatus] = None
    demo_video: Optional[str] = None
    pricing_tiers: Optional[list[PriceTier]] = None
    license: Optional[str] = None
    accept_offers: Optional[bool] = None
    featured: Optional[bool] = None
    specs: Optional[dict] = None


class OrderOut(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    amount: float
    fee: float
    status: str
    client_secret: str = ""
    download_token: str = ""
