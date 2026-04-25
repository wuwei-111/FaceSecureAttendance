<template>
  <router-view v-if="route.path === '/login'" />

  <el-container v-else class="layout">
    <el-aside class="aside glass">
      <div class="brand">
        <div class="logo">FS</div>
        <div class="meta">
          <div class="name">FaceSecure</div>
          <div class="desc">Attendance System</div>
        </div>
      </div>

      <el-menu class="menu" :default-active="route.path" router>
        <el-menu-item index="/">
          <el-icon><VideoCamera /></el-icon>
          <span>考勤</span>
        </el-menu-item>
        <el-menu-item index="/students">
          <el-icon><User /></el-icon>
          <span>学生管理</span>
        </el-menu-item>
        <el-menu-item index="/photo">
          <el-icon><Picture /></el-icon>
          <span>合照识别</span>
        </el-menu-item>
        <el-menu-item index="/emotion">
          <el-icon><Histogram /></el-icon>
          <span>情绪统计</span>
        </el-menu-item>
      </el-menu>

      <div class="asideFooter">
        <el-tag effect="light" type="info">API: 127.0.0.1:8000</el-tag>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="headerTitle">
          <div class="pageTitle">{{ title }}</div>
          <div class="pageSub">FaceSecureAttendance</div>
        </div>
        <div class="headerRight">
          <el-tooltip content="打开 Swagger 文档" placement="bottom">
            <el-button text @click="openDocs">
              <el-icon><Document /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>

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
import {
  Document,
  Histogram,
  Picture,
  User,
  VideoCamera
} from "@element-plus/icons-vue";

const route = useRoute();
const title = computed(() => {
  const map = {
    "/": "基础考勤",
    "/students": "学生管理",
    "/photo": "合照学生识别",
    "/emotion": "情绪分析统计"
  };
  return map[route.path] || "FaceSecureAttendance";
});

function openDocs() {
  window.open("http://127.0.0.1:8000/docs", "_blank");
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  padding: 16px;
  gap: 16px;
}

.header {
  height: auto;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.aside {
  width: 248px;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(20, 20, 20, 0.06);
}

.logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #dbeafe 0%, #f5d0fe 55%, #d1fae5 100%);
  border: 1px solid rgba(20, 20, 20, 0.08);
}

.name {
  font-weight: 800;
  line-height: 1.1;
}

.desc {
  color: rgba(31, 35, 40, 0.68);
  font-size: 12px;
  margin-top: 2px;
}

.menu {
  border-right: none;
  background: transparent;
}

.asideFooter {
  margin-top: auto;
  padding: 8px 10px;
  display: flex;
  justify-content: center;
}

.headerTitle {
  display: grid;
  gap: 2px;
}

.pageTitle {
  font-weight: 900;
  letter-spacing: 0.2px;
}

.pageSub {
  font-size: 12px;
  color: rgba(31, 35, 40, 0.68);
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
