import type { PayloadAction } from "@reduxjs/toolkit";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { contactsApi } from "../../services/api/ContactsApi";
import type {
  Contact,
  ContactFilters,
  ExtractionRequest,
  ExtractionResult,
} from "../../types/Contact";

interface ContactsState {
  contacts: Contact[];
  totalContacts: number;
  loading: boolean;
  error: string | null;
  filters: ContactFilters;
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
  };
  extractions: ExtractionResult[];
  stats: {
    totalContacts: number;
    contactsByState: Record<string, number>;
    contactsByLada: Record<string, number>;
    recentExtractions: number;
  };
}

const initialState: ContactsState = {
  contacts: [],
  totalContacts: 0,
  loading: false,
  error: null,
  filters: {},
  pagination: {
    page: 1,
    pageSize: 50,
    totalPages: 0,
  },
  extractions: [],
  stats: {
    totalContacts: 0,
    contactsByState: {},
    contactsByLada: {},
    recentExtractions: 0,
  },
};

// Async thunks
export const fetchContacts = createAsyncThunk(
  "contacts/fetchContacts",
  async ({
    filters,
    page,
    pageSize,
  }: {
    filters: ContactFilters;
    page: number;
    pageSize: number;
  }) => {
    const response = await contactsApi.getContacts(filters, page, pageSize);
    return response.data;
  }
);

export const fetchContactStats = createAsyncThunk(
  "contacts/fetchStats",
  async () => {
    const response = await contactsApi.getStats();
    return response.data;
  }
);

export const createExtraction = createAsyncThunk(
  "contacts/createExtraction",
  async (request: ExtractionRequest) => {
    const response = await contactsApi.createExtraction(request);
    return response.data;
  }
);

export const fetchExtractions = createAsyncThunk(
  "contacts/fetchExtractions",
  async () => {
    const response = await contactsApi.getExtractions();
    return response.data;
  }
);

const contactsSlice = createSlice({
  name: "contacts",
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ContactFilters>) => {
      state.filters = action.payload;
      state.pagination.page = 1; // Reset to first page when filters change
    },
    clearFilters: (state) => {
      state.filters = {};
      state.pagination.page = 1;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.pagination.page = action.payload;
    },
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pagination.pageSize = action.payload;
      state.pagination.page = 1;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch contacts
      .addCase(fetchContacts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchContacts.fulfilled, (state, action) => {
        state.loading = false;
        state.contacts = action.payload.data || [];
        state.totalContacts = action.payload.total || 0;
        state.pagination.totalPages = Math.ceil(
          (action.payload.total || 0) / state.pagination.pageSize
        );
      })
      .addCase(fetchContacts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "Failed to fetch contacts";
      })
      // Fetch stats
      .addCase(fetchContactStats.fulfilled, (state, action) => {
        state.stats = action.payload;
      })
      // Create extraction
      .addCase(createExtraction.fulfilled, (state, action) => {
        state.extractions.unshift(action.payload);
      })
      // Fetch extractions
      .addCase(fetchExtractions.fulfilled, (state, action) => {
        state.extractions = action.payload;
      });
  },
});

export const { setFilters, clearFilters, setPage, setPageSize, clearError } =
  contactsSlice.actions;
export default contactsSlice.reducer;
