import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Default chart colors palette
export const CHART_COLORS = {
  primary: "#3b82f6",
  secondary: "#ef4444",
  success: "#10b981",
  warning: "#f59e0b",
  purple: "#8b5cf6",
  cyan: "#06b6d4",
  lime: "#84cc16",
  orange: "#f97316",
  pink: "#ec4899",
  indigo: "#6366f1",
};

export const CHART_COLOR_ARRAY = Object.values(CHART_COLORS);

// Default responsive chart options
export const DEFAULT_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top" as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
          family: "Inter, system-ui, sans-serif",
        },
      },
    },
    tooltip: {
      backgroundColor: "rgba(0, 0, 0, 0.8)",
      titleColor: "#fff",
      bodyColor: "#fff",
      borderColor: "#374151",
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      titleFont: {
        size: 14,
        weight: "bold" as const,
      },
      bodyFont: {
        size: 13,
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        font: {
          size: 12,
          family: "Inter, system-ui, sans-serif",
        },
        color: "#6b7280",
      },
    },
    y: {
      beginAtZero: true,
      grid: {
        color: "rgba(0, 0, 0, 0.1)",
        lineWidth: 1,
      },
      ticks: {
        font: {
          size: 12,
          family: "Inter, system-ui, sans-serif",
        },
        color: "#6b7280",
      },
    },
  },
};

// Doughnut chart specific options
export const DOUGHNUT_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "bottom" as const,
      labels: {
        usePointStyle: true,
        padding: 15,
        font: {
          size: 12,
          family: "Inter, system-ui, sans-serif",
        },
      },
    },
    tooltip: {
      backgroundColor: "rgba(0, 0, 0, 0.8)",
      titleColor: "#fff",
      bodyColor: "#fff",
      callbacks: {
        label: function (context: {
          label: string;
          parsed: number;
          dataset: { data: number[] };
        }) {
          const label = context.label || "";
          const value = context.parsed;
          const total = context.dataset.data.reduce(
            (a: number, b: number) => a + b,
            0
          );
          const percentage = ((value / total) * 100).toFixed(1);
          return `${label}: ${value.toLocaleString()} (${percentage}%)`;
        },
      },
    },
  },
  cutout: "60%",
};
