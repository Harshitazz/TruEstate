from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.database import connect_to_mongo, close_mongo_connection
from src.routes import sales
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sales Management API", version="1.0.0")

origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales.router)

@app.on_event("startup")
async def startup_event():
    try:
        await connect_to_mongo()
        logger.info("Application startup complete - MongoDB connected")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Sales Management API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

