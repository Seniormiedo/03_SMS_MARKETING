import {
    ChartBarIcon,
    CheckBadgeIcon,
    DocumentTextIcon,
    HomeIcon,
    MegaphoneIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import { clsx } from "clsx";
import React from "react";
import { NavLink } from "react-router-dom";
import { Icon } from "./Icon";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Contacts", href: "/contacts", icon: UsersIcon },
  { name: "Campaigns", href: "/campaigns", icon: MegaphoneIcon },
  { name: "Validation", href: "/validation", icon: CheckBadgeIcon },
  { name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { name: "Reports", href: "/reports", icon: DocumentTextIcon },
];

export const Sidebar: React.FC = () => {
  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
      <div className="flex-1 flex flex-col min-h-0 bg-gray-900">
        <div className="flex items-center h-16 flex-shrink-0 px-4 bg-gray-800">
          <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">S</span>
          </div>
          <span className="ml-2 text-white font-semibold">SMS Marketing</span>
        </div>

        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  clsx(
                    isActive
                      ? "bg-gray-800 text-white"
                      : "text-gray-300 hover:bg-gray-700 hover:text-white",
                    "group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      icon={item.icon}
                      size="md"
                      className={clsx(
                        isActive
                          ? "text-white"
                          : "text-gray-400 group-hover:text-gray-300",
                        "mr-3 flex-shrink-0"
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
};
