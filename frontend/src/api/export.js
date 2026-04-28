import { api } from "./client";

function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "export.xlsx";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function downloadAttendanceExcel(params = {}) {
  const res = await api.get("/api/export/attendance/excel", {
    params,
    responseType: "blob"
  });
  triggerBlobDownload(res.data, "attendance.xlsx");
}

export async function downloadActivityExcel(params = {}) {
  const res = await api.get("/api/export/activity/excel", {
    params,
    responseType: "blob"
  });
  triggerBlobDownload(res.data, "activity.xlsx");
}

// 向后兼容：旧命名仍可用
export const exportAttendanceExcel = downloadAttendanceExcel;
export const exportActivityExcel = downloadActivityExcel;
