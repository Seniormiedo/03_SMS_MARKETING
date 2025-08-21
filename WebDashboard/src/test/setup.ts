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
