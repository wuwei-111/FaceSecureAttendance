import { api } from "./client";

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "export.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadAttendanceExcel(params = {}) {
  const res = await api.get("/api/export/attendance/excel", {
    params,
    responseType: "blob"
  });
  triggerDownload(res.data, "attendance.xlsx");
}

export async function downloadActivityExcel(params = {}) {
  const res = await api.get("/api/export/activity/excel", {
    params,
    responseType: "blob"
  });
  triggerDownload(res.data, "activity.xlsx");
}
