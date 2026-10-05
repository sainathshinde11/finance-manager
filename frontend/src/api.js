import axios from "axios";

const client = axios.create({ baseURL: "/api" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("financeai_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const authApi = {
  register: (payload) => client.post("/auth/register", payload).then((r) => r.data),
  login: (payload) => client.post("/auth/login", payload).then((r) => r.data),
  me: () => client.get("/auth/me").then((r) => r.data),
};

export const txnApi = {
  list: (params) => client.get("/transactions", { params }).then((r) => r.data),
  create: (payload) => client.post("/transactions", payload).then((r) => r.data),
  update: (id, payload) => client.put(`/transactions/${id}`, payload).then((r) => r.data),
  remove: (id) => client.delete(`/transactions/${id}`).then((r) => r.data),
  categorizePreview: (description) =>
    client.post("/categorize-preview", { description }).then((r) => r.data),
};

export const analyticsApi = {
  summary: () => client.get("/analytics/summary").then((r) => r.data),
  forecast: () => client.get("/analytics/forecast").then((r) => r.data),
};

export const categoriesApi = {
  list: () => client.get("/categories").then((r) => r.data),
};

export const budgetApi = {
  set: (monthly_budget) => client.put("/budget", { monthly_budget }).then((r) => r.data),
};

export default client;
