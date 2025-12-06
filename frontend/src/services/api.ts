import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: {
    indexes: null, // Use ?key=value1&key=value2 format for arrays (FastAPI compatible)
  },
});

export interface SalesTransaction {
  transaction_id: number;
  date: string;
  customer_id: string;
  customer_name: string;
  phone_number: string;
  gender: string;
  age: number;
  customer_region: string;
  customer_type: string;
  product_id: string;
  product_name: string;
  brand: string;
  product_category: string;
  tags: string;
  quantity: number;
  price_per_unit: number;
  discount_percentage: number;
  total_amount: number;
  final_amount: number;
  payment_method: string;
  order_status: string;
  delivery_type: string;
  store_id: string;
  store_location: string;
  salesperson_id: string;
  employee_name: string;
}

export interface SalesResponse {
  transactions: SalesTransaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SummaryStats {
  total_units_sold: number;
  total_amount: number;
  total_discount: number;
  total_sales_records: number;
}

export interface FilterOptions {
  customer_regions: string[];
  genders: string[];
  product_categories: string[];
  payment_methods: string[];
  tags: string[];
}

export interface SalesQueryParams {
  search?: string;
  customer_regions?: string[];
  genders?: string[];
  age_min?: number;
  age_max?: number;
  product_categories?: string[];
  tags?: string[];
  payment_methods?: string[];
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

export const salesAPI = {
  getTransactions: async (params: SalesQueryParams): Promise<SalesResponse> => {
    const response = await api.get<SalesResponse>('/api/sales/transactions', { params });
    return response.data;
  },

  getSummary: async (params: Omit<SalesQueryParams, 'search' | 'sort_by' | 'sort_order' | 'page' | 'page_size'>): Promise<SummaryStats> => {
    const response = await api.get<SummaryStats>('/api/sales/summary', { params });
    return response.data;
  },

  getFilterOptions: async (): Promise<FilterOptions> => {
    const response = await api.get<FilterOptions>('/api/sales/filter-options');
    return response.data;
  },
};

