import { clsx } from "clsx";
import React from "react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  color?: "blue" | "white" | "gray";
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "md",
  className,
  color = "blue",
}) => {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  const colorClasses = {
    blue: "border-gray-300 border-t-blue-600",
    white: "border-gray-300 border-t-white",
    gray: "border-gray-300 border-t-gray-600",
  };

  return (
    <div
      className={clsx(
        "animate-spin rounded-full border-2",
        sizeClasses[size],
        colorClasses[color],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};
