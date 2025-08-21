import {
    ArrowTrendingUpIcon,
    MapIcon,
    PhoneIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import React from "react";
import type { ContactFilters } from "../../types/Contact";

interface ContactStatsProps {
  totalContacts: number;
  stats: {
    totalContacts: number;
    contactsByState: Record<string, number>;
    contactsByLada: Record<string, number>;
    recentExtractions: number;
  };
  onFilterClick?: (filters: ContactFilters) => void;
}

export const ContactStats: React.FC<ContactStatsProps> = ({
  totalContacts,
  stats,
  onFilterClick,
}) => {
  // Calculate dynamic metrics
  const statesCount = Object.keys(stats.contactsByState).length;
  const ladasCount = Object.keys(stats.contactsByLada).length;
  const topState = Object.entries(stats.contactsByState)
    .sort(([, a], [, b]) => b - a)[0];
  const topLada = Object.entries(stats.contactsByLada)
    .sort(([, a], [, b]) => b - a)[0];

  const quickStats = [
    {
      name: "Total Contacts",
      value: totalContacts.toLocaleString(),
      icon: UsersIcon,
      color: "blue",
      description: "in database",
      clickable: false,
    },
    {
      name: "States Covered",
      value: statesCount.toString(),
      icon: MapIcon,
      color: "green",
      description: `Top: ${topState?.[0] || 'N/A'}`,
      clickable: true,
      onClick: () => onFilterClick?.({ state: topState?.[0] }),
    },
    {
      name: "LADA Codes",
      value: ladasCount.toString(),
      icon: PhoneIcon,
      color: "purple",
      description: `Top: ${topLada?.[0] || 'N/A'}`,
      clickable: true,
      onClick: () => onFilterClick?.({ lada: topLada?.[0] }),
    },
    {
      name: "Growth Rate",
      value: "+12.3%",
      icon: ArrowTrendingUpIcon,
      color: "orange",
      description: "this month",
      clickable: false,
    },
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: "bg-blue-50 text-blue-600 border-blue-200",
      green: "bg-green-50 text-green-600 border-green-200",
      purple: "bg-purple-50 text-purple-600 border-purple-200",
      orange: "bg-orange-50 text-orange-600 border-orange-200",
    };
    return colorMap[color as keyof typeof colorMap] || "bg-gray-50 text-gray-600 border-gray-200";
  };

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
      {quickStats.map((stat, index) => (
        <div
          key={stat.name}
          className={`
            bg-white border rounded-lg p-3 sm:p-4 transition-all duration-200
            ${stat.clickable
              ? 'cursor-pointer hover:shadow-md hover:scale-105 active:scale-95'
              : 'hover:shadow-sm'
            }
            animate-slide-up
          `}
          style={{ animationDelay: `${index * 100}ms` }}
          onClick={stat.onClick}
          role={stat.clickable ? "button" : "presentation"}
          tabIndex={stat.clickable ? 0 : -1}
          onKeyDown={(e) => {
            if (stat.clickable && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              stat.onClick?.();
            }
          }}
        >
          <div className="flex items-center">
            <div className={`flex-shrink-0 p-2 rounded-lg ${getColorClasses(stat.color)}`}>
              <stat.icon className="h-5 w-5 sm:h-6 sm:w-6" aria-hidden="true" />
            </div>
            <div className="ml-3 flex-1 min-w-0">
              <div className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                {stat.name}
              </div>
              <div className="text-lg sm:text-xl font-bold text-gray-900">
                {stat.value}
              </div>
              <div className="text-xs text-gray-400 truncate">
                {stat.description}
              </div>
            </div>
          </div>

          {stat.clickable && (
            <div className="mt-2 text-xs text-blue-600 font-medium">
              Click to filter
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
