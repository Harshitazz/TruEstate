# Sales Management System

## Overview

A Retail Sales Management System built with FastAPI and Next.js that provides comprehensive search, filtering, sorting, and pagination capabilities for sales transaction data. The system efficiently handles large datasets stored in CSV format, loaded into memory using Pandas for fast data processing. The application features an intuitive user interface with real-time search, multi-select filters, and robust error handling for edge cases.

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Pandas (data processing and filtering)
- NumPy (numerical operations)
- Pydantic (data validation)
- Python-dotenv (environment configuration)

**Frontend:**
- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS (styling)
- Axios (HTTP client)

**Data Storage:**
- CSV file (loaded into memory at startup)

## Search Implementation Summary

The search functionality implements case-insensitive multi-field search across major transaction fields including customer names, phone numbers, transaction IDs, customer IDs, product IDs, product names, employee names, store IDs, store locations, brands, customer types, order status, and delivery types. The backend uses Pandas string operations with `.str.contains()` for partial matching, handling both text and numeric fields. Phone numbers are normalized by removing non-digit characters for flexible matching. The frontend debounces user input (500ms delay) to optimize API calls and automatically resets pagination when search changes. Search results are combined with active filters using AND logic.

## Filter Implementation Summary

Multi-select filtering is implemented for Customer Region, Gender, Product Category, Tags, and Payment Method using dropdown components. Age range and date range filters use single dropdown selectors with predefined options. The backend normalizes all filter values to lowercase for consistent matching, validates filter conflicts (e.g., age_min > age_max), and handles missing optional fields gracefully. Filters are applied sequentially using Pandas boolean masking with `.isin()` for array filters and comparison operators for range filters. All filters work together using AND logic, and the system handles empty results, conflicting filters, and invalid numeric ranges with proper error messages. Filter options are dynamically loaded from the API to ensure accuracy.

## Sorting Implementation Summary

Sorting supports three fields: Date (newest/oldest first), Quantity (high to low / low to high), and Customer Name (A-Z / Z-A). The backend uses Pandas `.sort_values()` with stable sorting (`kind='mergesort'`) for consistent results. Date and quantity fields are sorted as their native types, while customer names are sorted case-insensitively by creating a temporary lowercase sort key. Sorting is applied after filtering but before pagination to ensure correct ordering across all pages. The frontend provides a dropdown selector matching the filter style, and sort state is preserved across filter and search changes. The index is reset after sorting to maintain proper pagination.

## Pagination Implementation Summary

Pagination is implemented with a configurable page size (default: 10 items per page). The backend calculates skip value as `(page - 1) * page_size` and uses Pandas `.iloc[]` slicing for efficient data retrieval. Total count is calculated from the filtered dataset before pagination to provide accurate pagination metadata. The frontend displays page numbers with ellipsis for large page counts, Previous/Next navigation buttons, and highlights the current page. Page state automatically resets to 1 when filters or search change, and the system handles edge cases where the current page exceeds total pages after filtering. All state (search, filters, sort) is preserved during page navigation.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- CSV data file (`truestate_assignment_dataset.csv`)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure the CSV file is in the project root:
   - Place `truestate_assignment_dataset.csv` in the root directory (`/assessment/`)

4. Start the FastAPI server:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

The CSV data will be automatically loaded into memory when the server starts.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file (if needed):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000` (or the next available port)

### Running the Complete Application

1. Start the backend server (from `backend/` directory):
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend server (from `frontend/` directory):
```bash
npm run dev
```

3. Open `http://localhost:3000` in your browser

### Environment Variables

**Backend (.env):**
- `CORS_ORIGINS` - Comma-separated list of allowed origins (default: `http://localhost:3000`)

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
