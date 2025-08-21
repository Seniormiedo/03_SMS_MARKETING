import {
    ChevronDownIcon,
    ChevronUpIcon,
    FunnelIcon,
    MagnifyingGlassIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline";
import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { useDebounce } from "../../hooks/useDebounce";
import type { ContactFilters as ContactFiltersType } from "../../types/Contact";
import { LoadingSpinner } from "../common/LoadingSpinner";



interface ContactFiltersProps {
  filters: ContactFiltersType;
  onFiltersChange: (filters: ContactFiltersType) => void;
  loading?: boolean;
}

export const ContactFilters: React.FC<ContactFiltersProps> = ({
  filters,
  onFiltersChange,
  loading = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeFiltersCount, setActiveFiltersCount] = useState(0);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
    setValue,
  } = useForm<ContactFiltersType>({
    defaultValues: filters,
  });

  const watchedValues = watch();
  const debouncedSearchQuery = useDebounce(watchedValues.searchQuery || "", 500);

  // Auto-submit search query with debounce
  useEffect(() => {
    if (debouncedSearchQuery !== filters.searchQuery) {
      onFiltersChange({
        ...filters,
        searchQuery: debouncedSearchQuery,
      });
    }
  }, [debouncedSearchQuery, filters, onFiltersChange]);

  // Count active filters
  useEffect(() => {
    const count = Object.values(filters).filter(value => {
      if (typeof value === 'object' && value !== null) {
        return Object.values(value).some(v => v && v !== '');
      }
      return value && value !== '';
    }).length;
    setActiveFiltersCount(count);
  }, [filters]);

  const onSubmit = (data: ContactFiltersType) => {
    onFiltersChange(data);
  };

  const clearFilters = () => {
    reset();
    onFiltersChange({});
  };

  const clearSpecificFilter = (filterKey: keyof ContactFiltersType) => {
    const newFilters = { ...filters };
    delete newFilters[filterKey];
    setValue(filterKey, undefined);
    onFiltersChange(newFilters);
  };

  // Mock data for dropdowns - will be replaced with real API calls
  const states = [
    "SINALOA", "JALISCO", "CDMX", "NUEVO LEON", "VERACRUZ",
    "PUEBLA", "GUANAJUATO", "CHIHUAHUA", "MICHOACAN", "OAXACA"
  ];

  const municipalities = watchedValues.state ? [
    "CULIACAN", "MAZATLAN", "LOS MOCHIS", "GUASAVE", "NAVOLATO"
  ] : [];

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-4 sm:px-6 sm:py-5">
        {/* Filter Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Filter Contacts
            </h3>
            {activeFiltersCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {activeFiltersCount} active
              </span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            {activeFiltersCount > 0 && (
              <button
                onClick={clearFilters}
                className="text-sm text-red-600 hover:text-red-500 font-medium"
              >
                Clear all
              </button>
            )}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center text-sm text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? (
                <>
                  <ChevronUpIcon className="h-4 w-4 mr-1" />
                  Collapse
                </>
              ) : (
                <>
                  <ChevronDownIcon className="h-4 w-4 mr-1" />
                  Expand
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Search - Always Visible */}
        <div className="mt-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              {...register("searchQuery")}
              type="text"
              className="input-field pl-10"
              placeholder="Search by phone number..."
            />
            {watchedValues.searchQuery && (
              <button
                onClick={() => clearSpecificFilter("searchQuery")}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <XMarkIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
          {errors.searchQuery && (
            <p className="mt-1 text-sm text-red-600">{errors.searchQuery.message}</p>
          )}
        </div>

        {/* Advanced Filters - Collapsible */}
        {isExpanded && (
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* State Filter */}
              <div>
                <label htmlFor="state" className="block text-sm font-medium text-gray-700">
                  State
                </label>
                <div className="relative">
                  <select
                    {...register("state")}
                    className="input-field"
                  >
                    <option value="">All States</option>
                    {states.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                    ))}
                  </select>
                  {watchedValues.state && (
                    <button
                      type="button"
                      onClick={() => clearSpecificFilter("state")}
                      className="absolute inset-y-0 right-8 flex items-center pr-2"
                    >
                      <XMarkIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                    </button>
                  )}
                </div>
                {errors.state && (
                  <p className="mt-1 text-sm text-red-600">{errors.state.message}</p>
                )}
              </div>

              {/* Municipality Filter */}
              <div>
                <label htmlFor="municipality" className="block text-sm font-medium text-gray-700">
                  Municipality
                </label>
                <div className="relative">
                  <select
                    {...register("municipality")}
                    className="input-field"
                    disabled={!watchedValues.state}
                  >
                    <option value="">All Municipalities</option>
                    {municipalities.map((municipality) => (
                      <option key={municipality} value={municipality}>
                        {municipality}
                      </option>
                    ))}
                  </select>
                  {watchedValues.municipality && (
                    <button
                      type="button"
                      onClick={() => clearSpecificFilter("municipality")}
                      className="absolute inset-y-0 right-8 flex items-center pr-2"
                    >
                      <XMarkIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                    </button>
                  )}
                </div>
                {errors.municipality && (
                  <p className="mt-1 text-sm text-red-600">{errors.municipality.message}</p>
                )}
              </div>

              {/* LADA Filter */}
              <div>
                <label htmlFor="lada" className="block text-sm font-medium text-gray-700">
                  LADA Code
                </label>
                <div className="relative">
                  <input
                    {...register("lada")}
                    type="text"
                    className="input-field"
                    placeholder="e.g., 667"
                    maxLength={3}
                  />
                  {watchedValues.lada && (
                    <button
                      type="button"
                      onClick={() => clearSpecificFilter("lada")}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    >
                      <XMarkIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                    </button>
                  )}
                </div>
                {errors.lada && (
                  <p className="mt-1 text-sm text-red-600">{errors.lada.message}</p>
                )}
              </div>

              {/* Date Range Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Date Range
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    {...register("dateRange.start")}
                    type="date"
                    className="input-field"
                    placeholder="Start date"
                  />
                  <input
                    {...register("dateRange.end")}
                    type="date"
                    className="input-field"
                    placeholder="End date"
                  />
                </div>
                {(errors.dateRange?.start || errors.dateRange?.end) && (
                  <p className="mt-1 text-sm text-red-600">
                    Invalid date range
                  </p>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row sm:justify-end space-y-3 sm:space-y-0 sm:space-x-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={clearFilters}
                disabled={loading}
                className="btn-secondary w-full sm:w-auto"
              >
                Clear All
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full sm:w-auto"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Applying...
                  </>
                ) : (
                  <>
                    <FunnelIcon className="-ml-1 mr-2 h-4 w-4" />
                    Apply Filters
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* Active Filters Display */}
        {activeFiltersCount > 0 && !isExpanded && (
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(filters).map(([key, value]) => {
              if (!value || value === '') return null;

              const displayValue = typeof value === 'object'
                ? `${value.start} - ${value.end}`
                : value;

              return (
                <span
                  key={key}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {key}: {displayValue}
                  <button
                    onClick={() => clearSpecificFilter(key as keyof ContactFiltersType)}
                    className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-blue-200"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
