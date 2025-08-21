import React from "react";
import { Bar } from "react-chartjs-2";
import { CHART_COLOR_ARRAY, DEFAULT_CHART_OPTIONS } from "../../utils/chartConfig";

// Test chart component to verify Chart.js is working
export const TestChart: React.FC = () => {
  const testData = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May"],
    datasets: [
      {
        label: "Test Data",
        data: [12, 19, 3, 5, 2],
        backgroundColor: CHART_COLOR_ARRAY.slice(0, 5),
        borderWidth: 0,
        borderRadius: 4,
      },
    ],
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Chart.js Test
      </h3>
      <div className="h-64">
        <Bar data={testData} options={DEFAULT_CHART_OPTIONS} />
      </div>
    </div>
  );
};
