import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RecentActivity } from "./RecentActivity";

// Mock date-fns
vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn((date) => `${Math.floor((Date.now() - date.getTime()) / 60000)} minutos`),
}));

describe("RecentActivity", () => {
  it("renders activity list", () => {
    render(<RecentActivity />);

    expect(screen.getByText("Actividad Reciente")).toBeInTheDocument();
  });

  it("displays all activity items", () => {
    render(<RecentActivity />);

    expect(screen.getByText("Nueva extracción completada: Estado SINALOA")).toBeInTheDocument();
    expect(screen.getByText("Importación masiva de contactos")).toBeInTheDocument();
    expect(screen.getByText("Validación WhatsApp completada")).toBeInTheDocument();
    expect(screen.getByText("Exportación generada: Municipio JALISCO")).toBeInTheDocument();
    expect(screen.getByText("Límite de velocidad alcanzado en validador Instagram")).toBeInTheDocument();
  });

  it("displays activity details", () => {
    render(<RecentActivity />);

    expect(screen.getByText("1,500 contactos extraídos")).toBeInTheDocument();
    expect(screen.getByText("2,300 nuevos contactos")).toBeInTheDocument();
    expect(screen.getByText("850 números validados")).toBeInTheDocument();
    expect(screen.getByText("3,200 contactos en formato XLSX")).toBeInTheDocument();
    expect(screen.getByText("Cambio automático a método de respaldo")).toBeInTheDocument();
  });

  it("displays timestamps", () => {
    render(<RecentActivity />);

    // Check that timestamps are rendered (exact text depends on mock implementation)
    const timestamps = screen.getAllByText(/minutos/);
    expect(timestamps.length).toBeGreaterThan(0);
  });

  it("shows auto-refresh message", () => {
    render(<RecentActivity />);

    expect(screen.getByText("Actualización automática cada 30 segundos")).toBeInTheDocument();
  });

  it("has view all button", () => {
    render(<RecentActivity />);

    expect(screen.getByText("Ver todo")).toBeInTheDocument();
  });

  it("displays activity icons with proper styling", () => {
    render(<RecentActivity />);

    // Check for activity containers with dark theme styling
    const activityContainers = document.querySelectorAll('.bg-white\\/5');
    expect(activityContainers.length).toBeGreaterThan(0);
  });

  it("shows live indicators", () => {
    render(<RecentActivity />);

    // Check for animated pulse elements
    const pulseElements = document.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("applies proper text colors for dark theme", () => {
    render(<RecentActivity />);

    // Check for proper text color classes
    const whiteText = document.querySelectorAll('.text-white');
    const slateText = document.querySelectorAll('.text-slate-300, .text-slate-400');

    expect(whiteText.length).toBeGreaterThan(0);
    expect(slateText.length).toBeGreaterThan(0);
  });
});
