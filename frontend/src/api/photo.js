import { api, unwrapApiResponse } from "./client";

export async function recognizeGroupPhoto(file, arg2, arg3) {
  // 兼容旧调用：
  // - recognizeGroupPhoto(file, onProgress)
  // 兼容新调用：
  // - recognizeGroupPhoto(file, activityName)
  // - recognizeGroupPhoto(file, { activityName, onProgress })
  let activityName = "";
  let onProgress = null;
  if (typeof arg2 === "function") {
    onProgress = arg2;
  } else if (typeof arg2 === "string") {
    activityName = arg2;
    onProgress = typeof arg3 === "function" ? arg3 : null;
  } else if (arg2 && typeof arg2 === "object") {
    activityName = String(arg2.activityName || "").trim();
    onProgress = typeof arg2.onProgress === "function" ? arg2.onProgress : null;
  }

  const form = new FormData();
  form.append("image", file, file.name || "group.jpg");
  if (activityName) {
    form.append("activity_name", activityName);
  }
  const { data } = await api.post("/api/photo/recognize", form, {
    timeout: 180000,
    onUploadProgress: (evt) => {
      if (!onProgress) return;
      const total = evt?.total || 0;
      const loaded = evt?.loaded || 0;
      const pct = total > 0 ? Math.round((loaded / total) * 100) : 0;
      onProgress(pct);
    }
  });
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
