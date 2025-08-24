import "@testing-library/jest-dom";
import React from "react";

// Mock Chart.js to avoid canvas issues in tests
import { vi } from "vitest";

// Mock Chart.js
vi.mock("react-chartjs-2", () => ({
  Bar: vi.fn(() =>
    React.createElement("div", { "data-testid": "bar-chart" }, "Bar Chart")
  ),
  Line: vi.fn(() =>
    React.createElement("div", { "data-testid": "line-chart" }, "Line Chart")
  ),
  Doughnut: vi.fn(() =>
    React.createElement(
      "div",
      { "data-testid": "doughnut-chart" },
      "Doughnut Chart"
    )
  ),
}));

// Mock Heroicons
vi.mock("@heroicons/react/24/outline", () => ({
  ChartBarIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "chart-bar-icon" },
      "ChartBarIcon"
    )
  ),
  ChartPieIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "chart-pie-icon" },
      "ChartPieIcon"
    )
  ),
  SparklesIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "sparkles-icon" },
      "SparklesIcon"
    )
  ),
  CpuChipIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "cpu-chip-icon" },
      "CpuChipIcon"
    )
  ),
  SignalIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "signal-icon" },
      "SignalIcon"
    )
  ),
  DocumentArrowDownIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "document-arrow-down-icon" },
      "DocumentArrowDownIcon"
    )
  ),
  CheckBadgeIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "check-badge-icon" },
      "CheckBadgeIcon"
    )
  ),
  ExclamationTriangleIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "exclamation-triangle-icon" },
      "ExclamationTriangleIcon"
    )
  ),
  UserPlusIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "user-plus-icon" },
      "UserPlusIcon"
    )
  ),
  CheckCircleIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "check-circle-icon" },
      "CheckCircleIcon"
    )
  ),
  DocumentTextIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "document-text-icon" },
      "DocumentTextIcon"
    )
  ),
  UsersIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "users-icon" },
      "UsersIcon"
    )
  ),
  ClockIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "clock-icon" },
      "ClockIcon"
    )
  ),
  PlusIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "plus-icon" },
      "PlusIcon"
    )
  ),
  ArrowDownTrayIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "arrow-down-tray-icon" },
      "ArrowDownTrayIcon"
    )
  ),
  Cog6ToothIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "cog-6-tooth-icon" },
      "Cog6ToothIcon"
    )
  ),
  BellIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "bell-icon" },
      "BellIcon"
    )
  ),
  ArrowPathIcon: vi.fn((props) =>
    React.createElement(
      "div",
      { ...props, "data-testid": "arrow-path-icon" },
      "ArrowPathIcon"
    )
  ),
}));

// Mock window.localStorage
Object.defineProperty(window, "localStorage", {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
