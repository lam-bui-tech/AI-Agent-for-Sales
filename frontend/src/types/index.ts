export interface ToolCall {
  id?: number;
  tool_name: string;
  input_payload: any;
  output_payload?: any;
  execution_time_ms?: number;
  duration_ms?: number;
  success?: boolean | number;
  created_at?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  source?: string;
  tool_calls?: ToolCall[];
}

export interface Product {
  sku: string;
  name: string;
  brand: string;
  price_vnd: number;
  cpu: string;
  ram_gb: number;
  storage_gb: number;
  screen: string;
  weight_kg: number;
  os: string;
  target_use: string;
  summary: string;
  ports?: string[];
  battery_hours?: number;
}

export interface InventoryItem {
  available: boolean;
  quantity: number;
  updated_at?: string;
}

export interface Lead {
  id: number;
  channel: string;
  channel_user_id?: string;
  name?: string;
  phone: string;
  product_skus?: string | string[];
  budget_vnd?: number;
  needs_summary?: string;
  preferred_contact_method?: string;
  consent_to_contact: boolean | number;
  status: string;
  created_at: string;
}

export interface HandoffTicket {
  id: number;
  ticket_id: string;
  conversation_id: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  summary: string;
  suggested_next_action?: string;
  preferred_contact_method?: string;
  status: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  tool_name: string;
  input_payload: string;
  output_payload: string;
  execution_time_ms: number;
  success: boolean | number;
  created_at: string;
}
