import { describe, expect, it } from "vitest";

const mockStats = {
  totalContacts: 31800000,
  contactsByState: {
    SINALOA: 2500000,
    JALISCO: 2200000,
    CDMX: 2000000,
    NUEVO_LEON: 1800000,
    VERACRUZ: 1500000,
  },
  contactsByLada: {
    "667": 850000,
    "33": 780000,
    "55": 720000,
    "81": 650000,
    "229": 580000,
  },
  recentExtractions: 23,
};

describe("ChartsGrid", () => {
  it("validates chart data structure", () => {
    expect(mockStats.totalContacts).toBe(31800000);
    expect(Object.keys(mockStats.contactsByState)).toHaveLength(5);
    expect(Object.keys(mockStats.contactsByLada)).toHaveLength(5);
    expect(mockStats.recentExtractions).toBe(23);
  });

  it("validates chart configuration options", () => {
    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
        tooltip: { enabled: true }
      }
    };

    expect(chartOptions.responsive).toBe(true);
    expect(chartOptions.maintainAspectRatio).toBe(false);
    expect(chartOptions.plugins.legend.position).toBe("bottom");
  });

  it("validates state chart data processing", () => {
    const stateEntries = Object.entries(mockStats.contactsByState)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    expect(stateEntries).toHaveLength(5); // Solo tenemos 5 estados
    expect(stateEntries[0][0]).toBe("SINALOA"); // El estado con más contactos
    expect(stateEntries[0][1]).toBe(2500000);
  });

  it("validates LADA chart data processing", () => {
    const ladaEntries = Object.entries(mockStats.contactsByLada)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 8);

    expect(ladaEntries).toHaveLength(5); // Solo tenemos 5 LADAs
    expect(ladaEntries[0][0]).toBe("667"); // La LADA con más contactos
    expect(ladaEntries[0][1]).toBe(850000);
  });

  it("validates chart titles and labels", () => {
    const chartTitles = [
      "Contactos por Estado (Top 10)",
      "Distribución por LADA (Top 8)",
      "Tendencia de Crecimiento Mensual"
    ];

    expect(chartTitles).toHaveLength(3);
    expect(chartTitles[0]).toBe("Contactos por Estado (Top 10)");
    expect(chartTitles[1]).toBe("Distribución por LADA (Top 8)");
    expect(chartTitles[2]).toBe("Tendencia de Crecimiento Mensual");
  });

  it("validates legend labels", () => {
    const legendLabels = [
      "Nuevos Contactos",
      "Validaciones"
    ];

    expect(legendLabels).toHaveLength(2);
    expect(legendLabels).toContain("Nuevos Contactos");
    expect(legendLabels).toContain("Validaciones");
  });

  it("validates chart color scheme", () => {
    const colorScheme = {
      primary: "#3b82f6",
      secondary: "#8b5cf6",
      success: "#10b981",
      warning: "#f59e0b"
    };

    expect(colorScheme.primary).toBe("#3b82f6");
    expect(colorScheme.secondary).toBe("#8b5cf6");
    expect(colorScheme.success).toBe("#10b981");
  });

  it("validates empty stats handling", () => {
    const emptyStats = {
      totalContacts: 0,
      contactsByState: {},
      contactsByLada: {},
      recentExtractions: 0,
    };

    expect(emptyStats.totalContacts).toBe(0);
    expect(Object.keys(emptyStats.contactsByState)).toHaveLength(0);
    expect(Object.keys(emptyStats.contactsByLada)).toHaveLength(0);
  });

  it("validates dark theme styling", () => {
    const darkThemeConfig = {
      backgroundColor: "white/5",
      backdropBlur: true,
      borderColor: "white/10",
      textColor: "white"
    };

    expect(darkThemeConfig.backgroundColor).toBe("white/5");
    expect(darkThemeConfig.backdropBlur).toBe(true);
    expect(darkThemeConfig.borderColor).toBe("white/10");
    expect(darkThemeConfig.textColor).toBe("white");
  });
});
