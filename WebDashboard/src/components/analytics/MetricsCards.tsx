import {
    CheckCircleIcon,
    ClockIcon,
    DocumentTextIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import React from "react";
import { Icon } from "../common/Icon";

interface MetricsCardsProps {
  stats: {
    totalContacts: number;
    contactsByState: Record<string, number>;
    contactsByLada: Record<string, number>;
    recentExtractions: number;
  };
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ stats }) => {
  // Provide default values if stats is undefined
  const safeStats = stats || {
    totalContacts: 0,
    contactsByState: {},
    contactsByLada: {},
    recentExtractions: 0,
  };

  const metrics = [
    {
      name: "Total Contacts",
      value: safeStats.totalContacts.toLocaleString(),
      icon: UsersIcon,
      change: "+2.5%",
      changeType: "increase" as const,
      description: "from last month",
      color: "blue",
    },
    {
      name: "States Covered",
      value: Object.keys(safeStats.contactsByState).length.toString(),
      icon: DocumentTextIcon,
      change: "+1",
      changeType: "increase" as const,
      description: "new state added",
      color: "green",
    },
    {
      name: "Recent Extractions",
      value: safeStats.recentExtractions.toString(),
      icon: CheckCircleIcon,
      change: "+12%",
      changeType: "increase" as const,
      description: "from last week",
      color: "purple",
    },
    {
      name: "Validation Rate",
      value: "94.2%",
      icon: ClockIcon,
      change: "+0.8%",
      changeType: "increase" as const,
      description: "accuracy improved",
      color: "orange",
    },
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: "bg-blue-50 text-blue-600",
      green: "bg-green-50 text-green-600",
      purple: "bg-purple-50 text-purple-600",
      orange: "bg-orange-50 text-orange-600",
    };
    return colorMap[color as keyof typeof colorMap] || "bg-gray-50 text-gray-600";
  };

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, index) => (
        <div
          key={metric.name}
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer animate-slide-up"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="p-3 sm:p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-2 sm:p-3 rounded-lg ${getColorClasses(metric.color)}`}>
                  <Icon icon={metric.icon} size="md" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-3 sm:ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                    {metric.name}
                  </dt>
                  <dd>
                    <div className="text-lg sm:text-2xl font-bold text-gray-900">
                      {metric.value}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-3 py-2 sm:px-5 sm:py-3">
            <div className="text-sm">
              <span
                className={`font-medium ${
                  metric.changeType === "increase"
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {metric.change}
              </span>
              <span className="text-gray-500"> {metric.description}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
