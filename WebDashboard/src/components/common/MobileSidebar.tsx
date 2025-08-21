import {
    Bars3Icon,
    ChartBarIcon,
    CheckBadgeIcon,
    DocumentTextIcon,
    HomeIcon,
    MegaphoneIcon,
    UsersIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline";
import { clsx } from "clsx";
import React, { useState } from "react";
import { NavLink } from "react-router-dom";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Contacts", href: "/contacts", icon: UsersIcon },
  { name: "Campaigns", href: "/campaigns", icon: MegaphoneIcon },
  { name: "Validation", href: "/validation", icon: CheckBadgeIcon },
  { name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { name: "Reports", href: "/reports", icon: DocumentTextIcon },
];

export const MobileSidebar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile menu button */}
      <div className="md:hidden">
        <button
          onClick={() => setIsOpen(true)}
          className="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Bars3Icon className="h-6 w-6" />
        </button>
      </div>

      {/* Mobile sidebar overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setIsOpen(false)}
          />

          {/* Sidebar */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-gray-900">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                onClick={() => setIsOpen(false)}
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              >
                <XMarkIcon className="h-6 w-6 text-white" />
              </button>
            </div>

            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="ml-2 text-white font-semibold">SMS Marketing</span>
              </div>
              <nav className="mt-5 px-2 space-y-1">
                {navigation.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    onClick={() => setIsOpen(false)}
                    className={({ isActive }) =>
                      clsx(
                        isActive
                          ? "bg-gray-800 text-white"
                          : "text-gray-300 hover:bg-gray-700 hover:text-white",
                        "group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors"
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <item.icon
                          className={clsx(
                            isActive
                              ? "text-white"
                              : "text-gray-400 group-hover:text-gray-300",
                            "mr-4 flex-shrink-0 h-6 w-6"
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
      )}
    </>
  );
};
