import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricsCards } from "./MetricsCards";

const mockStats = {
  totalContacts: 31800000,
  contactsByState: {
    SINALOA: 2500000,
    JALISCO: 2200000,
    CDMX: 2000000,
  },
  contactsByLada: {
    "667": 850000,
    "33": 780000,
    "55": 720000,
  },
  recentExtractions: 23,
};

describe("MetricsCards", () => {
  it("renders all metric cards", () => {
    render(<MetricsCards stats={mockStats} />);

    expect(screen.getByText("Total Contacts")).toBeInTheDocument();
    expect(screen.getByText("States Covered")).toBeInTheDocument();
    expect(screen.getByText("Recent Extractions")).toBeInTheDocument();
    expect(screen.getByText("Validation Rate")).toBeInTheDocument();
  });

  it("displays formatted total contacts", () => {
    render(<MetricsCards stats={mockStats} />);

    expect(screen.getByText("31,800,000")).toBeInTheDocument();
  });

  it("displays correct states count", () => {
    render(<MetricsCards stats={mockStats} />);

    expect(screen.getByText("3")).toBeInTheDocument(); // 3 states in mock data
  });

  it("displays recent extractions count", () => {
    render(<MetricsCards stats={mockStats} />);

    expect(screen.getByText("23")).toBeInTheDocument();
  });

  it("displays validation rate", () => {
    render(<MetricsCards stats={mockStats} />);

    expect(screen.getByText("94.2%")).toBeInTheDocument();
  });
});
