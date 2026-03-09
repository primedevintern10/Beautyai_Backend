# routers/products.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorCollection
from config.database import get_products_collection
from model import Product
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[Product])
async def get_all_products(collection: AsyncIOMotorCollection = Depends(get_products_collection)):
    cursor = collection.find({})
    products = await cursor.to_list(length=1000) 
    return products

@router.get("/unique-values")
async def get_unique_values(collection: AsyncIOMotorCollection = Depends(get_products_collection)):
    

    unique_values = defaultdict(set)

    async for doc in collection.find({}):
        for key, value in doc.items():
            if isinstance(value, list):
                for item in value:
                    try:
                        unique_values[key].add(item)
                    except TypeError:
                        unique_values[key].add(str(item))
            else:
                try:
                    unique_values[key].add(value)
                except TypeError:
                    unique_values[key].add(str(value))

    return {
        key: sorted([str(v) for v in values])
        for key, values in unique_values.items()
    }


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str, collection: AsyncIOMotorCollection = Depends(get_products_collection)):
    product = await collection.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product