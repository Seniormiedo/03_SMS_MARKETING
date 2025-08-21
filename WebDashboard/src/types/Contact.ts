export interface Contact {
  id: string;
  phoneE164: string;
  phoneNational: string;
  lada: string;
  stateName: string;
  municipality: string;
  createdAt: string;
  updatedAt: string;
}

export interface ContactFilters {
  state?: string;
  municipality?: string;
  lada?: string;
  searchQuery?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface ExtractionRequest {
  type: "state" | "municipality" | "lada";
  value: string;
  amount: number;
  format: "xlsx" | "txt";
  includeValidation: boolean;
}

export interface ExtractionResult {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  totalContacts: number;
  processedContacts: number;
  downloadUrl?: string;
  error?: string;
  createdAt: string;
  completedAt?: string;
}
