import { api, unwrapApiResponse } from "./client";

export async function fetchEmotionStats() {
  const { data } = await api.get("/api/emotion/stats");
  return unwrapApiResponse(data);
}

