import { ChartBarIcon, ChartPieIcon } from "@heroicons/react/24/outline";
import React from "react";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import { DEFAULT_CHART_OPTIONS, DOUGHNUT_OPTIONS } from "../../utils/chartConfig";
import {
  generateChartColors,
  generateMockGrowthData,
  processLadaData,
  processStateData,
} from "../../utils/chartHelpers";

interface ChartsGridProps {
  stats: {
    totalContacts: number;
    contactsByState: Record<string, number>;
    contactsByLada: Record<string, number>;
    recentExtractions: number;
  };
}

export const ChartsGrid: React.FC<ChartsGridProps> = ({ stats }) => {
  // Provide default values if stats is undefined
  const safeStats = stats || {
    totalContacts: 0,
    contactsByState: {},
    contactsByLada: {},
    recentExtractions: 0,
  };

  // Process data for charts
  const stateData = processStateData(safeStats.contactsByState);
  const ladaData = processLadaData(safeStats.contactsByLada);
  const growthData = generateMockGrowthData();

  // Contacts by State Chart Data
  const stateChartData = {
    labels: stateData.labels,
    datasets: [
      {
        label: "Contacts by State",
        data: stateData.data,
        backgroundColor: generateChartColors(stateData.labels.length),
        borderWidth: 0,
        borderRadius: 4,
      },
    ],
  };

  // LADA Distribution Chart Data
  const ladaChartData = {
    labels: ladaData.labels,
    datasets: [
      {
        data: ladaData.data,
        backgroundColor: generateChartColors(ladaData.labels.length),
        borderWidth: 2,
        borderColor: "#ffffff",
      },
    ],
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Contacts by State */}
      <div className="bg-white/5 backdrop-blur-sm p-6 rounded-xl border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ChartBarIcon className="w-5 h-5 text-blue-300" />
            <span>Contactos por Estado (Top 10)</span>
          </h3>
          <div className="text-sm text-slate-400">
            {stateData.data.reduce((a, b) => a + b, 0).toLocaleString()} total
          </div>
        </div>
        <div className="relative w-full h-72 max-w-full overflow-hidden chart-container">
          <div style={{
            position: 'relative',
            height: '288px',
            width: '100%',
            maxWidth: '100%',
            maxHeight: '288px',
            overflow: 'hidden'
          }}>
            <Bar
              data={stateChartData}
              options={{
                ...DEFAULT_CHART_OPTIONS,
                maintainAspectRatio: false,
                responsive: false,
                aspectRatio: 2,
                plugins: {
                  ...DEFAULT_CHART_OPTIONS.plugins,
                  legend: {
                    ...DEFAULT_CHART_OPTIONS.plugins.legend,
                    labels: {
                      ...DEFAULT_CHART_OPTIONS.plugins.legend.labels,
                      color: '#e2e8f0'
                    }
                  }
                },
                scales: {
                  ...DEFAULT_CHART_OPTIONS.scales,
                  x: {
                    ...DEFAULT_CHART_OPTIONS.scales.x,
                    ticks: {
                      ...DEFAULT_CHART_OPTIONS.scales.x.ticks,
                      color: '#94a3b8'
                    }
                  },
                  y: {
                    ...DEFAULT_CHART_OPTIONS.scales.y,
                    ticks: {
                      ...DEFAULT_CHART_OPTIONS.scales.y.ticks,
                      color: '#94a3b8'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* LADA Distribution */}
      <div className="bg-white/5 backdrop-blur-sm p-6 rounded-xl border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ChartPieIcon className="w-5 h-5 text-purple-300" />
            <span>Distribución por LADA (Top 8)</span>
          </h3>
          <div className="text-sm text-slate-400">
            {ladaData.data.reduce((a, b) => a + b, 0).toLocaleString()} contactos
          </div>
        </div>
        <div className="relative w-full h-72 max-w-full flex items-center justify-center overflow-hidden chart-container">
          <div style={{
            position: 'relative',
            height: '288px',
            width: '288px',
            maxWidth: '288px',
            maxHeight: '288px',
            overflow: 'hidden'
          }}>
            <Doughnut
              data={ladaChartData}
              options={{
                ...DOUGHNUT_OPTIONS,
                maintainAspectRatio: false,
                responsive: false,
                aspectRatio: 1,
                plugins: {
                  ...DOUGHNUT_OPTIONS.plugins,
                  legend: {
                    ...DOUGHNUT_OPTIONS.plugins.legend,
                    labels: {
                      ...DOUGHNUT_OPTIONS.plugins.legend.labels,
                      color: '#e2e8f0'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Monthly Growth */}
      <div className="bg-white/5 backdrop-blur-sm p-6 rounded-xl border border-white/10 lg:col-span-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ChartBarIcon className="w-5 h-5 text-emerald-300" />
            <span>Tendencia de Crecimiento Mensual</span>
          </h3>
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-400 rounded-full mr-2"></div>
              <span className="text-slate-300">Nuevos Contactos</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-emerald-400 rounded-full mr-2"></div>
              <span className="text-slate-300">Validaciones</span>
            </div>
          </div>
        </div>
        <div className="relative w-full h-72 max-w-full overflow-hidden chart-container">
          <div style={{
            position: 'relative',
            height: '288px',
            width: '100%',
            maxWidth: '100%',
            maxHeight: '288px',
            overflow: 'hidden'
          }}>
            <Line
              data={growthData}
              options={{
                ...DEFAULT_CHART_OPTIONS,
                maintainAspectRatio: false,
                responsive: false,
                aspectRatio: 2.5,
                plugins: {
                  ...DEFAULT_CHART_OPTIONS.plugins,
                  legend: {
                    ...DEFAULT_CHART_OPTIONS.plugins.legend,
                    labels: {
                      ...DEFAULT_CHART_OPTIONS.plugins.legend.labels,
                      color: '#e2e8f0'
                    }
                  }
                },
                scales: {
                  ...DEFAULT_CHART_OPTIONS.scales,
                  x: {
                    ...DEFAULT_CHART_OPTIONS.scales.x,
                    ticks: {
                      ...DEFAULT_CHART_OPTIONS.scales.x.ticks,
                      color: '#94a3b8'
                    }
                  },
                  y: {
                    ...DEFAULT_CHART_OPTIONS.scales.y,
                    ticks: {
                      ...DEFAULT_CHART_OPTIONS.scales.y.ticks,
                      color: '#94a3b8'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
