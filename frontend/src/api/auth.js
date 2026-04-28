import { api, unwrapApiResponse } from "./client";

export async function login(username, password) {
  const { data } = await api.post("/api/auth/login", { username, password });
  return unwrapApiResponse(data);
}

export async function getCurrentUser() {
  const { data } = await api.get("/api/auth/me");
  return unwrapApiResponse(data);
}

