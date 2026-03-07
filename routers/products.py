# routers/products.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorCollection
from database import get_products_collection
from model import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[Product])
async def get_all_products(collection: AsyncIOMotorCollection = Depends(get_products_collection)):
    cursor = collection.find({})
    products = await cursor.to_list(length=1000)  # adjust limit as needed
    return products

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str, collection: AsyncIOMotorCollection = Depends(get_products_collection)):
    product = await collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product