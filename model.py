# models.py
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

class Review(BaseModel):
    review_id: str
    rating: float
    comment: str
    reviewer_name: str
    createdAt: datetime

class Product(BaseModel):
    id: str
    name: str
    brand: str
    description: str
    howToUse: str
    imageUrl: str
    category: str
    subcategory: str
    routineStep: str
    price: float
    skin_types: Optional[List[str]] = None
    hair_types: Optional[List[str]] = None
    concerns: List[str]
    ingredients: List[str]
    exclusions: List[str]
    texture: str
    averageRating: float
    reviewCount: int
    trendingScore: int
    purchaseCount: int
    reviews: List[Review]
    isActive: bool
    isBestseller: bool
    stockStatus: str
    listedAt: datetime
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True  # allows mapping from MongoDB dict