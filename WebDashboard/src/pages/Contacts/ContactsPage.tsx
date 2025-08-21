import { ArrowPathIcon, PlusIcon } from "@heroicons/react/24/outline";
import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ContactFilters } from "../../components/contacts/ContactFilters";
import { ContactList } from "../../components/contacts/ContactList";
import { ContactStats } from "../../components/contacts/ContactStats";
import { ExtractionForm } from "../../components/contacts/ExtractionForm";
import { useAppDispatch, useAppSelector } from "../../hooks/redux";
import {
    clearError,
    fetchContacts,
    setFilters,
    setPage,
} from "../../store/slices/contactsSlice";
import type { ContactFilters as ContactFiltersType } from "../../types/Contact";

export const ContactsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const {
    contacts,
    loading,
    error,
    filters,
    pagination,
    totalContacts,
    stats
  } = useAppSelector((state) => state.contacts);

  const [showExtractionForm, setShowExtractionForm] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load initial data
  useEffect(() => {
    dispatch(fetchContacts({
      filters,
      page: pagination.page,
      pageSize: pagination.pageSize,
    }));
  }, [dispatch, filters, pagination.page, pagination.pageSize]);

  // Event handlers
  const handleFiltersChange = (newFilters: ContactFiltersType) => {
    dispatch(setFilters(newFilters));
  };

  const handlePageChange = (page: number) => {
    dispatch(setPage(page));
  };

  const handleExtractionModal = (show: boolean) => {
    setShowExtractionForm(show);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await dispatch(fetchContacts({
        filters,
        page: pagination.page,
        pageSize: pagination.pageSize,
      })).unwrap();
      toast.success("Contacts refreshed successfully!");
    } catch {
      toast.error("Failed to refresh contacts");
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleClearError = () => {
    dispatch(clearError());
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl">
            Contacts
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage and extract contacts from your database
          </p>
        </div>
        <div className="mt-4 flex space-x-3 sm:mt-0 sm:ml-4">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing || loading}
            className="btn-secondary"
          >
            {isRefreshing ? (
              <LoadingSpinner size="sm" className="mr-2" />
            ) : (
              <ArrowPathIcon className="-ml-1 mr-2 h-5 w-5" />
            )}
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>
          <button
            onClick={() => handleExtractionModal(true)}
            className="btn-primary"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
            New Extraction
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                Error loading contacts
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={handleRefresh}
                  className="btn-primary"
                >
                  Retry
                </button>
                <button
                  onClick={handleClearError}
                  className="btn-secondary"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contact Stats */}
      <ContactStats
        totalContacts={totalContacts}
        stats={stats}
        onFilterClick={handleFiltersChange}
      />

      {/* Filters */}
      <ContactFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        loading={loading}
      />

      {/* Contact List */}
      <ContactList
        contacts={contacts}
        loading={loading}
        pagination={pagination}
        onPageChange={handlePageChange}
      />

      {/* Extraction Form Modal */}
      {showExtractionForm && (
        <ExtractionForm
          onClose={() => handleExtractionModal(false)}
          onSuccess={() => {
            handleExtractionModal(false);
            toast.success("Extraction started successfully!");
            // Refresh extractions list would go here
          }}
        />
      )}
    </div>
  );
};
