import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 20000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      void import("../stores/groupPhotoRecognition.js").then((m) =>
        m.resetGroupPhotoRecognitionStore()
      );
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_info");
      localStorage.removeItem("remember_until");
      const current = window.location.pathname + window.location.search;
      if (!window.location.pathname.startsWith("/login")) {
        const next = encodeURIComponent(current || "/");
        window.location.assign(`/login?next=${next}`);
      }
    }
    if (status === 403 && !window.location.pathname.startsWith("/login")) {
      // 统一无权限落地页：保持登录态，回到可访问页面
      window.location.assign("/attendance?forbidden=1");
    }
    return Promise.reject(error);
  }
);

export function unwrapApiResponse(payload) {
  if (payload && typeof payload === "object" && "code" in payload && "data" in payload) {
    if (payload.code !== 0) {
      throw new Error(payload.message || "业务请求失败");
    }
    return payload.data;
  }
  return payload;
}

export function getErrorMessage(e) {
  if (e?.code === "ECONNABORTED") {
    return "识别超时：分析耗时过长，请稍后重试或缩小图片";
  }
  if (e?.code === "ERR_NETWORK") {
    return "网络异常：无法连接服务器，请检查网络或服务是否已启动";
  }
  const status = e?.response?.status;
  if (status === 413) {
    return e?.response?.data?.detail || "上传文件过大，请压缩后重试";
  }
  if (status === 415) {
    return e?.response?.data?.detail || "不支持的文件格式，请使用 JPG / PNG / GIF / WEBP";
  }
  if (status === 503) {
    return (
      e?.response?.data?.detail ||
      e?.response?.data?.message ||
      "识别服务暂时不可用，请稍后重试"
    );
  }
  if (status === 504) {
    return e?.response?.data?.detail || e?.response?.data?.message || "网关超时，请稍后重试";
  }
  if (status === 500) {
    return e?.response?.data?.message || "服务器处理异常，请稍后重试";
  }
  return (
    e?.response?.data?.detail ||
    e?.response?.data?.message ||
    e?.message ||
    "请求失败"
  );
}

