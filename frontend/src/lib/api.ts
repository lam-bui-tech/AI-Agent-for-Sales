import { Product, InventoryItem, Lead, HandoffTicket, AuditLog, ToolCall } from '@/types';

export const getApiBase = (): string => {
  if (typeof window !== 'undefined') {
    if (window.location.port === '3000') {
      return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    }
  }
  return '';
};

export async function sendChatMessage(message: string, userId: string): Promise<{
  reply: string;
  source?: string;
  tool_calls?: ToolCall[];
}> {
  const base = getApiBase();
  const res = await fetch(`${base}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId }),
  });
  if (!res.ok) {
    throw new Error(`Server returned ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function getCatalog(): Promise<{ products: Product[] }> {
  const base = getApiBase();
  const res = await fetch(`${base}/api/catalog`);
  if (!res.ok) throw new Error('Failed to load catalog');
  return res.json();
}

export async function getInventory(): Promise<{ inventory: Record<string, InventoryItem> }> {
  const base = getApiBase();
  const res = await fetch(`${base}/admin/inventory`);
  if (!res.ok) throw new Error('Failed to load inventory');
  return res.json();
}

export async function adjustInventory(sku: string, quantity: number): Promise<{ success: boolean; quantity: number }> {
  const base = getApiBase();
  const res = await fetch(`${base}/admin/inventory/adjust`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sku, quantity }),
  });
  if (!res.ok) throw new Error('Failed to adjust inventory');
  return res.json();
}

export async function getLeads(): Promise<{ leads: Lead[] }> {
  const base = getApiBase();
  const res = await fetch(`${base}/admin/leads`);
  if (!res.ok) throw new Error('Failed to load leads');
  return res.json();
}

export async function getHandoffs(): Promise<{ handoffs: HandoffTicket[] }> {
  const base = getApiBase();
  const res = await fetch(`${base}/admin/handoffs`);
  if (!res.ok) throw new Error('Failed to load handoffs');
  return res.json();
}

export async function getAuditLogs(): Promise<{ audit_logs: AuditLog[] }> {
  const base = getApiBase();
  const res = await fetch(`${base}/admin/audit-logs`);
  if (!res.ok) throw new Error('Failed to load audit logs');
  return res.json();
}

export async function getZaloInfo(): Promise<any> {
  const base = getApiBase();
  const res = await fetch(`${base}/api/zalo/qr`);
  if (!res.ok) throw new Error('Failed to fetch Zalo QR');
  return res.json();
}

export async function triggerZaloLogin(force: boolean = false): Promise<any> {
  const base = getApiBase();
  const res = await fetch(`${base}/api/zalo/login?force=${force}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger Zalo login');
  return res.json();
}

export async function getZaloStatus(): Promise<any> {
  const base = getApiBase();
  const res = await fetch(`${base}/api/zalo/status`);
  if (!res.ok) throw new Error('Failed to fetch Zalo status');
  return res.json();
}
