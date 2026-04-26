<template>
  <el-aside class="aside glass">
    <div class="brand">
      <div class="logo">FS</div>
      <div class="meta">
        <div class="name">FaceSecure</div>
        <div class="desc">Attendance System</div>
      </div>
    </div>

    <el-menu class="menu" :default-active="route.path" router>
      <el-menu-item index="/attendance">
        <el-icon><VideoCamera /></el-icon>
        <span>考勤</span>
      </el-menu-item>
      <el-menu-item index="/records">
        <el-icon><Tickets /></el-icon>
        <span>记录查询</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/students">
        <el-icon><User /></el-icon>
        <span>学生管理</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/group-photo">
        <el-icon><Picture /></el-icon>
        <span>合照识别</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/emotion">
        <el-icon><Histogram /></el-icon>
        <span>情绪统计</span>
      </el-menu-item>
    </el-menu>

    <div class="asideFooter">
      <el-tag effect="light" type="info">{{ isTeacher ? "教师模式" : "学生模式" }}</el-tag>
    </div>
  </el-aside>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { Histogram, Picture, Tickets, User, VideoCamera } from "@element-plus/icons-vue";

const props = defineProps({
  role: {
    type: String,
    default: "student"
  }
});

const route = useRoute();
const isTeacher = computed(() => props.role === "teacher");
</script>

<style scoped>
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
</style>

