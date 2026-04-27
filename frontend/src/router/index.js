import { createRouter, createWebHistory } from "vue-router";
import AttendanceView from "../views/AttendanceView.vue";
import PhotoRecognitionView from "../views/PhotoRecognitionView.vue";
import EmotionStatsView from "../views/EmotionStatsView.vue";
import StudentManageView from "../views/StudentManageView.vue";
import LoginView from "../views/LoginView.vue";
import MainLayout from "../layouts/MainLayout.vue";
import RecordsView from "../views/RecordsView.vue";
import { getCurrentUser } from "../api/auth";

const routes = [
  { path: "/login", component: LoginView, meta: { auth: false } },
  {
    path: "/",
    component: MainLayout,
    meta: { auth: true },
    children: [
      { path: "", redirect: "/attendance" },
      { path: "attendance", component: AttendanceView, meta: { auth: true, roles: ["teacher", "student"] } },
      { path: "records", component: RecordsView, meta: { auth: true, roles: ["teacher", "student"] } },
      { path: "group-photo", component: PhotoRecognitionView, meta: { auth: true, roles: ["teacher"] } },
      { path: "emotion", component: EmotionStatsView, meta: { auth: true, roles: ["teacher"] } },
      { path: "students", component: StudentManageView, meta: { auth: true, roles: ["teacher"] } }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

let profilePromise = null;

async function ensureUserProfile() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;

  const raw = localStorage.getItem("user_info");
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch {
      localStorage.removeItem("user_info");
    }
  }

  if (!profilePromise) {
    profilePromise = getCurrentUser()
      .then((profile) => {
        localStorage.setItem("user_info", JSON.stringify(profile));
        return profile;
      })
      .finally(() => {
        profilePromise = null;
      });
  }
  return profilePromise;
}

function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_info");
}

router.beforeEach(async (to) => {
  const requiresAuth = to.matched.some((r) => r.meta?.auth !== false);
  if (!requiresAuth) return true;

  const token = localStorage.getItem("access_token");
  if (!token) {
    return `/login?next=${encodeURIComponent(to.fullPath || "/")}`;
  }

  let user = null;
  try {
    user = await ensureUserProfile();
  } catch {
    clearAuth();
    return `/login?next=${encodeURIComponent(to.fullPath || "/")}`;
  }
  if (!user?.role) {
    clearAuth();
    return `/login?next=${encodeURIComponent(to.fullPath || "/")}`;
  }

  const roles = to.meta?.roles;
  if (Array.isArray(roles) && roles.length > 0) {
    if (!roles.includes(user.role)) {
      return "/attendance";
    }
  }
  return true;
});

export default router;
