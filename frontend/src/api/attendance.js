import { api, unwrapApiResponse } from "./client";

export async function checkinWithImageBlob(blob, filename = "frame.jpg") {
  const form = new FormData();
  form.append("image", blob, filename);
  const { data } = await api.post("/api/attendance/checkin", form);
  return unwrapApiResponse(data);
}

