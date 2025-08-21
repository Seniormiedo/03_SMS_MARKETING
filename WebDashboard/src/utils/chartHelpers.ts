import { CHART_COLOR_ARRAY } from "./chartConfig";

/**
 * Generate colors for chart datasets
 */
export const generateChartColors = (count: number): string[] => {
  const colors = [];
  for (let i = 0; i < count; i++) {
    colors.push(CHART_COLOR_ARRAY[i % CHART_COLOR_ARRAY.length]);
  }
  return colors;
};

/**
 * Format numbers for chart display
 */
export const formatChartNumber = (value: number): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
};

/**
 * Create gradient for line charts
 */
export const createGradient = (
  ctx: CanvasRenderingContext2D,
  color: string,
  opacity: number = 0.1
): CanvasGradient => {
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(
    0,
    color.replace("rgb", "rgba").replace(")", `, ${opacity})`)
  );
  gradient.addColorStop(1, color.replace("rgb", "rgba").replace(")", ", 0)"));
  return gradient;
};

/**
 * Process data for state distribution chart
 */
export const processStateData = (contactsByState: Record<string, number>) => {
  const entries = Object.entries(contactsByState)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10); // Top 10 states

  return {
    labels: entries.map(([state]) => state),
    data: entries.map(([, count]) => count),
  };
};

/**
 * Process data for LADA distribution chart
 */
export const processLadaData = (contactsByLada: Record<string, number>) => {
  const entries = Object.entries(contactsByLada)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8); // Top 8 LADAs

  return {
    labels: entries.map(([lada]) => `LADA ${lada}`),
    data: entries.map(([, count]) => count),
  };
};

/**
 * Generate mock monthly data for growth chart
 */
export const generateMockGrowthData = () => {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
  const baseContacts = 1000;
  const baseValidations = 800;

  return {
    labels: months,
    datasets: [
      {
        label: "New Contacts",
        data: months.map(
          (_, i) => baseContacts + Math.random() * 2000 + i * 500
        ),
        borderColor: CHART_COLOR_ARRAY[0],
        backgroundColor: `${CHART_COLOR_ARRAY[0]}20`,
        fill: true,
        tension: 0.4,
      },
      {
        label: "Validations",
        data: months.map(
          (_, i) => baseValidations + Math.random() * 1500 + i * 400
        ),
        borderColor: CHART_COLOR_ARRAY[2],
        backgroundColor: `${CHART_COLOR_ARRAY[2]}20`,
        fill: true,
        tension: 0.4,
      },
    ],
  };
};
