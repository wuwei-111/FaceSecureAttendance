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
    if (status === 401 || status === 403) {
      const current = window.location.pathname + window.location.search;
      if (!window.location.pathname.startsWith("/login")) {
        const next = encodeURIComponent(current || "/");
        window.location.assign(`/login?next=${next}`);
      }
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
  return (
    e?.response?.data?.detail ||
    e?.response?.data?.message ||
    e?.message ||
    "请求失败"
  );
}

