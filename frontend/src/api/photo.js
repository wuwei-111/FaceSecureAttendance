import { api, unwrapApiResponse } from "./client";

export async function recognizeGroupPhoto(file) {
  const form = new FormData();
  form.append("image", file, file.name || "group.jpg");
  const { data } = await api.post("/api/photo/recognize", form);
  return unwrapApiResponse(data);
}

