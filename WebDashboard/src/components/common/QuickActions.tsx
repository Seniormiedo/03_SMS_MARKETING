import {
    ArrowDownTrayIcon,
    ArrowPathIcon,
    EllipsisVerticalIcon,
    PlusIcon,
} from "@heroicons/react/24/outline";
import React, { useState } from "react";
import toast from "react-hot-toast";
import { useAppDispatch } from "../../hooks/redux";
import { fetchContactStats } from "../../store/slices/contactsSlice";
import { LoadingSpinner } from "./LoadingSpinner";

export const QuickActions: React.FC = () => {
  const dispatch = useAppDispatch();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await dispatch(fetchContactStats()).unwrap();
      toast.success("Data refreshed successfully!");
    } catch {
      toast.error("Failed to refresh data");
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleNewExtraction = () => {
    toast.success("New extraction feature coming in Phase 3!");
  };

  const handleExportData = () => {
    toast.success("Export feature coming soon!");
  };

  return (
    <div className="flex items-center space-x-3">
      {/* New Extraction Button */}
      <button
        onClick={handleNewExtraction}
        className="btn-primary"
      >
        <PlusIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
        New Extraction
      </button>

      {/* Refresh Button */}
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="btn-secondary"
      >
        {isRefreshing ? (
          <LoadingSpinner size="sm" className="mr-2" />
        ) : (
          <ArrowPathIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
        )}
        {isRefreshing ? "Refreshing..." : "Refresh"}
      </button>

      {/* More Actions Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="btn-secondary"
        >
          <EllipsisVerticalIcon className="h-5 w-5" aria-hidden="true" />
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
            <div className="py-1">
              <button
                onClick={handleExportData}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                <ArrowDownTrayIcon className="mr-3 h-4 w-4" />
                Export Data
              </button>
              <button
                onClick={() => toast.success("Settings coming soon!")}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Settings
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};
