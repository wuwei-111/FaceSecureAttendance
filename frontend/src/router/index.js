import { createRouter, createWebHistory } from "vue-router";
import AttendanceView from "../views/AttendanceView.vue";
import PhotoRecognitionView from "../views/PhotoRecognitionView.vue";
import EmotionStatsView from "../views/EmotionStatsView.vue";

const routes = [
  { path: "/", component: AttendanceView },
  { path: "/photo", component: PhotoRecognitionView },
  { path: "/emotion", component: EmotionStatsView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
