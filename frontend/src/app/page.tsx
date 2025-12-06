'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import SummaryCards from '@/components/SummaryCards';
import Filters, { FilterState } from '@/components/Filters';
import SalesTable from '@/components/SalesTable';
import Pagination from '@/components/Pagination';
import { salesAPI, SalesTransaction, SummaryStats, FilterOptions } from '@/services/api';

export default function Home() {
  const [transactions, setTransactions] = useState<SalesTransaction[]>([]);
  const [summary, setSummary] = useState<SummaryStats>({
    total_units_sold: 0,
    total_amount: 0,
    total_discount: 0,
    total_sales_records: 0,
  });
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    customer_regions: [],
    genders: [],
    product_categories: [],
    payment_methods: [],
    tags: [],
  });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    customer_regions: [],
    genders: [],
    age_range: '',
    product_categories: [],
    tags: [],
    payment_methods: [],
    date_range: '',
  });
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [sortDropdownOpen, setSortDropdownOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [showFullView, setShowFullView] = useState(false);

  const pageSize = 10;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {
        page: currentPage,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      
      console.log('Fetching with sort params:', { sort_by: sortBy, sort_order: sortOrder });

      const buildFilterParams = () => {
        const filterParams: any = {};
        if (filters.customer_regions.length > 0) {
          filterParams.customer_regions = filters.customer_regions.map(r => r.toLowerCase());
        }
        if (filters.genders.length > 0) {
          filterParams.genders = filters.genders.map(g => g.toLowerCase());
        }
        if (filters.age_range) {
          const [min, max] = filters.age_range.split('-');
          if (max) {
            const ageMin = parseInt(min, 10);
            const ageMax = parseInt(max, 10);
            if (!isNaN(ageMin) && !isNaN(ageMax) && ageMin >= 0 && ageMax <= 150 && ageMin <= ageMax) {
              filterParams.age_min = ageMin;
              filterParams.age_max = ageMax;
            }
          } else if (min.endsWith('+')) {
            const ageMin = parseInt(min.replace('+', ''), 10);
            if (!isNaN(ageMin) && ageMin >= 0 && ageMin <= 150) {
              filterParams.age_min = ageMin;
            }
          }
        }
        if (filters.product_categories.length > 0) {
          filterParams.product_categories = filters.product_categories.map(c => c.toLowerCase());
        }
        if (filters.tags.length > 0) {
          filterParams.tags = filters.tags.map(t => t.toLowerCase());
        }
        if (filters.payment_methods.length > 0) {
          filterParams.payment_methods = filters.payment_methods.map(p => p.toLowerCase());
          console.log('Payment method filter:', filterParams.payment_methods);
        }
        if (filters.date_range) {
          filterParams.date_from = filters.date_range;
        }
        return filterParams;
      };

      const filterParams = buildFilterParams();
      
      if (debouncedSearchQuery && debouncedSearchQuery.trim()) {
        params.search = debouncedSearchQuery.trim();
        console.log('Searching for:', params.search);
      }
      
      Object.assign(params, filterParams);
      
      const summaryParams = { ...filterParams };

      const [transactionsData, summaryData] = await Promise.all([
        salesAPI.getTransactions(params),
        salesAPI.getSummary(summaryParams),
      ]);

      setTransactions(transactionsData.transactions);
      setTotal(transactionsData.total);
      setTotalPages(transactionsData.total_pages);
      setSummary(summaryData);
      
      if (transactionsData.transactions.length > 0) {
        const firstFew = transactionsData.transactions.slice(0, 3).map(t => ({
          date: t.date,
          quantity: t.quantity,
          customer_name: t.customer_name
        }));
        console.log(`Sort: ${sortBy} ${sortOrder}, First 3 transactions:`, firstFew);
      }
      
      if (debouncedSearchQuery && debouncedSearchQuery.trim()) {
        console.log(`Search "${debouncedSearchQuery}" returned ${transactionsData.total} results`);
      }
      
      if (currentPage > transactionsData.total_pages && transactionsData.total_pages > 0) {
        setCurrentPage(1);
      }
    } catch (error: any) {
      console.error('Error fetching data:', error);
      if (error.response?.status === 400) {
        const errorMessage = error.response?.data?.detail || 'Invalid filter parameters';
        alert(errorMessage);
      } else {
        setTransactions([]);
        setTotal(0);
        setTotalPages(0);
        setSummary({
          total_units_sold: 0,
          total_amount: 0,
          total_discount: 0,
          total_sales_records: 0,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [debouncedSearchQuery, filters, sortBy, sortOrder, currentPage]);

  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const options = await salesAPI.getFilterOptions();
        setFilterOptions(options);
      } catch (error) {
        console.error('Error fetching filter options:', error);
      }
    };

    fetchFilterOptions();
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
      setCurrentPage(1);
    }, 500);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleFilterChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters);
    setCurrentPage(1);
  }, []);

  const handleSortChange = (newSortBy: string, newSortOrder: string) => {
    console.log('Sort changed:', { newSortBy, newSortOrder });
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1);
    setSortDropdownOpen(false);
  };

  const SortByDropdown = ({ sortBy, sortOrder, onSortChange }: { sortBy: string; sortOrder: string; onSortChange: (field: string, order: string) => void }) => {
    const sortOptions = [
      { value: 'date_desc', label: 'Date (Newest First)' },
      { value: 'date_asc', label: 'Date (Oldest First)' },
      { value: 'quantity_desc', label: 'Quantity (High to Low)' },
      { value: 'quantity_asc', label: 'Quantity (Low to High)' },
      { value: 'customer_name_asc', label: 'Customer Name (A-Z)' },
      { value: 'customer_name_desc', label: 'Customer Name (Z-A)' },
    ];

    const currentValue = `${sortBy}_${sortOrder}`;
    const currentLabel = sortOptions.find(opt => opt.value === currentValue)?.label || 'Sort by';

    return (
      <div className="relative min-w-[180px]">
        <button
          onClick={() => setSortDropdownOpen(!sortDropdownOpen)}
          className="w-full px-2 py-1 text-left bg-gray-100 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex justify-between rounded-md"
        >
          <span className="text-sm text-gray-700 truncate">
            {currentLabel}
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${sortDropdownOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {sortDropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setSortDropdownOpen(false)}
            ></div>
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
              {sortOptions.map((option) => {
                const [field, order] = option.value.split('_');
                return (
                  <button
                    key={option.value}
                    onClick={() => onSortChange(field, order)}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </>
        )}
      </div>
    );
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getSortLabel = () => {
    const labels: Record<string, string> = {
      date: 'Date (Newest First)',
      quantity: 'Quantity',
      customer_name: 'Customer Name (A-Z)',
    };
    return labels[sortBy] || 'Date (Newest First)';
  };

  return (
    <div className="flex min-h-screen ">
      <Sidebar />
      <div className="flex-1 p-6 lg:p-8">

        <div className="mb-6 flex flex-col md:flex-row gap-4 items-center justify-between">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-6">Sales Management System</h1>

          <div className="w-full md:w-auto relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search by Name, Phone, ID, Product..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full bg-gray-100 md:w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mb-6 flex flex-col md:flex-row gap-4 justify-between">
          <Filters
            filterOptions={filterOptions}
            onFilterChange={handleFilterChange}
            loading={loading}
          />
          <SortByDropdown
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSortChange={handleSortChange}
          />
        </div>

        <SummaryCards stats={summary} loading={loading} />

        <SalesTable
          transactions={transactions}
          loading={loading}
          onSortChange={handleSortChange}
          currentSort={{ sortBy, sortOrder }}
          showFullView={showFullView}
          onToggleFullView={() => setShowFullView(!showFullView)}
        />

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          loading={loading}
        />
      </div>
    </div>
  );
}

