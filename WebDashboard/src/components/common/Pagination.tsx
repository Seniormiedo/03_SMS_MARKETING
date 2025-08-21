import {
    ChevronDoubleLeftIcon,
    ChevronDoubleRightIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
} from "@heroicons/react/24/outline";
import React from "react";
import { LoadingSpinner } from "./LoadingSpinner";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  loading = false,
}) => {
  // Calculate display range
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate page numbers to display
  const getPageNumbers = () => {
    const delta = 2; // Number of pages to show on each side of current page
    const range = [];
    const rangeWithDots = [];

    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else if (totalPages > 1) {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  };

  const pageNumbers = getPageNumbers();

  const handlePageClick = (page: number) => {
    if (page !== currentPage && page >= 1 && page <= totalPages && !loading) {
      onPageChange(page);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, page: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handlePageClick(page);
    }
  };

  if (totalPages <= 1) {
    return (
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700">
          Showing {totalItems} result{totalItems !== 1 ? 's' : ''}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
      {/* Results Info */}
      <div className="text-sm text-gray-700">
        {loading ? (
          <div className="flex items-center">
            <LoadingSpinner size="sm" className="mr-2" />
            Loading...
          </div>
        ) : (
          <span>
            Showing <span className="font-medium">{startItem}</span> to{" "}
            <span className="font-medium">{endItem}</span> of{" "}
            <span className="font-medium">{totalItems}</span> results
          </span>
        )}
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center space-x-1">
        {/* First Page */}
        <button
          onClick={() => handlePageClick(1)}
          disabled={currentPage === 1 || loading}
          className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="First page"
        >
          <ChevronDoubleLeftIcon className="h-4 w-4" />
        </button>

        {/* Previous Page */}
        <button
          onClick={() => handlePageClick(currentPage - 1)}
          disabled={currentPage === 1 || loading}
          className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Previous page"
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </button>

        {/* Page Numbers */}
        <div className="hidden sm:flex items-center space-x-1">
          {pageNumbers.map((pageNumber, index) => {
            if (pageNumber === '...') {
              return (
                <span
                  key={`dots-${index}`}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                >
                  ...
                </span>
              );
            }

            const page = pageNumber as number;
            const isCurrentPage = page === currentPage;

            return (
              <button
                key={page}
                onClick={() => handlePageClick(page)}
                onKeyDown={(e) => handleKeyDown(e, page)}
                disabled={loading}
                className={`
                  relative inline-flex items-center px-4 py-2 border text-sm font-medium rounded-md transition-colors
                  ${isCurrentPage
                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                {page}
              </button>
            );
          })}
        </div>

        {/* Mobile Page Info */}
        <div className="sm:hidden flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 rounded-md">
          Page {currentPage} of {totalPages}
        </div>

        {/* Next Page */}
        <button
          onClick={() => handlePageClick(currentPage + 1)}
          disabled={currentPage === totalPages || loading}
          className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Next page"
        >
          <ChevronRightIcon className="h-4 w-4" />
        </button>

        {/* Last Page */}
        <button
          onClick={() => handlePageClick(totalPages)}
          disabled={currentPage === totalPages || loading}
          className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Last page"
        >
          <ChevronDoubleRightIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
