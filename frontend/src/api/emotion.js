import { api, unwrapApiResponse } from "./client";

export async function fetchEmotionStats(params = {}) {
  const { data } = await api.get("/api/emotion/stats", { params });
  return unwrapApiResponse(data);
}

export async function fetchEmotionRecords(params = {}) {
  const { data } = await api.get("/api/emotion/records", { params });
  return unwrapApiResponse(data);
}
