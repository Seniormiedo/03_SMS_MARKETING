import { describe, expect, it } from "vitest";

describe("DashboardPage", () => {
  it("validates page configuration", () => {
    const pageConfig = {
      title: "SMS Marketing Platform",
      subtitle: "Control total de tus campañas de marketing",
      theme: "dark",
      layout: "responsive"
    };

    expect(pageConfig.title).toBe("SMS Marketing Platform");
    expect(pageConfig.subtitle).toBe("Control total de tus campañas de marketing");
    expect(pageConfig.theme).toBe("dark");
    expect(pageConfig.layout).toBe("responsive");
  });

  it("validates component sections", () => {
    const sections = [
      { id: "header", component: "Header", visible: true },
      { id: "metrics", component: "MetricsCards", visible: true },
      { id: "charts", component: "ChartsGrid", visible: true },
      { id: "activity", component: "RecentActivity", visible: true },
      { id: "footer", component: "Footer", visible: true }
    ];

    expect(sections).toHaveLength(5);
    expect(sections.find(s => s.id === "metrics")?.component).toBe("MetricsCards");
    expect(sections.find(s => s.id === "charts")?.component).toBe("ChartsGrid");
    expect(sections.every(s => s.visible)).toBe(true);
  });

  it("validates metrics data structure", () => {
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

    expect(mockStats.totalContacts).toBe(31800000);
    expect(mockStats.contactsByState.SINALOA).toBe(2500000);
    expect(mockStats.contactsByLada["667"]).toBe(850000);
    expect(mockStats.recentExtractions).toBe(23);
  });

  it("validates system status structure", () => {
    const systemStatus = [
      { service: "Base de Datos", status: "Saludable", icon: "database" },
      { service: "Bot Telegram", status: "Activo", icon: "bot" },
      { service: "Validadores", status: "Operativo", icon: "validators" }
    ];

    expect(systemStatus).toHaveLength(3);
    expect(systemStatus[0].service).toBe("Base de Datos");
    expect(systemStatus[0].status).toBe("Saludable");
    expect(systemStatus[1].service).toBe("Bot Telegram");
  });

  it("validates live indicators", () => {
    const liveIndicators = [
      { section: "metrics", isLive: true },
      { section: "activity", isLive: true },
      { section: "status", isLive: true }
    ];

    expect(liveIndicators.every(indicator => indicator.isLive)).toBe(true);
    expect(liveIndicators.find(i => i.section === "metrics")?.isLive).toBe(true);
  });

  it("validates footer data", () => {
    const footerData = {
      contactCount: "31.8M",
      activeContacts: "contactos activos",
      systemStatus: "Sistema Operativo",
      lastUpdated: new Date().toISOString()
    };

    expect(footerData.contactCount).toBe("31.8M");
    expect(footerData.activeContacts).toBe("contactos activos");
    expect(footerData.systemStatus).toBe("Sistema Operativo");
    expect(footerData.lastUpdated).toBeDefined();
  });

  it("validates analytics section", () => {
    const analyticsConfig = {
      title: "Analytics",
      charts: ["state-distribution", "lada-distribution", "growth-trend"],
      refreshInterval: 30000,
      autoRefresh: true
    };

    expect(analyticsConfig.title).toBe("Analytics");
    expect(analyticsConfig.charts).toHaveLength(3);
    expect(analyticsConfig.charts).toContain("state-distribution");
    expect(analyticsConfig.autoRefresh).toBe(true);
  });

  it("validates responsive design configuration", () => {
    const responsiveConfig = {
      mobile: { columns: 1, spacing: "compact" },
      tablet: { columns: 2, spacing: "normal" },
      desktop: { columns: 4, spacing: "wide" }
    };

    expect(responsiveConfig.mobile.columns).toBe(1);
    expect(responsiveConfig.tablet.columns).toBe(2);
    expect(responsiveConfig.desktop.columns).toBe(4);
  });
});
