export interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: "draft" | "active" | "paused" | "completed";
  targetContacts: number;
  sentMessages: number;
  deliveredMessages: number;
  responseRate: number;
  createdAt: string;
  updatedAt: string;
  scheduledAt?: string;
}

export interface CampaignMetrics {
  totalCampaigns: number;
  activeCampaigns: number;
  totalMessagesSent: number;
  averageResponseRate: number;
  topPerformingCampaign?: Campaign;
}
