import {
    DocumentArrowDownIcon,
    InformationCircleIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline";
import { yupResolver } from "@hookform/resolvers/yup";
import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import * as yup from "yup";
import { useAppDispatch } from "../../hooks/redux";
import { createExtraction } from "../../store/slices/contactsSlice";
import type { ExtractionRequest } from "../../types/Contact";
import { LoadingSpinner } from "../common/LoadingSpinner";

const schema = yup.object().shape({
  type: yup
    .string()
    .oneOf(["state", "municipality", "lada"])
    .required("Extraction type is required"),
  value: yup.string().required("Value is required"),
  amount: yup
    .number()
    .min(1, "Amount must be at least 1")
    .max(100000, "Amount cannot exceed 100,000")
    .required("Amount is required"),
  format: yup
    .string()
    .oneOf(["xlsx", "txt"])
    .required("Format is required"),
  includeValidation: yup.boolean().default(false),
});

interface ExtractionFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const ExtractionForm: React.FC<ExtractionFormProps> = ({
  onClose,
  onSuccess,
}) => {
  const dispatch = useAppDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [estimatedTime, setEstimatedTime] = useState<string>("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },

  } = useForm<ExtractionRequest>({
    resolver: yupResolver(schema),
    defaultValues: {
      type: "state",
      format: "xlsx",
      includeValidation: true,
      amount: 1000,
    },
  });

  const watchType = watch("type");
  const watchAmount = watch("amount");

  // Calculate estimated processing time
  useEffect(() => {
    if (watchAmount) {
      const baseTime = Math.ceil(watchAmount / 1000); // 1 second per 1000 contacts
      const validationTime = watch("includeValidation") ? Math.ceil(watchAmount / 10000) : 0;
      const totalMinutes = baseTime + validationTime;

      if (totalMinutes < 1) {
        setEstimatedTime("< 1 minute");
      } else if (totalMinutes < 60) {
        setEstimatedTime(`~${totalMinutes} minute${totalMinutes !== 1 ? 's' : ''}`);
      } else {
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
        setEstimatedTime(`~${hours}h ${minutes}m`);
      }
    }
  }, [watchAmount, watch]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const onSubmit = async (data: ExtractionRequest) => {
    setIsSubmitting(true);
    try {
      await dispatch(createExtraction(data)).unwrap();
      toast.success("Extraction started successfully!");
      onSuccess();
    } catch (error) {
      toast.error("Failed to start extraction");
      console.error("Extraction error:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPlaceholderText = () => {
    switch (watchType) {
      case "state":
        return "e.g., SINALOA";
      case "municipality":
        return "e.g., CULIACAN";
      case "lada":
        return "e.g., 667";
      default:
        return "";
    }
  };

  const getValueSuggestions = () => {
    switch (watchType) {
      case "state":
        return ["SINALOA", "JALISCO", "CDMX", "NUEVO LEON", "VERACRUZ"];
      case "municipality":
        return ["CULIACAN", "MAZATLAN", "LOS MOCHIS", "GUADALAJARA", "MONTERREY"];
      case "lada":
        return ["667", "33", "55", "81", "229"];
      default:
        return [];
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6 animate-slide-up">
          {/* Header */}
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              type="button"
              onClick={onClose}
              className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
              <DocumentArrowDownIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Create New Extraction
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Extract contacts from your database with custom filters and formats.
                </p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-6">
            {/* Extraction Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Extraction Type
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: "state", label: "State", description: "Extract by state" },
                  { value: "municipality", label: "Municipality", description: "Extract by city" },
                  { value: "lada", label: "LADA", description: "Extract by area code" },
                ].map((option) => (
                  <label key={option.value} className="relative">
                    <input
                      {...register("type")}
                      type="radio"
                      value={option.value}
                      className="sr-only"
                    />
                    <div className={`
                      cursor-pointer rounded-lg border p-3 text-center transition-all
                      ${watchType === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                        : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                      }
                    `}>
                      <div className="text-sm font-medium">{option.label}</div>
                      <div className="text-xs text-gray-500 mt-1">{option.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              {errors.type && (
                <p className="mt-2 text-sm text-red-600">{errors.type.message}</p>
              )}
            </div>

            {/* Value with Autocomplete */}
            <div>
              <label htmlFor="value" className="block text-sm font-medium text-gray-700">
                Value
              </label>
              <input
                {...register("value")}
                type="text"
                className="input-field"
                placeholder={getPlaceholderText()}
                list={`${watchType}-suggestions`}
              />
              <datalist id={`${watchType}-suggestions`}>
                {getValueSuggestions().map((suggestion) => (
                  <option key={suggestion} value={suggestion} />
                ))}
              </datalist>
              {errors.value && (
                <p className="mt-1 text-sm text-red-600">{errors.value.message}</p>
              )}
            </div>

            {/* Amount */}
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                Number of Contacts
              </label>
              <input
                {...register("amount")}
                type="number"
                min="1"
                max="100000"
                className="input-field"
              />
              {estimatedTime && (
                <p className="mt-1 text-sm text-gray-500">
                  Estimated processing time: {estimatedTime}
                </p>
              )}
              {errors.amount && (
                <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
              )}
            </div>

            {/* Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Export Format
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  {
                    value: "xlsx",
                    label: "Excel (XLSX)",
                    description: "Best for spreadsheet apps",
                    icon: "📊"
                  },
                  {
                    value: "txt",
                    label: "Text (TXT)",
                    description: "Simple text format",
                    icon: "📄"
                  },
                ].map((option) => (
                  <label key={option.value} className="relative">
                    <input
                      {...register("format")}
                      type="radio"
                      value={option.value}
                      className="sr-only"
                    />
                    <div className={`
                      cursor-pointer rounded-lg border p-3 transition-all
                      ${watch("format") === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                        : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                      }
                    `}>
                      <div className="flex items-center">
                        <span className="text-lg mr-2">{option.icon}</span>
                        <div>
                          <div className="text-sm font-medium">{option.label}</div>
                          <div className="text-xs text-gray-500">{option.description}</div>
                        </div>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              {errors.format && (
                <p className="mt-2 text-sm text-red-600">{errors.format.message}</p>
              )}
            </div>

            {/* Include Validation */}
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  {...register("includeValidation")}
                  type="checkbox"
                  className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label className="font-medium text-gray-700">
                  Include validation numbers
                </label>
                <div className="flex items-center mt-1">
                  <InformationCircleIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-gray-500">
                    Adds 1 validation number per 1000 contacts for testing
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row sm:justify-end space-y-3 sm:space-y-0 sm:space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="btn-secondary w-full sm:w-auto"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary w-full sm:w-auto"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Creating Extraction...
                  </>
                ) : (
                  <>
                    <DocumentArrowDownIcon className="-ml-1 mr-2 h-5 w-5" />
                    Create Extraction
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
