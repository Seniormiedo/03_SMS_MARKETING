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
  // Process data for charts
  const stateData = processStateData(stats.contactsByState);
  const ladaData = processLadaData(stats.contactsByLada);
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
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Contacts by State (Top 10)
          </h3>
          <div className="text-sm text-gray-500">
            {stateData.data.reduce((a, b) => a + b, 0).toLocaleString()} total
          </div>
        </div>
        <div className="h-80">
          <Bar data={stateChartData} options={DEFAULT_CHART_OPTIONS} />
        </div>
      </div>

      {/* LADA Distribution */}
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            LADA Distribution (Top 8)
          </h3>
          <div className="text-sm text-gray-500">
            {ladaData.data.reduce((a, b) => a + b, 0).toLocaleString()} contacts
          </div>
        </div>
        <div className="h-80">
          <Doughnut data={ladaChartData} options={DOUGHNUT_OPTIONS} />
        </div>
      </div>

      {/* Monthly Growth */}
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow lg:col-span-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Monthly Growth Trend
          </h3>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              New Contacts
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              Validations
            </div>
          </div>
        </div>
        <div className="h-80">
          <Line data={growthData} options={DEFAULT_CHART_OPTIONS} />
        </div>
      </div>
    </div>
  );
};
