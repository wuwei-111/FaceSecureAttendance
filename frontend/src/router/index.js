import { createRouter, createWebHistory } from "vue-router";
import AttendanceView from "../views/AttendanceView.vue";
import PhotoRecognitionView from "../views/PhotoRecognitionView.vue";
import EmotionStatsView from "../views/EmotionStatsView.vue";
import StudentManageView from "../views/StudentManageView.vue";
import LoginView from "../views/LoginView.vue";

const routes = [
  { path: "/login", component: LoginView },
  { path: "/", component: AttendanceView },
  { path: "/photo", component: PhotoRecognitionView },
  { path: "/emotion", component: EmotionStatsView },
  { path: "/students", component: StudentManageView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  if (to.path === "/login") return true;
  const token = localStorage.getItem("access_token");
  if (!token) {
    return `/login?next=${encodeURIComponent(to.fullPath || "/")}`;
  }
  return true;
});

export default router;
