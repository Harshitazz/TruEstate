from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SalesTransaction(BaseModel):
    transaction_id: int
    date: str
    customer_id: str
    customer_name: str
    phone_number: str
    gender: str
    age: int
    customer_region: str
    customer_type: str
    product_id: str
    product_name: str
    brand: str
    product_category: str
    tags: str
    quantity: int
    price_per_unit: float
    discount_percentage: float
    total_amount: float
    final_amount: float
    payment_method: str
    order_status: str
    delivery_type: str
    store_id: str
    store_location: str
    salesperson_id: str
    employee_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": 1,
                "date": "2023-03-23",
                "customer_id": "CUST-40823",
                "customer_name": "Neha Khan",
                "phone_number": "9720639364",
                "gender": "Male",
                "age": 21,
                "customer_region": "East",
                "customer_type": "Returning",
                "product_id": "PROD-8721",
                "product_name": "Herbal Face Wash",
                "brand": "SilkSkin",
                "product_category": "Beauty",
                "tags": "organic,skincare",
                "quantity": 5,
                "price_per_unit": 4268.0,
                "discount_percentage": 12.0,
                "total_amount": 21340.0,
                "final_amount": 18779.2,
                "payment_method": "UPI",
                "order_status": "Completed",
                "delivery_type": "Standard",
                "store_id": "ST-015",
                "store_location": "Ahmedabad",
                "salesperson_id": "EMP-7554",
                "employee_name": "Harsh Agarwal"
            }
        }

class SalesResponse(BaseModel):
    transactions: list[SalesTransaction]
    total: int
    page: int
    page_size: int
    total_pages: int

class SummaryStats(BaseModel):
    total_units_sold: int
    total_amount: float
    total_discount: float
    total_sales_records: int

