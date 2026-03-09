# main.py
from config.logging_config import setup_logging
setup_logging()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import products, web_search_agent, product_recommender
from config.database import connect_db, close_db
from product_recommender_agent.tools import init_keywords_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await init_keywords_cache()

    yield
    await close_db()


app = FastAPI(title="BeautyMart API", lifespan=lifespan)

# Allow frontend to connect (update origins later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # change to your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(web_search_agent.router)
app.include_router(product_recommender.router)


@app.get("/")
def read_root():
    return {"message": "SalesAgent API is running"}