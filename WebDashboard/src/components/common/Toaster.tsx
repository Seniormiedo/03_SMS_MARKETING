import React from "react";
import { Toaster as HotToaster } from "react-hot-toast";

export const Toaster: React.FC = () => {
  return (
    <HotToaster
      position="top-right"
      toastOptions={{
        // Default options for all toasts
        duration: 4000,
        style: {
          background: "#363636",
          color: "#fff",
          fontSize: "14px",
          borderRadius: "8px",
          padding: "12px 16px",
          maxWidth: "500px",
        },
        // Success toasts
        success: {
          style: {
            background: "#10b981",
          },
          iconTheme: {
            primary: "#fff",
            secondary: "#10b981",
          },
        },
        // Error toasts
        error: {
          style: {
            background: "#ef4444",
          },
          iconTheme: {
            primary: "#fff",
            secondary: "#ef4444",
          },
        },
        // Loading toasts
        loading: {
          style: {
            background: "#3b82f6",
          },
        },
      }}
    />
  );
};
