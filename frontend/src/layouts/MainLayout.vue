<template>
  <el-container class="layout">
    <NavSidebar :role="role" />

    <el-container direction="vertical">
      <TopHeader :title="title" :role="role" :username="username" />
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fadeSlide">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import NavSidebar from "../components/layout/NavSidebar.vue";
import TopHeader from "../components/layout/TopHeader.vue";

const route = useRoute();

const userInfo = computed(() => {
  try {
    return JSON.parse(localStorage.getItem("user_info") || "{}");
  } catch {
    return {};
  }
});

const role = computed(() => userInfo.value?.role || "student");
const username = computed(() => userInfo.value?.username || "用户");

const title = computed(() => {
  const map = {
    "/attendance": "基础考勤",
    "/students": "学生管理",
    "/group-photo": "合照学生识别",
    "/emotion": "情绪分析统计",
    "/records": "考勤记录查询"
  };
  return map[route.path] || "FaceSecureAttendance";
});
</script>

<style scoped>
.layout {
  min-height: 100vh;
  padding: 16px;
  gap: 16px;
}
.main {
  padding: 16px 0 0 0;
}
.fadeSlide-enter-active,
.fadeSlide-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.fadeSlide-enter-from,
.fadeSlide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>

