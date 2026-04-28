import { api, unwrapApiResponse } from "./client";

export async function checkinWithImageBlob(blob, filename = "frame.jpg") {
  const form = new FormData();
  form.append("image", blob, filename);
  const { data } = await api.post("/api/attendance/checkin", form);
  return unwrapApiResponse(data);
}

function dateToLocalYmd(d) {
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return d;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export async function fetchAttendanceRecords(params = {}) {
  const payload = { ...params };
  if (payload.date_from instanceof Date) {
    payload.date_from = dateToLocalYmd(payload.date_from);
  }
  if (payload.date_to instanceof Date) {
    payload.date_to = dateToLocalYmd(payload.date_to);
  }
  const { data } = await api.get("/api/attendance/records", { params: payload });
  return unwrapApiResponse(data);
}

