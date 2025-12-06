'use client';

import React, { useState } from 'react';
import { SalesTransaction } from '@/services/api';

interface SalesTableProps {
  transactions: SalesTransaction[];
  loading?: boolean;
  onSortChange: (sortBy: string, sortOrder: string) => void;
  currentSort: { sortBy: string; sortOrder: string };
  showFullView?: boolean;
  onToggleFullView?: () => void;
}

const SalesTable: React.FC<SalesTableProps> = ({
  transactions,
  loading,
  onSortChange,
  currentSort,
  showFullView = false,
  onToggleFullView,
}) => {
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [copiedPhoneId, setCopiedPhoneId] = useState<number | null>(null);

  const copyToClipboard = async (phoneNumber: string, transactionId: number) => {
    try {
      await navigator.clipboard.writeText(phoneNumber);
      setCopiedPhoneId(transactionId);
      setTimeout(() => {
        setCopiedPhoneId(null);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy phone number:', err);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPhoneNumber = (phone: string) => {
    if (phone.startsWith('+91')) return phone;
    if (phone.length === 10) return `+91 ${phone}`;
    return phone;
  };

  const baseColumns = [
    'Transaction ID',
    'Date',
    'Customer ID',
    'Customer name',
    'Phone Number',
    'Gender',
    'Age',
    'Product Category',
    'Quantity',
  ];

  const extendedColumns = [
    ...baseColumns,
    'Total Amount',
    'Customer region',
    'Product ID',
    'Employee name',
  ];

  const columns = showFullView ? extendedColumns : baseColumns;

  const getCellValue = (transaction: SalesTransaction, column: string) => {
    try {
      switch (column) {
        case 'Transaction ID':
          return transaction.transaction_id ?? 'N/A';
        case 'Date':
          return transaction.date ?? 'N/A';
        case 'Customer ID':
          return transaction.customer_id ?? 'N/A';
        case 'Customer name':
          return transaction.customer_name ?? 'N/A';
        case 'Phone Number':
          return transaction.phone_number ? formatPhoneNumber(transaction.phone_number) : 'N/A';
        case 'Gender':
          return transaction.gender ?? 'N/A';
        case 'Age':
          return transaction.age ?? 'N/A';
        case 'Product Category':
          return transaction.product_category ?? 'N/A';
        case 'Quantity':
          return transaction.quantity != null ? String(transaction.quantity).padStart(2, '0') : 'N/A';
        case 'Total Amount':
          return transaction.total_amount != null ? formatCurrency(transaction.total_amount) : 'N/A';
        case 'Customer region':
          return transaction.customer_region ?? 'N/A';
        case 'Product ID':
          return transaction.product_id ?? 'N/A';
        case 'Employee name':
          return transaction.employee_name ?? 'N/A';
        default:
          return 'N/A';
      }
    } catch (error) {
      return 'N/A';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Sales Transactions</h2>
        {onToggleFullView && (
          <button
            onClick={onToggleFullView}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showFullView ? 'Compact View' : 'Full Table View'}
          </button>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-8 text-center">
                  <div className="flex flex-col items-center justify-center">
                    <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-gray-500 font-medium">No transactions found</p>
                    <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filter criteria</p>
                  </div>
                </td>
              </tr>
            ) : (
              transactions.map((transaction) => (
                <tr key={transaction.transaction_id} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td key={column} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {column === 'Phone Number' ? (
                        <span className="flex items-center gap-2">
                          
                          <span>{getCellValue(transaction, column)}</span>
                          <button
                            onClick={() => copyToClipboard(transaction.phone_number, transaction.transaction_id)}
                            className="ml-1 p-1 hover:bg-gray-200 rounded transition-colors"
                            title="Copy phone number"
                          >
                            {copiedPhoneId === transaction.transaction_id ? (
                              <svg
                                className="w-4 h-4 text-green-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            ) : (
                              <svg
                                className="w-4 h-4 text-gray-500 hover:text-gray-700"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                                />
                              </svg>
                            )}
                          </button>
                        </span>
                      ) : (
                        getCellValue(transaction, column)
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SalesTable;

