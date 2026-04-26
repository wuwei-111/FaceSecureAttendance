import { createRouter, createWebHistory } from "vue-router";
import AttendanceView from "../views/AttendanceView.vue";
import PhotoRecognitionView from "../views/PhotoRecognitionView.vue";
import EmotionStatsView from "../views/EmotionStatsView.vue";
import StudentManageView from "../views/StudentManageView.vue";
import LoginView from "../views/LoginView.vue";
import MainLayout from "../layouts/MainLayout.vue";
import RecordsView from "../views/RecordsView.vue";

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

router.beforeEach((to) => {
  const requiresAuth = to.matched.some((r) => r.meta?.auth !== false);
  if (!requiresAuth) return true;

  const token = localStorage.getItem("access_token");
  if (!token) {
    return `/login?next=${encodeURIComponent(to.fullPath || "/")}`;
  }

  const roles = to.meta?.roles;
  if (Array.isArray(roles) && roles.length > 0) {
    try {
      const raw = localStorage.getItem("user_info");
      const role = raw ? JSON.parse(raw)?.role : null;
      if (!role || !roles.includes(role)) {
        return "/attendance";
      }
    } catch {
      return "/attendance";
    }
  }
  return true;
});

export default router;
