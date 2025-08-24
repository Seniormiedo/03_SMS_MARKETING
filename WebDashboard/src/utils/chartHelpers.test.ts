import { describe, expect, it } from "vitest";
import {
  generateChartColors,
  generateMockGrowthData,
  processLadaData,
  processStateData,
} from "./chartHelpers";

describe("chartHelpers", () => {
  describe("processStateData", () => {
    it("processes state data correctly", () => {
      const stateData = {
        SINALOA: 2500000,
        JALISCO: 2200000,
        CDMX: 2000000,
        NUEVO_LEON: 1800000,
        VERACRUZ: 1500000,
      };

      const result = processStateData(stateData);

      expect(result.labels).toEqual([
        "SINALOA",
        "JALISCO",
        "CDMX",
        "NUEVO_LEON",
        "VERACRUZ",
      ]);
      expect(result.data).toEqual([
        2500000, 2200000, 2000000, 1800000, 1500000,
      ]);
    });

    it("limits to top 10 states", () => {
      const stateData: Record<string, number> = {};
      for (let i = 0; i < 15; i++) {
        stateData[`STATE_${i}`] = 1000000 - i * 10000;
      }

      const result = processStateData(stateData);

      expect(result.labels).toHaveLength(10);
      expect(result.data).toHaveLength(10);
      expect(result.data[0]).toBeGreaterThan(result.data[9]);
    });

    it("sorts by value descending", () => {
      const stateData = {
        LOW: 1000,
        HIGH: 5000,
        MEDIUM: 3000,
      };

      const result = processStateData(stateData);

      expect(result.labels).toEqual(["HIGH", "MEDIUM", "LOW"]);
      expect(result.data).toEqual([5000, 3000, 1000]);
    });

    it("handles empty data", () => {
      const result = processStateData({});

      expect(result.labels).toEqual([]);
      expect(result.data).toEqual([]);
    });
  });

  describe("processLadaData", () => {
    it("processes LADA data correctly", () => {
      const ladaData = {
        "667": 850000,
        "33": 780000,
        "55": 720000,
        "81": 650000,
      };

      const result = processLadaData(ladaData);

      expect(result.labels).toEqual([
        "LADA 667",
        "LADA 33",
        "LADA 55",
        "LADA 81",
      ]);
      expect(result.data).toEqual([850000, 780000, 720000, 650000]);
    });

    it("limits to top 8 LADAs", () => {
      const ladaData: Record<string, number> = {};
      for (let i = 0; i < 12; i++) {
        ladaData[`${600 + i}`] = 1000000 - i * 10000;
      }

      const result = processLadaData(ladaData);

      expect(result.labels).toHaveLength(8);
      expect(result.data).toHaveLength(8);
      expect(result.data[0]).toBeGreaterThan(result.data[7]);
    });

    it("sorts by value descending", () => {
      const ladaData = {
        "100": 1000,
        "200": 5000,
        "300": 3000,
      };

      const result = processLadaData(ladaData);

      expect(result.labels).toEqual(["LADA 200", "LADA 300", "LADA 100"]);
      expect(result.data).toEqual([5000, 3000, 1000]);
    });

    it("handles empty data", () => {
      const result = processLadaData({});

      expect(result.labels).toEqual([]);
      expect(result.data).toEqual([]);
    });
  });

  describe("generateChartColors", () => {
    it("generates correct number of colors", () => {
      const colors = generateChartColors(5);
      expect(colors).toHaveLength(5);
    });

    it("generates different colors", () => {
      const colors = generateChartColors(10);
      const uniqueColors = new Set(colors);
      expect(uniqueColors.size).toBe(colors.length);
    });

    it("handles zero count", () => {
      const colors = generateChartColors(0);
      expect(colors).toEqual([]);
    });

    it("generates valid hex colors", () => {
      const colors = generateChartColors(3);
      colors.forEach((color) => {
        expect(color).toMatch(/^#[0-9A-F]{6}$/i);
      });
    });

    it("cycles through available colors", () => {
      const colors1 = generateChartColors(2);
      const colors2 = generateChartColors(2);

      // Should be consistent
      expect(colors1).toEqual(colors2);
    });
  });

  describe("generateMockGrowthData", () => {
    it("generates growth data with correct structure", () => {
      const data = generateMockGrowthData();

      expect(data).toHaveProperty("labels");
      expect(data).toHaveProperty("datasets");
      expect(Array.isArray(data.labels)).toBe(true);
      expect(Array.isArray(data.datasets)).toBe(true);
    });

    it("generates 6 months of data", () => {
      const data = generateMockGrowthData();

      expect(data.labels).toHaveLength(6);
    });

    it("generates two datasets", () => {
      const data = generateMockGrowthData();

      expect(data.datasets).toHaveLength(2);
      expect(data.datasets[0]).toHaveProperty("label");
      expect(data.datasets[1]).toHaveProperty("label");
    });

    it("generates realistic data values", () => {
      const data = generateMockGrowthData();

      data.datasets.forEach((dataset) => {
        expect(Array.isArray(dataset.data)).toBe(true);
        expect(dataset.data).toHaveLength(6);

        dataset.data.forEach((value) => {
          expect(typeof value).toBe("number");
          expect(value).toBeGreaterThanOrEqual(0);
          expect(value).toBeLessThan(1000000);
        });
      });
    });

    it("includes proper styling", () => {
      const data = generateMockGrowthData();

      data.datasets.forEach((dataset) => {
        expect(dataset).toHaveProperty("borderColor");
        expect(dataset).toHaveProperty("backgroundColor");
        expect(dataset).toHaveProperty("tension");
        expect(dataset).toHaveProperty("fill");
      });
    });

    it("generates consistent data on multiple calls", () => {
      const data1 = generateMockGrowthData();
      const data2 = generateMockGrowthData();

      expect(data1.labels).toEqual(data2.labels);
      expect(data1.datasets[0].label).toEqual(data2.datasets[0].label);
      expect(data1.datasets[1].label).toEqual(data2.datasets[1].label);
    });
  });
});
