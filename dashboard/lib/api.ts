const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY || "sharkmmo_admin_secret_key_2026";

async function fetcher(endpoint: string, options: RequestInit = {}) {
  const headers = {
    "Content-Type": "application/json",
    "X-Admin-Key": ADMIN_KEY,
    ...(options.headers || {})
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorData.detail || `HTTP Error ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Dashboard
  getStats: () => fetcher("/dashboard/stats"),

  // Products
  getProducts: (params?: { category?: string; search?: string; is_active?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append("category", params.category);
    if (params?.search) query.append("search", params.search);
    if (params?.is_active !== undefined) query.append("is_active", String(params.is_active));
    return fetcher(`/products?${query.toString()}`);
  },
  syncProducts: () => fetcher("/products/sync", { method: "POST" }),
  updateProduct: (id: number, data: any) => fetcher(`/products/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data)
  }),

  // Pricing Rules
  getPricingRules: () => fetcher("/pricing/rules"),
  createPricingRule: (data: any) => fetcher("/pricing/rules", {
    method: "POST",
    body: JSON.stringify(data)
  }),
  updatePricingRule: (id: number, data: any) => fetcher(`/pricing/rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data)
  }),
  deletePricingRule: (id: number) => fetcher(`/pricing/rules/${id}`, {
    method: "DELETE"
  }),
  reapplyAllPricing: () => fetcher("/pricing/apply-all", { method: "POST" }),

  // Orders
  getOrders: (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.search) query.append("search", params.search);
    if (params?.limit) query.append("limit", String(params.limit));
    if (params?.offset) query.append("offset", String(params.offset));
    return fetcher(`/orders?${query.toString()}`);
  },
  refundOrder: (id: number) => fetcher(`/orders/${id}/refund`, { method: "POST" }),

  // Users
  getUsers: (params?: { search?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.limit) query.append("limit", String(params.limit));
    return fetcher(`/users?${query.toString()}`);
  },
  updateUser: (id: number, data: any) => fetcher(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data)
  }),

  // Payments
  getPayments: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.limit) query.append("limit", String(params.limit));
    return fetcher(`/payments?${query.toString()}`);
  },
  approvePayment: (id: number) => fetcher(`/payments/${id}/approve`, { method: "POST" }),
  rejectPayment: (id: number) => fetcher(`/payments/${id}/reject`, { method: "POST" }),

  // Settings
  getSettings: () => fetcher("/settings"),
  updateSettings: (data: any) => fetcher("/settings", {
    method: "POST",
    body: JSON.stringify({ settings: data })
  })
};
