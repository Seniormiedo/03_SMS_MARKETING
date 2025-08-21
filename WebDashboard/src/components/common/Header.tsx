import {
    BellIcon,
    Cog6ToothIcon,
    UserCircleIcon,
} from "@heroicons/react/24/outline";
import React from "react";
import { useAppSelector } from "../../hooks/redux";
import { MobileSidebar } from "./MobileSidebar";
import { Icon } from "./Icon";

export const Header: React.FC = () => {
  const stats = useAppSelector((state) => state.contacts?.stats);
  const totalContacts = stats?.totalContacts || 0;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 truncate">
              SMS Marketing Dashboard
            </h1>
            <div className="hidden sm:block ml-4 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
              {totalContacts.toLocaleString()} contacts
            </div>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Mobile menu button */}
            <MobileSidebar />

            <button className="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
              <Icon icon={BellIcon} size="md" />
            </button>

            <button className="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
              <Icon icon={Cog6ToothIcon} size="md" />
            </button>

            <div className="flex items-center space-x-2">
              <Icon icon={UserCircleIcon} size="lg" className="text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                Admin User
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
