export interface ValidationResult {
  contactId: string;
  phoneNumber: string;
  platforms: {
    whatsapp: PlatformStatus;
    instagram: PlatformStatus;
    facebook: PlatformStatus;
    google: PlatformStatus;
    apple: PlatformStatus;
  };
  leadScore: number;
  validatedAt: string;
}

export interface PlatformStatus {
  isValid: boolean;
  isBusiness: boolean;
  confidence: number;
  lastChecked: string;
  error?: string;
}

export interface LeadScore {
  score: number;
  factors: {
    platformCount: number;
    businessAccounts: number;
    profileCompleteness: number;
    activityScore: number;
  };
  category: "low" | "medium" | "high" | "premium";
}
