// Mock data for development and testing
export const MOCK_CONTACT_STATS = {
  totalContacts: 31800000,
  contactsByState: {
    SINALOA: 2500000,
    JALISCO: 2200000,
    CDMX: 2000000,
    "NUEVO LEON": 1800000,
    VERACRUZ: 1600000,
    PUEBLA: 1400000,
    GUANAJUATO: 1300000,
    CHIHUAHUA: 1200000,
    MICHOACAN: 1100000,
    OAXACA: 1000000,
    TAMAULIPAS: 950000,
    SONORA: 900000,
  },
  contactsByLada: {
    "667": 850000, // Culiacán
    "33": 780000, // Guadalajara
    "55": 720000, // CDMX
    "81": 650000, // Monterrey
    "229": 580000, // Veracruz
    "222": 520000, // Puebla
    "461": 480000, // León
    "614": 450000, // Chihuahua
    "443": 420000, // Morelia
    "951": 380000, // Oaxaca
  },
  recentExtractions: 23,
};

// Mock API responses
export const createMockApiResponse = <T>(data: T) => ({
  data,
  success: true,
  message: "Success",
});

// Mock contact data
export const MOCK_CONTACTS = Array.from({ length: 50 }, (_, i) => ({
  id: `contact_${i + 1}`,
  phoneE164: `+521667${String(Math.floor(Math.random() * 9000000) + 1000000)}`,
  phoneNational: `667${String(Math.floor(Math.random() * 9000000) + 1000000)}`,
  lada: "667",
  stateName: "SINALOA",
  municipality: "CULIACAN",
  createdAt: new Date(
    Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000
  ).toISOString(),
  updatedAt: new Date().toISOString(),
}));
