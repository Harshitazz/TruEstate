import pandas as pd
import os
import pathlib
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    df: Optional[pd.DataFrame] = None

database = Database()

def load_csv_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load CSV data into memory"""
    if csv_path is None:
        project_root = pathlib.Path(__file__).parent.parent.parent.parent
        csv_path = project_root / "truestate_assignment_dataset.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    logger.info(f"Loading CSV data from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    
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
    
    logger.info(f"Loaded {len(df)} records from CSV")
    return df

async def connect_to_mongo():
    """Load CSV data into memory (replaces MongoDB connection)"""
    try:
        database.df = load_csv_data()
        logger.info(f"Data loaded successfully. Total records: {len(database.df)}")
    except Exception as e:
        logger.error(f"Failed to load CSV data: {str(e)}", exc_info=True)
        raise

async def close_mongo_connection():
    """Clear in-memory data"""
    database.df = None
    logger.info("Data cleared from memory")
