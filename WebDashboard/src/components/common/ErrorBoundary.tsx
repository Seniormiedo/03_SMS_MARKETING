import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import type { ErrorInfo, ReactNode } from "react";
import { Component } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Log error to monitoring service
    // TODO: Integrate with error tracking service (Sentry, LogRocket, etc.)
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon
                  className="h-8 w-8 text-red-400"
                  aria-hidden="true"
                />
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Something went wrong
                </h3>
                <div className="mt-2 text-sm text-gray-500">
                  <p>
                    An unexpected error occurred. Please try refreshing the page.
                  </p>
                </div>
              </div>
            </div>

            {process.env.NODE_ENV === "development" && this.state.error && (
              <div className="mt-4">
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-gray-700">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono overflow-auto">
                    <div className="text-red-600 font-bold">
                      {this.state.error.name}: {this.state.error.message}
                    </div>
                    <pre className="mt-2 whitespace-pre-wrap">
                      {this.state.error.stack}
                    </pre>
                  </div>
                </details>
              </div>
            )}

            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Refresh Page
              </button>
              <button
                onClick={() => (window.location.href = "/")}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
