'use client';

import React, { useState, useEffect } from 'react';
import { FilterOptions } from '@/services/api';

interface FiltersProps {
  filterOptions: FilterOptions;
  onFilterChange: (filters: FilterState) => void;
  loading?: boolean;
}

export interface FilterState {
  customer_regions: string[];
  genders: string[];
  age_range: string;
  product_categories: string[];
  tags: string[];
  payment_methods: string[];
  date_range: string;
}

const Filters: React.FC<FiltersProps> = ({ filterOptions, onFilterChange, loading }) => {
  const [filters, setFilters] = useState<FilterState>({
    customer_regions: [],
    genders: [],
    age_range: '',
    product_categories: [],
    tags: [],
    payment_methods: [],
    date_range: '',
  });

  const [dropdownsOpen, setDropdownsOpen] = useState<Record<string, boolean>>({});

  const toggleDropdown = (key: string) => {
    setDropdownsOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleMultiSelect = (key: keyof FilterState, value: string) => {
    setFilters((prev) => {
      const current = (prev[key] as string[]) || [];
      const newValue = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [key]: newValue };
    });
  };

  const handleAgeRange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      age_range: value,
    }));
  };

  const handleDateRange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      date_range: value,
    }));
  };

  const getDateRangeOptions = () => {
    const today = new Date();
    const formatDate = (date: Date) => date.toISOString().split('T')[0];
    
    const options: { label: string; value: string }[] = [];
    
    options.push({ label: 'Today', value: formatDate(today) });
    
    const last7Days = new Date(today);
    last7Days.setDate(today.getDate() - 7);
    options.push({ label: 'Last 7 days', value: formatDate(last7Days) });
    
    const last30Days = new Date(today);
    last30Days.setDate(today.getDate() - 30);
    options.push({ label: 'Last 30 days', value: formatDate(last30Days) });
    
    const last90Days = new Date(today);
    last90Days.setDate(today.getDate() - 90);
    options.push({ label: 'Last 90 days', value: formatDate(last90Days) });
    
    const thisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    options.push({ label: 'This month', value: formatDate(thisMonth) });
    
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    options.push({ label: 'Last month', value: formatDate(lastMonth) });
    
    const thisYear = new Date(today.getFullYear(), 0, 1);
    options.push({ label: 'This year', value: formatDate(thisYear) });
    
    const lastYear = new Date(today.getFullYear() - 1, 0, 1);
    options.push({ label: 'Last year', value: formatDate(lastYear) });
    
    return options;
  };

  const dateRangeOptions = getDateRangeOptions();

  const handleRefresh = () => {
    setFilters({
      customer_regions: [],
      genders: [],
      age_range: '',
      product_categories: [],
      tags: [],
      payment_methods: [],
      date_range: '',
    });
  };

  useEffect(() => {
    onFilterChange(filters);
  }, [filters]);

  const clearFilter = (key: keyof FilterState) => {
    if (Array.isArray(filters[key])) {
      setFilters((prev) => ({ ...prev, [key]: [] }));
    } else {
      setFilters((prev) => ({ ...prev, [key]: '' }));
    }
  };

  const MultiSelectDropdown = ({
    label,
    keyName,
    options,
  }: {
    label: string;
    keyName: keyof FilterState;
    options: string[];
  }) => {
    const selected = (filters[keyName] as string[]) || [];
    const isOpen = dropdownsOpen[keyName] || false;

    return (
      <div className="relative min-w-[90px]">
        <button
          onClick={() => toggleDropdown(keyName)}
          className="w-full px-2 py-1 text-left bg-gray-100 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
        >
          <span className="text-sm text-gray-700 truncate">
            {selected.length > 0 ? `${label} (${selected.length})` : label}
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => toggleDropdown(keyName)}
            ></div>
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
              {options.map((option) => (
                <label
                  key={option}
                  className="flex items-center px-4 py-2 hover:bg-gray-100 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(option)}
                    onChange={() => handleMultiSelect(keyName, option)}
                    className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          </>
        )}
        {selected.length > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              clearFilter(keyName);
            }}
            className="absolute right-8 top-2 text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        )}
      </div>
    );
  };

  const ageRangeOptions = [
    '18-25',
    '26-35',
    '36-45',
    '46-55',
    '56-65',
    '65+',
  ];

  const AgeRangeDropdown = () => {
    const isOpen = dropdownsOpen['age_range'] || false;
    return (
      <div className="relative min-w-[90px]">
        <button
          onClick={() => toggleDropdown('age_range')}
          className="w-full px-2 py-1 text-left bg-gray-100 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between rounded-md"
        >
          <span className="text-sm text-gray-700 truncate">
            {filters.age_range || 'Age Range'}
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => toggleDropdown('age_range')}
            ></div>
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
              <button
                onClick={() => {
                  handleAgeRange('');
                  toggleDropdown('age_range');
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
              >
                All Ages
              </button>
              {ageRangeOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => {
                    handleAgeRange(option);
                    toggleDropdown('age_range');
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                >
                  {option}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  const DateRangeDropdown = () => {
    const isOpen = dropdownsOpen['date_range'] || false;
    const selectedLabel = dateRangeOptions.find(opt => opt.value === filters.date_range)?.label || 'Date';
    
    return (
      <div className="relative min-w-[90px]">
        <button
          onClick={() => toggleDropdown('date_range')}
          className="w-full px-2 py-1 text-left bg-gray-100 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between rounded-md"
        >
          <span className="text-sm text-gray-700 truncate">
            {filters.date_range ? selectedLabel : 'Date'}
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => toggleDropdown('date_range')}
            ></div>
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
              <button
                onClick={() => {
                  handleDateRange('');
                  toggleDropdown('date_range');
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
              >
                All Dates
              </button>
              {dateRangeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    handleDateRange(option.value);
                    toggleDropdown('date_range');
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="mb-6 flex items-center gap-3 flex-wrap">
      <button
        onClick={handleRefresh}
        className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        title="Refresh filters"
      >
        <svg
          className="w-5 h-5 text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      </button>

      <MultiSelectDropdown
        label="Customer Region"
        keyName="customer_regions"
        options={filterOptions.customer_regions}
      />
      <MultiSelectDropdown
        label="Gender"
        keyName="genders"
        options={filterOptions.genders}
      />
      <AgeRangeDropdown />
      <MultiSelectDropdown
        label="Product Category"
        keyName="product_categories"
        options={filterOptions.product_categories}
      />
      <MultiSelectDropdown
        label="Tags"
        keyName="tags"
        options={filterOptions.tags}
      />
      <MultiSelectDropdown
        label="Payment Method"
        keyName="payment_methods"
        options={filterOptions.payment_methods}
      />
      <DateRangeDropdown />
    </div>
  );
};

export default Filters;

