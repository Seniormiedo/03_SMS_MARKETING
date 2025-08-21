import {
    CalendarIcon,
    EyeIcon,
    MapPinIcon,
    PencilIcon,
    PhoneIcon,
    TrashIcon,
} from "@heroicons/react/24/outline";
import { format } from "date-fns";
import React from "react";
import type { Contact } from "../../types/Contact";

interface ContactCardProps {
  contact: Contact;
  isSelected: boolean;
  onSelect: () => void;
}

export const ContactCard: React.FC<ContactCardProps> = ({
  contact,
  isSelected,
  onSelect,
}) => {
  const formatPhoneNumber = (phoneE164: string, phoneNational: string) => {
    return phoneNational || phoneE164;
  };

  return (
    <div
      className={`
        bg-white border rounded-lg p-4 transition-all duration-200
        ${isSelected
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
        }
      `}
    >
      {/* Card Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <div className="ml-3 flex-1 min-w-0">
            <div className="flex items-center">
              <PhoneIcon className="h-4 w-4 text-gray-400 mr-2" />
              <p className="text-sm font-medium text-gray-900 truncate">
                {formatPhoneNumber(contact.phoneE164, contact.phoneNational)}
              </p>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {contact.phoneE164}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-1 ml-2">
          <button
            className="p-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-100 rounded transition-colors"
            title="View details"
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          <button
            className="p-1.5 text-yellow-600 hover:text-yellow-900 hover:bg-yellow-100 rounded transition-colors"
            title="Edit contact"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            className="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-100 rounded transition-colors"
            title="Delete contact"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Card Content */}
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="flex items-center">
          <MapPinIcon className="h-4 w-4 text-gray-400 mr-2" />
          <div>
            <p className="font-medium text-gray-900">{contact.stateName}</p>
            <p className="text-gray-500">{contact.municipality}</p>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-gray-100 px-2 py-1 rounded text-xs font-medium text-gray-800">
            LADA {contact.lada}
          </div>
        </div>

        <div className="flex items-center col-span-2">
          <CalendarIcon className="h-4 w-4 text-gray-400 mr-2" />
          <p className="text-gray-500">
            Created {format(new Date(contact.createdAt), "MMM dd, yyyy 'at' HH:mm")}
          </p>
        </div>
      </div>

      {/* Validation Status - Placeholder for future */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Validation Status</span>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Pending
          </span>
        </div>
      </div>
    </div>
  );
};
