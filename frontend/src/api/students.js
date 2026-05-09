import { api, unwrapApiResponse } from "./client";

export async function listStudents(params = {}) {
  const { data } = await api.get("/api/students", { params });
  return unwrapApiResponse(data);
}

export async function createStudent(payload) {
  const { data } = await api.post("/api/students", payload);
  return unwrapApiResponse(data);
}

export async function updateStudent(id, payload) {
  const { data } = await api.put(`/api/students/${id}`, payload);
  return unwrapApiResponse(data);
}

export async function batchImportStudents(file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/students/batch-import", form, {
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

export async function deleteStudent(id) {
  const { data } = await api.delete(`/api/students/${id}`);
  return unwrapApiResponse(data);
}

export async function uploadStudentFace(id, file, onProgress) {
  const form = new FormData();
  form.append("image", file, file.name || "face.jpg");
  const { data } = await api.post(`/api/students/${id}/face`, form, {
    timeout: 120000,
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

export async function deleteStudentFace(id) {
  const { data } = await api.delete(`/api/students/${id}/face`);
  return unwrapApiResponse(data);
}

export async function batchImportStudentsCsv(file, onProgress) {
  const form = new FormData();
  form.append("file", file, file.name || "students.csv");
  const { data } = await api.post("/api/students/batch-import", form, {
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

