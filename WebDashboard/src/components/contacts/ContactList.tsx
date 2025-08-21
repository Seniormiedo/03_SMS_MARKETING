import {
    ChevronUpDownIcon,
    EyeIcon,
    PencilIcon,
    TrashIcon,
} from "@heroicons/react/24/outline";
import { format } from "date-fns";
import React, { useState } from "react";
import type { Contact } from "../../types/Contact";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { Pagination } from "../common/Pagination";
import { ContactCard } from "./ContactCard";

interface ContactListProps {
  contacts: Contact[];
  loading: boolean;
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
  };
  onPageChange: (page: number) => void;
}

type SortField = keyof Contact;
type SortDirection = "asc" | "desc";

export const ContactList: React.FC<ContactListProps> = ({
  contacts,
  loading,
  pagination,
  onPageChange,
}) => {
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>("createdAt");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [viewMode, setViewMode] = useState<"table" | "cards">("table");

  // Handle sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Handle contact selection
  const handleSelectContact = (contactId: string) => {
    const newSelected = new Set(selectedContacts);
    if (newSelected.has(contactId)) {
      newSelected.delete(contactId);
    } else {
      newSelected.add(contactId);
    }
    setSelectedContacts(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedContacts.size === contacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(contacts.map(c => c.id)));
    }
  };

  // Format phone number for display
  const formatPhoneNumber = (phoneE164: string, phoneNational: string) => {
    return phoneNational || phoneE164;
  };

  // Sort contacts
  const sortedContacts = [...contacts].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    return 0;
  });

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ChevronUpDownIcon className="h-4 w-4 text-gray-400" />;
    }
    return (
      <ChevronUpDownIcon
        className={`h-4 w-4 ${sortDirection === "asc" ? "text-blue-600" : "text-blue-600 transform rotate-180"}`}
      />
    );
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    );
  }

  if (contacts.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No contacts found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search criteria or filters.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Bulk Actions Header */}
      {selectedContacts.size > 0 && (
        <div className="bg-blue-50 px-4 py-3 border-b border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-sm font-medium text-blue-900">
                {selectedContacts.size} contact{selectedContacts.size !== 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <button className="text-sm text-blue-600 hover:text-blue-500 font-medium">
                Export Selected
              </button>
              <button className="text-sm text-red-600 hover:text-red-500 font-medium">
                Delete Selected
              </button>
              <button
                onClick={() => setSelectedContacts(new Set())}
                className="text-sm text-gray-600 hover:text-gray-500"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle - Mobile */}
      <div className="block sm:hidden px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">View Mode</span>
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewMode("table")}
              className={`px-3 py-1 text-xs font-medium rounded-l-md border ${
                viewMode === "table"
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode("cards")}
              className={`px-3 py-1 text-xs font-medium rounded-r-md border-t border-r border-b ${
                viewMode === "cards"
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
            >
              Cards
            </button>
          </div>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className={`${viewMode === "cards" ? "hidden sm:block" : ""} overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedContacts.size === contacts.length && contacts.length > 0}
                    onChange={handleSelectAll}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("phoneNational")}
                >
                  <div className="flex items-center">
                    Phone Number
                    {getSortIcon("phoneNational")}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("stateName")}
                >
                  <div className="flex items-center">
                    State
                    {getSortIcon("stateName")}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("municipality")}
                >
                  <div className="flex items-center">
                    Municipality
                    {getSortIcon("municipality")}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("lada")}
                >
                  <div className="flex items-center">
                    LADA
                    {getSortIcon("lada")}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("createdAt")}
                >
                  <div className="flex items-center">
                    Created
                    {getSortIcon("createdAt")}
                  </div>
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedContacts.map((contact) => (
                <tr
                  key={contact.id}
                  className={`hover:bg-gray-50 transition-colors ${
                    selectedContacts.has(contact.id) ? "bg-blue-50" : ""
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedContacts.has(contact.id)}
                      onChange={() => handleSelectContact(contact.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {formatPhoneNumber(contact.phoneE164, contact.phoneNational)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {contact.phoneE164}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {contact.stateName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {contact.municipality}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {contact.lada}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(contact.createdAt), "MMM dd, yyyy")}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        className="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
                        title="View details"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      <button
                        className="text-yellow-600 hover:text-yellow-900 p-1 rounded hover:bg-yellow-50"
                        title="Edit contact"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                        title="Delete contact"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Cards View */}
      <div className={`${viewMode === "table" ? "block sm:hidden" : "block"} space-y-4 p-4`}>
        {sortedContacts.map((contact) => (
          <ContactCard
            key={contact.id}
            contact={contact}
            isSelected={selectedContacts.has(contact.id)}
            onSelect={() => handleSelectContact(contact.id)}
          />
        ))}
      </div>

      {/* Pagination */}
      <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
        <Pagination
          currentPage={pagination.page}
          totalPages={pagination.totalPages}
          pageSize={pagination.pageSize}
          totalItems={contacts.length}
          onPageChange={onPageChange}
          loading={loading}
        />
      </div>
    </div>
  );
};
