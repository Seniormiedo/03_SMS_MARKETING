import React, { useEffect } from "react";
import { ChartsGrid } from "../../components/analytics/ChartsGrid";
import { MetricsCards } from "../../components/analytics/MetricsCards";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { QuickActions } from "../../components/common/QuickActions";
import { RecentActivity } from "../../components/common/RecentActivity";
import { useAppDispatch, useAppSelector } from "../../hooks/redux";
import { fetchContactStats } from "../../store/slices/contactsSlice";

export const DashboardPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { stats, loading, error } = useAppSelector((state) => state.contacts);

  useEffect(() => {
    dispatch(fetchContactStats());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading dashboard data
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={() => dispatch(fetchContactStats())}
                className="btn-primary"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your SMS marketing platform
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <QuickActions />
        </div>
      </div>

      {/* Metrics Cards */}
      <MetricsCards stats={stats} />

      {/* Charts Grid */}
      <ChartsGrid stats={stats} />

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity />
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            System Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Healthy
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Telegram Bot</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Validation System</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Ready for Implementation
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
