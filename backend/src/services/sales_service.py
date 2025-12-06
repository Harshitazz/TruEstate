from typing import Optional, List
import pandas as pd
import numpy as np
import re
from src.config.database import database
from src.models.sales import SalesTransaction, SummaryStats
import math
import logging

logger = logging.getLogger(__name__)

class SalesService:
    def __init__(self):
        if database.df is None:
            raise ValueError("Data not loaded. Make sure CSV data is loaded.")
        self.df: pd.DataFrame = database.df.copy(deep=True)

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

    def _apply_filters(
        self,
        df: pd.DataFrame,
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
    ) -> pd.DataFrame:
        """Apply all filters to the dataframe"""
        self._validate_filters(age_min=age_min, age_max=age_max, date_from=date_from, date_to=date_to)
        
        filtered_df = df.copy(deep=True)
        
        if search and search.strip():
            search_term = search.strip()
            search_lower = search_term.lower()
            search_digits = ''.join(filter(str.isdigit, search_term))
            
            mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            
            text_fields = [
                'customer_name',
                'product_name',
                'employee_name',
                'store_location',
                'brand',
                'customer_type',
                'order_status',
                'delivery_type'
            ]
            
            for field in text_fields:
                if field in filtered_df.columns:
                    field_data = filtered_df[field].fillna('').astype(str)
                    mask |= field_data.str.lower().str.contains(search_lower, na=False, regex=False)
            
            id_fields = [
                'customer_id',
                'product_id',
                'store_id',
                'salesperson_id'
            ]
            
            for field in id_fields:
                if field in filtered_df.columns:
                    field_data = filtered_df[field].fillna('').astype(str)
                    mask |= field_data.str.lower().str.contains(search_lower, na=False, regex=False)
            
            if 'transaction_id' in filtered_df.columns and search_digits:
                transaction_data = filtered_df['transaction_id'].fillna(0).astype(str)
                mask |= transaction_data.str.contains(search_digits, na=False, regex=False)
            
            if 'phone_number' in filtered_df.columns and search_digits:
                phone_data = filtered_df['phone_number'].fillna('').astype(str)
                mask |= phone_data.str.contains(search_digits, na=False, regex=False)
                phone_clean = phone_data.str.replace(r'[^\d]', '', regex=True)
                mask |= phone_clean.str.contains(search_digits, na=False, regex=False)
            
            filtered_df = filtered_df[mask].copy()
            filtered_df.reset_index(drop=True, inplace=True)
            
            logger.info(f"Search '{search_term}' found {len(filtered_df)} results across multiple fields")
        
        customer_regions = self._normalize_string_list(customer_regions, to_lowercase=True)
        if customer_regions:
            region_set = set(customer_regions)
            if 'customer_region' in filtered_df.columns:
                region_data = filtered_df['customer_region'].fillna('')
                region_mask = region_data.isin(region_set)
                filtered_df = filtered_df[region_mask].copy()
                filtered_df.reset_index(drop=True, inplace=True)
        
        genders = self._normalize_string_list(genders, to_lowercase=True)
        if genders:
            gender_set = set(genders)
            if 'gender' in filtered_df.columns:
                gender_data = filtered_df['gender'].fillna('')
                gender_mask = gender_data.isin(gender_set)
                filtered_df = filtered_df[gender_mask].copy()
                filtered_df.reset_index(drop=True, inplace=True)
            logger.info(f"Gender filter applied: {genders}, filtered to {len(filtered_df)} records from {len(df)}")
            unique_genders = filtered_df['gender'].unique()
            logger.debug(f"Unique genders after filter: {unique_genders.tolist()}")
        
        if age_min is not None:
            if 'age' in filtered_df.columns:
                age_data = pd.to_numeric(filtered_df['age'], errors='coerce').fillna(0)
                filtered_df = filtered_df[age_data >= age_min].copy()
        if age_max is not None:
            if 'age' in filtered_df.columns:
                age_data = pd.to_numeric(filtered_df['age'], errors='coerce').fillna(0)
                filtered_df = filtered_df[age_data <= age_max].copy()
        
        product_categories = self._normalize_string_list(product_categories, to_lowercase=True)
        if product_categories:
            category_set = set(product_categories)
            if 'product_category' in filtered_df.columns:
                category_data = filtered_df['product_category'].fillna('')
                category_mask = category_data.isin(category_set)
                filtered_df = filtered_df[category_mask].copy()
                filtered_df.reset_index(drop=True, inplace=True)
        
        tags = self._normalize_string_list(tags, to_lowercase=True)
        if tags:
            if 'tags' in filtered_df.columns:
                tag_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                tags_data = filtered_df['tags'].fillna('').astype(str)
                for tag in tags:
                    if tag:
                        tag_escaped = re.escape(tag)
                        tag_mask |= tags_data.str.contains(
                            f'\\b{tag_escaped}\\b', 
                            case=False, 
                            na=False, 
                            regex=True
                        )
                filtered_df = filtered_df[tag_mask].copy()
                filtered_df.reset_index(drop=True, inplace=True)
        
        payment_methods = self._normalize_string_list(payment_methods, to_lowercase=True)
        if payment_methods:
            payment_set = set(payment_methods)
            if 'payment_method' in filtered_df.columns:
                payment_data = filtered_df['payment_method'].fillna('')
                payment_mask = payment_data.isin(payment_set)
                filtered_df = filtered_df[payment_mask].copy()
                filtered_df.reset_index(drop=True, inplace=True)
            logger.info(f"Payment method filter applied: {payment_methods}, filtered to {len(filtered_df)} records")
            if len(filtered_df) > 0:
                unique_payments = filtered_df['payment_method'].unique()
                logger.debug(f"Unique payment methods after filter: {unique_payments.tolist()}")
        
        if date_from and date_from.strip():
            date_from_clean = date_from.strip()
            if 'date' in filtered_df.columns:
                date_data = filtered_df['date'].fillna('').astype(str)
                filtered_df = filtered_df[date_data >= date_from_clean].copy()
        if date_to and date_to.strip():
            date_to_clean = date_to.strip()
            if 'date' in filtered_df.columns:
                date_data = filtered_df['date'].fillna('').astype(str)
                filtered_df = filtered_df[date_data <= date_to_clean].copy()
        
        if len(filtered_df) == 0:
            logger.info("No results found after applying filters")
            return pd.DataFrame(columns=df.columns)
        
        return filtered_df

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
        
        initial_count = len(self.df)
        logger.debug(f"Starting with {initial_count} records, filters: genders={genders}")
        
        filtered_df = self._apply_filters(
            self.df,
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
        
        filtered_count = len(filtered_df)
        logger.debug(f"After filters: {filtered_count} records (from {initial_count})")
        
        total = len(filtered_df)
        
        sort_field_map = {
            "date": "date",
            "quantity": "quantity",
            "customer_name": "customer_name"
        }
        sort_field = sort_field_map.get(sort_by, "date")
        ascending = sort_order == "asc"
        
        logger.info(f"Sorting by: {sort_field}, order: {sort_order} (ascending: {ascending})")
        
        if sort_field == "date":
            filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending, na_position='last', kind='mergesort')
        elif sort_field == "quantity":
            filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending, na_position='last', kind='mergesort')
        elif sort_field == "customer_name":
            filtered_df = filtered_df.copy()
            filtered_df['_sort_key'] = filtered_df[sort_field].astype(str).str.lower()
            filtered_df = filtered_df.sort_values(by='_sort_key', ascending=ascending, na_position='last', kind='mergesort')
            filtered_df = filtered_df.drop(columns=['_sort_key'])
        else:
            filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending, na_position='last', kind='mergesort')
        
        filtered_df = filtered_df.reset_index(drop=True)
        
        if len(filtered_df) > 0:
            sample_values = filtered_df[sort_field].head(5).tolist()
            logger.info(f"After sorting by {sort_field} ({'asc' if ascending else 'desc'}), first 5 values: {sample_values}")
        else:
            logger.info(f"After sorting by {sort_field}, no records found")
        
        skip = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        if skip >= total:
            paginated_df = pd.DataFrame()
        else:
            paginated_df = filtered_df.iloc[skip:skip + page_size].copy()
        
        if len(paginated_df) > 0:
            paginated_values = paginated_df[sort_field].head(3).tolist()
            logger.info(f"Paginated results (page {page}), first 3 {sort_field} values: {paginated_values}")
        
        result = []
        if genders and len(paginated_df) > 0:
            unique_genders_in_result = paginated_df['gender'].unique()
            expected_genders = self._normalize_string_list(genders, to_lowercase=True)
            if expected_genders:
                expected_set = set(expected_genders)
                actual_set = {str(g).lower().strip() for g in unique_genders_in_result}
                unexpected = actual_set - expected_set
                if unexpected:
                    logger.error(f"FILTER ERROR: Found unexpected genders {unexpected} in paginated results! Expected: {expected_set}, Got: {actual_set}")
                    paginated_df = paginated_df[paginated_df['gender'].isin(expected_set)].copy()
                    logger.warning(f"Re-filtered paginated results, now have {len(paginated_df)} records")
        
        def to_title_case(s):
            """Convert string to title case for display"""
            if not s or pd.isna(s):
                return s
            s_str = str(s).strip()
            if not s_str:
                return s_str
            return s_str[0].upper() + s_str[1:].lower() if len(s_str) > 1 else s_str.upper()
        
        for _, row in paginated_df.iterrows():
            try:
                transaction_dict = row.to_dict()
                if 'gender' in transaction_dict:
                    transaction_dict['gender'] = to_title_case(transaction_dict['gender'])
                if 'customer_region' in transaction_dict:
                    transaction_dict['customer_region'] = to_title_case(transaction_dict['customer_region'])
                if 'product_category' in transaction_dict:
                    transaction_dict['product_category'] = to_title_case(transaction_dict['product_category'])
                if 'payment_method' in transaction_dict:
                    transaction_dict['payment_method'] = to_title_case(transaction_dict['payment_method'])
                if 'tags' in transaction_dict and transaction_dict['tags']:
                    tags_list = [to_title_case(t.strip()) for t in str(transaction_dict['tags']).split(',') if t.strip()]
                    transaction_dict['tags'] = ','.join(tags_list)
                result.append(SalesTransaction(**transaction_dict))
            except Exception as e:
                logger.warning(f"Error converting transaction {transaction_dict.get('transaction_id', 'unknown')}: {str(e)}")
                continue
        
        return {
            "transactions": result,
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
        
        filtered_df = self._apply_filters(
            self.df,
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
        
        if len(filtered_df) == 0:
            return SummaryStats(
                total_units_sold=0,
                total_amount=0.0,
                total_discount=0.0,
                total_sales_records=0
            )
        
        total_units_sold = int(filtered_df['quantity'].sum())
        total_amount = float(filtered_df['total_amount'].sum())
        total_discount = float((filtered_df['total_amount'] - filtered_df['final_amount']).sum())
        total_sales_records = len(filtered_df)
        
        return SummaryStats(
            total_units_sold=total_units_sold,
            total_amount=total_amount,
            total_discount=total_discount,
            total_sales_records=total_sales_records
            )
    
    async def get_filter_options(self) -> dict:
        """Get all unique filter options for dropdowns"""
        df = self.df
        
        customer_regions = sorted([
            str(v).strip() for v in df['customer_region'].dropna().unique() 
            if pd.notna(v) and str(v).strip()
        ])
        
        genders = sorted([
            str(v).strip() for v in df['gender'].dropna().unique() 
            if pd.notna(v) and str(v).strip()
        ])
        
        product_categories = sorted([
            str(v).strip() for v in df['product_category'].dropna().unique() 
            if pd.notna(v) and str(v).strip()
        ])
        
        payment_methods = sorted([
            str(v).strip() for v in df['payment_method'].dropna().unique() 
            if pd.notna(v) and str(v).strip()
        ])
        
        all_tags = set()
        for tag_string in df['tags'].dropna():
            if tag_string and pd.notna(tag_string):
                tag_list = [t.strip() for t in str(tag_string).split(",") if t.strip()]
                all_tags.update(tag_list)
        
        def to_title_case(s):
            """Convert string to title case for display"""
            if not s or pd.isna(s):
                return s
            s_str = str(s).strip()
            if not s_str:
                return s_str
            return s_str[0].upper() + s_str[1:].lower() if len(s_str) > 1 else s_str.upper()
        
        return {
            "customer_regions": [to_title_case(r) for r in customer_regions],
            "genders": [to_title_case(g) for g in genders],
            "product_categories": [to_title_case(c) for c in product_categories],
            "payment_methods": [to_title_case(p) for p in payment_methods],
            "tags": sorted([to_title_case(t) for t in all_tags])
        }
