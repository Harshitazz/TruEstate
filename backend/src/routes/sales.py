from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from src.services.sales_service import SalesService
from src.models.sales import SalesResponse, SummaryStats
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales", tags=["sales"])

@router.get("/transactions", response_model=SalesResponse)
async def get_transactions(
    search: Optional[str] = Query(None, description="Search across multiple fields: name, phone, transaction ID, customer ID, product ID, employee name, etc."),
    customer_regions: Optional[List[str]] = Query(None, description="Filter by customer regions"),
    genders: Optional[List[str]] = Query(None, description="Filter by genders"),
    age_min: Optional[int] = Query(None, description="Minimum age"),
    age_max: Optional[int] = Query(None, description="Maximum age"),
    product_categories: Optional[List[str]] = Query(None, description="Filter by product categories"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    payment_methods: Optional[List[str]] = Query(None, description="Filter by payment methods"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("date", description="Sort field: date, quantity, or customer_name"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """Get sales transactions with search, filter, sort, and pagination"""
    try:
        if age_min is not None and (age_min < 0 or age_min > 150):
            raise HTTPException(status_code=400, detail=f"Invalid age_min: {age_min}. Must be between 0 and 150.")
        if age_max is not None and (age_max < 0 or age_max > 150):
            raise HTTPException(status_code=400, detail=f"Invalid age_max: {age_max}. Must be between 0 and 150.")
        if age_min is not None and age_max is not None and age_min > age_max:
            raise HTTPException(status_code=400, detail=f"Conflicting age range: age_min ({age_min}) cannot be greater than age_max ({age_max})")
        
        customer_regions = customer_regions if customer_regions and len(customer_regions) > 0 else None
        genders = genders if genders and len(genders) > 0 else None
        product_categories = product_categories if product_categories and len(product_categories) > 0 else None
        tags = tags if tags and len(tags) > 0 else None
        payment_methods = payment_methods if payment_methods and len(payment_methods) > 0 else None
        
        logger.info(f"Received filters - genders: {genders}, customer_regions: {customer_regions}, product_categories: {product_categories}")
        logger.info(f"Received sort params - sort_by: {sort_by}, sort_order: {sort_order}")
        service = SalesService()
        result = await service.get_transactions(
            search=search,
            customer_regions=customer_regions,
            genders=genders,
            age_min=age_min,
            age_max=age_max,
            product_categories=product_categories,
            tags=tags,
            payment_methods=payment_methods,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        logger.info(f"Returning {len(result['transactions'])} transactions out of {result['total']} total")
        return result
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/summary", response_model=SummaryStats)
async def get_summary(
    customer_regions: Optional[List[str]] = Query(None),
    genders: Optional[List[str]] = Query(None),
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    product_categories: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    payment_methods: Optional[List[str]] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Get summary statistics based on current filters"""
    try:
        customer_regions = customer_regions if customer_regions and len(customer_regions) > 0 else None
        genders = genders if genders and len(genders) > 0 else None
        product_categories = product_categories if product_categories and len(product_categories) > 0 else None
        tags = tags if tags and len(tags) > 0 else None
        payment_methods = payment_methods if payment_methods and len(payment_methods) > 0 else None
        
        service = SalesService()
        return await service.get_summary_stats(
            customer_regions=customer_regions,
            genders=genders,
            age_min=age_min,
            age_max=age_max,
            product_categories=product_categories,
            tags=tags,
            payment_methods=payment_methods,
            date_from=date_from,
            date_to=date_to
        )
    except Exception as e:
        logger.error(f"Error fetching summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/filter-options")
async def get_filter_options():
    """Get all available filter options"""
    try:
        service = SalesService()
        return await service.get_filter_options()
    except Exception as e:
        logger.error(f"Error fetching filter options: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

