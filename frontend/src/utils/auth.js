export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("user_info") || "{}");
  } catch {
    return {};
  }
}

export function getStoredRole() {
  return getStoredUser()?.role || "student";
}

export function isTeacherRole() {
  return getStoredRole() === "teacher";
}
