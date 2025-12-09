"""
Script to migrate CSV data to MongoDB
Usage: python -m scripts.migrate_to_mongodb
"""

import sys
import os
import pathlib
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv(
    "MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DATABASE")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

def process_csv_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Process CSV data with the same transformations used in the application
    """
    if csv_path is None:
        csv_path = project_root / "truestate_assignment_dataset.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    logger.info(f"Loading CSV data from: {csv_path}")
    
    # Read CSV in chunks to handle large files
    chunk_size = 10000
    chunks = []
    
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        chunk.columns = chunk.columns.str.lower().str.replace(" ", "_")
        chunks.append(chunk)
        logger.info(f"Loaded chunk of {len(chunk)} records...")
    
    df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Total records loaded: {len(df)}")
    
    df['transaction_id'] = pd.to_numeric(df['transaction_id'], errors='coerce').fillna(0).astype(int)
    df['date'] = df['date'].astype(str).str.strip()
    df['customer_id'] = df['customer_id'].astype(str).str.strip()
    df['customer_name'] = df['customer_name'].astype(str).str.strip()
    df['phone_number'] = df['phone_number'].astype(str).str.strip()
    df['gender'] = df['gender'].astype(str).str.strip().str.lower()
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)
    df['customer_region'] = df['customer_region'].astype(str).str.strip().str.lower()
    df['customer_type'] = df['customer_type'].astype(str).str.strip()
    df['product_id'] = df['product_id'].astype(str).str.strip()
    df['product_name'] = df['product_name'].astype(str).str.strip()
    df['brand'] = df['brand'].astype(str).str.strip()
    df['product_category'] = df['product_category'].astype(str).str.strip().str.lower()
    df['tags'] = df['tags'].astype(str).str.strip().str.lower()
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    df['price_per_unit'] = pd.to_numeric(df['price_per_unit'], errors='coerce').fillna(0.0).astype(float)
    df['discount_percentage'] = pd.to_numeric(df['discount_percentage'], errors='coerce').fillna(0.0).astype(float)
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0.0).astype(float)
    df['final_amount'] = pd.to_numeric(df['final_amount'], errors='coerce').fillna(0.0).astype(float)
    df['payment_method'] = df['payment_method'].astype(str).str.strip().str.lower()
    df['order_status'] = df['order_status'].astype(str).str.strip()
    df['delivery_type'] = df['delivery_type'].astype(str).str.strip()
    df['store_id'] = df['store_id'].astype(str).str.strip()
    df['store_location'] = df['store_location'].astype(str).str.strip()
    df['salesperson_id'] = df['salesperson_id'].astype(str).str.strip()
    df['employee_name'] = df['employee_name'].astype(str).str.strip()
    
    df = df.fillna({
        'tags': '',
        'customer_type': '',
        'brand': '',
        'date': '',
        'customer_name': '',
        'phone_number': '',
        'gender': '',
        'customer_region': '',
        'product_category': '',
        'payment_method': ''
    })
    
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].replace('nan', '', regex=False)
        df[col] = df[col].replace('NaN', '', regex=False)
    
    logger.info(f"Processed {len(df)} records from CSV")
    return df

def migrate_to_mongodb():
    """
    Migrate CSV data to MongoDB
    """
    try:
        logger.info(f"Connecting to MongoDB...")
        client = MongoClient(MONGO_URI)
        
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        df = process_csv_data()
        
        logger.info("Converting DataFrame to documents...")
        records = df.to_dict('records')
        
        logger.info(f"Clearing existing collection '{COLLECTION_NAME}'...")
        collection.delete_many({})
        
        batch_size = 1000
        total_records = len(records)
        inserted_count = 0
        
        logger.info(f"Inserting {total_records} records in batches of {batch_size}...")
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            try:
                result = collection.insert_many(batch, ordered=False)
                inserted_count += len(result.inserted_ids)
                logger.info(f"Inserted batch {i // batch_size + 1}: {len(result.inserted_ids)} records "
                          f"(Total: {inserted_count}/{total_records})")
            except BulkWriteError as e:
                inserted_count += e.details.get('nInserted', 0)
                logger.warning(f"Batch {i // batch_size + 1} had some errors: {e.details.get('writeErrors', [])}")
                logger.info(f"Inserted {e.details.get('nInserted', 0)} records from this batch "
                          f"(Total: {inserted_count}/{total_records})")
        
        logger.info("Creating indexes...")
        collection.create_index("transaction_id", unique=True)
        collection.create_index("customer_id")
        collection.create_index("product_id")
        collection.create_index("date")
        collection.create_index("store_id")
        logger.info("Indexes created successfully")
        
        count = collection.count_documents({})
        logger.info(f"Migration completed! Total records in database: {count}")
        
        client.close()
        logger.info("MongoDB connection closed")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting CSV to MongoDB migration...")
    success = migrate_to_mongodb()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)

