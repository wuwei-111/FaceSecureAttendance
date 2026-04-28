<template>
  <el-header class="header">
    <div class="headerTitle">
      <div class="pageTitle">{{ title }}</div>
      <div class="pageSub">FaceSecureAttendance</div>
    </div>
    <div class="headerRight">
      <el-tag effect="light" :type="role === 'teacher' ? 'success' : 'info'">
        {{ role === "teacher" ? "教师" : "学生" }}
      </el-tag>
      <el-dropdown>
        <span class="userChip">
          {{ username }}
          <el-icon class="userArrow"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="openDocs">打开 API 文档</el-dropdown-item>
            <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { ArrowDown } from "@element-plus/icons-vue";
import { ElMessageBox } from "element-plus";

defineProps({
  title: { type: String, default: "FaceSecureAttendance" },
  role: { type: String, default: "student" },
  username: { type: String, default: "用户" }
});

function openDocs() {
  window.open("http://127.0.0.1:8000/docs", "_blank");
}

async function logout() {
  try {
    await ElMessageBox.confirm("确认退出当前账号？", "退出登录", {
      type: "warning",
      confirmButtonText: "退出",
      cancelButtonText: "取消"
    });
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    localStorage.removeItem("remember_until");
    window.location.assign("/login");
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
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
.headerRight {
  display: flex;
  align-items: center;
  gap: 8px;
}
.userChip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(20, 20, 20, 0.1);
  background: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  cursor: pointer;
}
.userArrow {
  font-size: 12px;
}
</style>

