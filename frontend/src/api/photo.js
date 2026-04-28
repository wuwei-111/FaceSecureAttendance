import { api, unwrapApiResponse } from "./client";

export async function recognizeGroupPhoto(file, activityName) {
  const form = new FormData();
  form.append("image", file, file.name || "group.jpg");
  if (activityName && String(activityName).trim()) {
    form.append("activity_name", String(activityName).trim());
  }
  const { data } = await api.post("/api/photo/recognize", form);
  return unwrapApiResponse(data);
}

export async function fetchGroupPhotoList(params = {}) {
  const { data } = await api.get("/api/photo/list", { params });
  return unwrapApiResponse(data);
}

export async function fetchPhotoActivityStats() {
  const { data } = await api.get("/api/photo/activity-stats");
  return unwrapApiResponse(data);
}
