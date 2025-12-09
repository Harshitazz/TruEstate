from typing import Optional, List
import re
import math
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from src.config.database import get_collection
from src.models.sales import SalesTransaction, SummaryStats
import logging

logger = logging.getLogger(__name__)

class SalesService:
    def __init__(self):
        self.collection: Collection = get_collection()

    def _normalize_string_list(self, value_list: Optional[List[str]], to_lowercase: bool = True) -> Optional[List[str]]:
        """Normalize string list by stripping whitespace, converting to lowercase, and filtering empty values"""
        if value_list is None:
            return None
        if not isinstance(value_list, list):
            return None
        if len(value_list) == 0:
            return None
        normalized = [str(v).strip().lower() if to_lowercase else str(v).strip() 
                     for v in value_list if v is not None and str(v).strip()]
        return normalized if normalized else None

    def _validate_filters(
        self,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> None:
        """Validate filter parameters for conflicts and invalid ranges"""
        if age_min is not None:
            if age_min < 0 or age_min > 150:
                raise ValueError(f"Invalid age_min: {age_min}. Must be between 0 and 150.")
        
        if age_max is not None:
            if age_max < 0 or age_max > 150:
                raise ValueError(f"Invalid age_max: {age_max}. Must be between 0 and 150.")
        
        if age_min is not None and age_max is not None:
            if age_min > age_max:
                raise ValueError(f"Conflicting age range: age_min ({age_min}) cannot be greater than age_max ({age_max})")
        
        if date_from and date_to:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from.strip(), '%Y-%m-%d')
                date_to_obj = datetime.strptime(date_to.strip(), '%Y-%m-%d')
                if date_from_obj > date_to_obj:
                    raise ValueError(f"Conflicting date range: date_from ({date_from}) cannot be after date_to ({date_to})")
            except ValueError as e:
                if "Conflicting date range" in str(e):
                    raise
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD format.")

    def _build_query(
        self,
        search: Optional[str] = None,
        customer_regions: Optional[List[str]] = None,
        genders: Optional[List[str]] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        product_categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        payment_methods: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """Build MongoDB query from filters"""
        self._validate_filters(age_min=age_min, age_max=age_max, date_from=date_from, date_to=date_to)
        
        query = {}
        
        if search and search.strip():
            search_term = search.strip()
            search_lower = search_term.lower()
            search_digits = ''.join(filter(str.isdigit, search_term))
            
            search_conditions = []
            
            text_fields = [
                'customer_name', 'product_name', 'employee_name', 'store_location',
                'brand', 'customer_type', 'order_status', 'delivery_type'
            ]
            for field in text_fields:
                search_conditions.append({field: {'$regex': re.escape(search_lower), '$options': 'i'}})
            
            id_fields = ['customer_id', 'product_id', 'store_id', 'salesperson_id']
            for field in id_fields:
                search_conditions.append({field: {'$regex': re.escape(search_lower), '$options': 'i'}})
            
            if search_digits:
                try:
                    transaction_id = int(search_digits)
                    search_conditions.append({'transaction_id': transaction_id})
                except ValueError:
                    pass
            
            if search_digits:
                search_conditions.append({'phone_number': {'$regex': re.escape(search_digits), '$options': 'i'}})
            
            if search_conditions:
                query['$or'] = search_conditions
        
        customer_regions = self._normalize_string_list(customer_regions, to_lowercase=True)
        if customer_regions:
            query['customer_region'] = {'$in': customer_regions}
        
        genders = self._normalize_string_list(genders, to_lowercase=True)
        if genders:
            query['gender'] = {'$in': genders}
        
        if age_min is not None or age_max is not None:
            age_query = {}
            if age_min is not None:
                age_query['$gte'] = age_min
            if age_max is not None:
                age_query['$lte'] = age_max
            query['age'] = age_query
        
        product_categories = self._normalize_string_list(product_categories, to_lowercase=True)
        if product_categories:
            query['product_category'] = {'$in': product_categories}
        
        tags = self._normalize_string_list(tags, to_lowercase=True)
        if tags:
            tag_conditions = [{'tags': {'$regex': f'\\b{re.escape(tag)}\\b', '$options': 'i'}} for tag in tags]
            if '$or' in query:
                search_or = query.pop('$or')
                query['$and'] = query.get('$and', []) + [
                    {'$or': search_or},
                    {'$or': tag_conditions}
                ]
            else:
                query['$or'] = tag_conditions
        
        payment_methods = self._normalize_string_list(payment_methods, to_lowercase=True)
        if payment_methods:
            query['payment_method'] = {'$in': payment_methods}
        
        if date_from and date_from.strip() or date_to and date_to.strip():
            date_query = {}
            if date_from and date_from.strip():
                date_query['$gte'] = date_from.strip()
            if date_to and date_to.strip():
                date_query['$lte'] = date_to.strip()
            query['date'] = date_query
        
        return query

    def _build_sort(self, sort_by: str = "date", sort_order: str = "desc") -> List[tuple]:
        """Build MongoDB sort specification"""
        sort_field_map = {
            "date": "date",
            "quantity": "quantity",
            "customer_name": "customer_name"
        }
        sort_field = sort_field_map.get(sort_by, "date")
        sort_direction = ASCENDING if sort_order == "asc" else DESCENDING
        return [(sort_field, sort_direction)]

    def _convert_to_transaction(self, doc: dict) -> SalesTransaction:
        """Convert MongoDB document to SalesTransaction model"""
        doc.pop('_id', None)
        
        def to_title_case(s):
            if not s:
                return s
            s_str = str(s).strip()
            if not s_str:
                return s_str
            return s_str[0].upper() + s_str[1:].lower() if len(s_str) > 1 else s_str.upper()
        
        if 'gender' in doc:
            doc['gender'] = to_title_case(doc['gender'])
        if 'customer_region' in doc:
            doc['customer_region'] = to_title_case(doc['customer_region'])
        if 'product_category' in doc:
            doc['product_category'] = to_title_case(doc['product_category'])
        if 'payment_method' in doc:
            doc['payment_method'] = to_title_case(doc['payment_method'])
        if 'tags' in doc and doc['tags']:
            tags_list = [to_title_case(t.strip()) for t in str(doc['tags']).split(',') if t.strip()]
            doc['tags'] = ','.join(tags_list)
        
        return SalesTransaction(**doc)

    async def get_transactions(
        self,
        search: Optional[str] = None,
        customer_regions: Optional[List[str]] = None,
        genders: Optional[List[str]] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        product_categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        payment_methods: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """Get transactions with search, filter, sort, and pagination"""
        
        query = self._build_query(
            search=search,
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
        
        sort_spec = self._build_sort(sort_by=sort_by, sort_order=sort_order)
        
        total = self.collection.count_documents(query)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        skip = (page - 1) * page_size
        
        cursor = self.collection.find(query).sort(sort_spec).skip(skip).limit(page_size)
        documents = list(cursor)
        
        transactions = []
        for doc in documents:
            try:
                transaction = self._convert_to_transaction(doc)
                transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Error converting document: {str(e)}")
                continue
        
        return {
            "transactions": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def get_summary_stats(
        self,
        customer_regions: Optional[List[str]] = None,
        genders: Optional[List[str]] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        product_categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        payment_methods: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SummaryStats:
        """Get summary statistics based on current filters"""
        
        query = self._build_query(
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
        
        pipeline = [
            {'$match': query},
            {
                '$group': {
                    '_id': None,
                    'total_units_sold': {'$sum': '$quantity'},
                    'total_amount': {'$sum': '$total_amount'},
                    'total_final_amount': {'$sum': '$final_amount'},
                    'total_sales_records': {'$sum': 1}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        if not result:
            return SummaryStats(
                total_units_sold=0,
                total_amount=0.0,
                total_discount=0.0,
                total_sales_records=0
            )
        
        stats = result[0]
        total_discount = stats['total_amount'] - stats['total_final_amount']
        
        return SummaryStats(
            total_units_sold=int(stats['total_units_sold']),
            total_amount=float(stats['total_amount']),
            total_discount=float(total_discount),
            total_sales_records=int(stats['total_sales_records'])
        )
    
    async def get_filter_options(self) -> dict:
        """Get all unique filter options for dropdowns"""
        
        def to_title_case(s):
            if not s:
                return s
            s_str = str(s).strip()
            if not s_str:
                return s_str
            return s_str[0].upper() + s_str[1:].lower() if len(s_str) > 1 else s_str.upper()
        
        customer_regions = sorted([
            to_title_case(val)
            for val in self.collection.distinct('customer_region')
            if val
        ])
        
        genders = sorted([
            to_title_case(val)
            for val in self.collection.distinct('gender')
            if val
        ])
        
        product_categories = sorted([
            to_title_case(val)
            for val in self.collection.distinct('product_category')
            if val
        ])
        
        payment_methods = sorted([
            to_title_case(val)
            for val in self.collection.distinct('payment_method')
            if val
        ])
        
        tags_set = set()
        pipeline = [
            {'$project': {'tags': 1}},
            {'$match': {'tags': {'$ne': '', '$exists': True}}}
        ]
        for doc in self.collection.aggregate(pipeline):
            if doc.get('tags'):
                tag_list = [t.strip() for t in str(doc['tags']).split(',') if t.strip()]
                tags_set.update(tag_list)
        
        tags = sorted([to_title_case(t) for t in tags_set])
        
        return {
            "customer_regions": customer_regions,
            "genders": genders,
            "product_categories": product_categories,
            "payment_methods": payment_methods,
            "tags": tags
        }
