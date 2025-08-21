import type { ApiResponse, PaginatedResponse } from "../../types/Api";
import type {
  Contact,
  ContactFilters,
  ExtractionRequest,
  ExtractionResult,
} from "../../types/Contact";
import { apiClient } from "./ApiClient";
import {
  createMockApiResponse,
  MOCK_CONTACT_STATS,
  MOCK_CONTACTS,
} from "./mockData";

class ContactsApiService {
  async getContacts(
    filters: ContactFilters,
    page: number = 1,
    pageSize: number = 50
  ): Promise<ApiResponse<PaginatedResponse<Contact>>> {
    const params = new URLSearchParams();
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    // Add filters to params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        if (typeof value === "object" && "start" in value && "end" in value) {
          // Handle date range
          params.append(`${key}_start`, value.start);
          params.append(`${key}_end`, value.end);
        } else {
          params.append(key, value.toString());
        }
      }
    });

    try {
      return await apiClient.get(`/dashboard/contacts?${params}`);
    } catch {
      // Return mock data if backend is not available
      const filteredContacts = this.filterMockContacts(MOCK_CONTACTS, filters);
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      const paginatedContacts = filteredContacts.slice(startIndex, endIndex);

      return createMockApiResponse({
        data: paginatedContacts,
        total: filteredContacts.length,
        page,
        pageSize,
        totalPages: Math.ceil(filteredContacts.length / pageSize),
      });
    }
  }

  private filterMockContacts(
    contacts: typeof MOCK_CONTACTS,
    filters: ContactFilters
  ): typeof MOCK_CONTACTS {
    return contacts.filter((contact) => {
      if (
        filters.searchQuery &&
        !contact.phoneNational.includes(filters.searchQuery)
      ) {
        return false;
      }
      if (filters.state && contact.stateName !== filters.state) {
        return false;
      }
      if (
        filters.municipality &&
        contact.municipality !== filters.municipality
      ) {
        return false;
      }
      if (filters.lada && contact.lada !== filters.lada) {
        return false;
      }
      return true;
    });
  }

  async getContactById(id: string): Promise<ApiResponse<Contact>> {
    return apiClient.get(`/contacts/${id}`);
  }

  async getStats(): Promise<
    ApiResponse<{
      totalContacts: number;
      contactsByState: Record<string, number>;
      contactsByLada: Record<string, number>;
      recentExtractions: number;
    }>
  > {
    try {
      return await apiClient.get("/dashboard/stats");
    } catch {
      // Return mock data if backend is not available
      return createMockApiResponse(MOCK_CONTACT_STATS);
    }
  }

  async createExtraction(
    request: ExtractionRequest
  ): Promise<ApiResponse<ExtractionResult>> {
    return apiClient.post("/api/v1/extractions", request);
  }

  async getExtractions(): Promise<ApiResponse<ExtractionResult[]>> {
    return apiClient.get("/api/v1/extractions");
  }

  async getExtractionById(id: string): Promise<ApiResponse<ExtractionResult>> {
    return apiClient.get(`/api/v1/extractions/${id}`);
  }

  async downloadExtraction(id: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `/api/v1/extractions/${id}/download`
    );
    return response.data as Blob;
  }

  async searchContacts(query: string): Promise<ApiResponse<Contact[]>> {
    return apiClient.get(
      `/api/v1/contacts/search?q=${encodeURIComponent(query)}`
    );
  }

  async getStates(): Promise<ApiResponse<string[]>> {
    return apiClient.get("/dashboard/states");
  }

  async getMunicipalities(state: string): Promise<ApiResponse<string[]>> {
    return apiClient.get(
      `/dashboard/municipalities?state=${encodeURIComponent(state)}`
    );
  }

  async getLadas(): Promise<ApiResponse<string[]>> {
    return apiClient.get("/dashboard/ladas");
  }
}

export const contactsApi = new ContactsApiService();
