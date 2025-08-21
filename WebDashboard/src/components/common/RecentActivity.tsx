import {
    CheckBadgeIcon,
    DocumentArrowDownIcon,
    ExclamationTriangleIcon,
    UserPlusIcon,
} from "@heroicons/react/24/outline";
import { formatDistanceToNow } from "date-fns";
import React from "react";

interface Activity {
  id: string;
  type: "extraction" | "contact_added" | "validation" | "error";
  message: string;
  timestamp: Date;
  details?: string;
}

export const RecentActivity: React.FC = () => {
  // Mock data - will be replaced with real data from API
  const activities: Activity[] = [
    {
      id: "1",
      type: "extraction",
      message: "New extraction completed: SINALOA state",
      timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
      details: "1,500 contacts extracted",
    },
    {
      id: "2",
      type: "contact_added",
      message: "Bulk contacts imported",
      timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
      details: "2,300 new contacts",
    },
    {
      id: "3",
      type: "validation",
      message: "WhatsApp validation completed",
      timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
      details: "850 numbers validated",
    },
    {
      id: "4",
      type: "extraction",
      message: "Export generated: JALISCO municipality",
      timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
      details: "3,200 contacts in XLSX format",
    },
    {
      id: "5",
      type: "error",
      message: "Rate limit reached on Instagram validator",
      timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
      details: "Automatically switched to backup method",
    },
  ];

  const getActivityIcon = (type: Activity["type"]) => {
    const iconMap = {
      extraction: DocumentArrowDownIcon,
      contact_added: UserPlusIcon,
      validation: CheckBadgeIcon,
      error: ExclamationTriangleIcon,
    };
    return iconMap[type];
  };

  const getActivityColor = (type: Activity["type"]) => {
    const colorMap = {
      extraction: "text-blue-500 bg-blue-50",
      contact_added: "text-green-500 bg-green-50",
      validation: "text-purple-500 bg-purple-50",
      error: "text-red-500 bg-red-50",
    };
    return colorMap[type];
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        <button className="text-sm text-blue-600 hover:text-blue-500">
          View all
        </button>
      </div>

      <div className="flow-root">
        <ul className="-mb-8">
          {activities.map((activity, index) => {
            const Icon = getActivityIcon(activity.type);
            const isLast = index === activities.length - 1;

            return (
              <li key={activity.id}>
                <div className="relative pb-8">
                  {!isLast && (
                    <span
                      className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex items-start space-x-3">
                    <div className="relative">
                      <div
                        className={`h-10 w-10 rounded-full flex items-center justify-center ring-8 ring-white ${getActivityColor(
                          activity.type
                        )}`}
                      >
                        <Icon className="h-5 w-5" aria-hidden="true" />
                      </div>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div>
                        <div className="text-sm">
                          <span className="font-medium text-gray-900">
                            {activity.message}
                          </span>
                        </div>
                        <p className="mt-0.5 text-sm text-gray-500">
                          {formatDistanceToNow(activity.timestamp, {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                      {activity.details && (
                        <div className="mt-2 text-sm text-gray-500">
                          {activity.details}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-500 text-center">
          Auto-refreshes every 30 seconds
        </div>
      </div>
    </div>
  );
};
