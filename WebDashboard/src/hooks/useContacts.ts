import { useEffect } from "react";
import {
  clearError,
  fetchContacts,
  fetchContactStats,
  setFilters,
  setPage,
  setPageSize,
} from "../store/slices/contactsSlice";
import type { ContactFilters } from "../types/Contact";
import { useAppDispatch, useAppSelector } from "./redux";

export const useContacts = () => {
  const dispatch = useAppDispatch();
  const contactsState = useAppSelector((state) => state.contacts);

  // Auto-fetch contacts when filters or pagination changes
  useEffect(() => {
    dispatch(
      fetchContacts({
        filters: contactsState.filters,
        page: contactsState.pagination.page,
        pageSize: contactsState.pagination.pageSize,
      })
    );
  }, [
    dispatch,
    contactsState.filters,
    contactsState.pagination.page,
    contactsState.pagination.pageSize,
  ]);

  // Fetch stats on mount
  useEffect(() => {
    dispatch(fetchContactStats());
  }, [dispatch]);

  const updateFilters = (filters: ContactFilters) => {
    dispatch(setFilters(filters));
  };

  const updatePage = (page: number) => {
    dispatch(setPage(page));
  };

  const updatePageSize = (pageSize: number) => {
    dispatch(setPageSize(pageSize));
  };

  const clearErrors = () => {
    dispatch(clearError());
  };

  const refreshData = () => {
    dispatch(
      fetchContacts({
        filters: contactsState.filters,
        page: contactsState.pagination.page,
        pageSize: contactsState.pagination.pageSize,
      })
    );
    dispatch(fetchContactStats());
  };

  return {
    // State
    contacts: contactsState.contacts,
    totalContacts: contactsState.totalContacts,
    loading: contactsState.loading,
    error: contactsState.error,
    filters: contactsState.filters,
    pagination: contactsState.pagination,
    stats: contactsState.stats,
    extractions: contactsState.extractions,

    // Actions
    updateFilters,
    updatePage,
    updatePageSize,
    clearErrors,
    refreshData,
  };
};
