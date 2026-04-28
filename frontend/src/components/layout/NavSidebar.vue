<template>
  <el-aside class="aside glass">
    <div class="brand">
      <div class="logo">FS</div>
      <div class="meta">
        <div class="name">FaceSecure</div>
        <div class="desc">Attendance System</div>
      </div>
    </div>

    <div ref="searchWrapRef" class="searchWrap">
      <el-button class="searchBtn" @click="searchOpen = !searchOpen">
        <el-icon><Search /></el-icon>
        功能搜索
      </el-button>
      <div v-if="searchOpen" class="searchPanel">
        <el-input v-model="kw" clearable placeholder="搜索功能名" />
        <div class="searchBody">
          <el-checkbox-group v-model="picked">
            <el-checkbox
              v-for="item in filteredFeatures"
              :key="item.key"
              :label="item.key"
              class="cbItem"
            >
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="searchActions">
          <el-button size="small" @click="searchOpen = false">关闭</el-button>
          <el-button class="goBtn" size="small" type="primary" :disabled="picked.length === 0" @click="goFeature">
            定位
          </el-button>
        </div>
      </div>
    </div>

    <el-menu class="menu" :default-active="route.path" router>
      <el-menu-item index="/attendance" class="mi m1">
        <span class="dot"><el-icon><VideoCamera /></el-icon></span>
        <span>考勤</span>
      </el-menu-item>
      <el-menu-item index="/records" class="mi m2">
        <span class="dot"><el-icon><Tickets /></el-icon></span>
        <span>记录查询</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/students" class="mi m3">
        <span class="dot"><el-icon><User /></el-icon></span>
        <span>学生管理</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/group-photo" class="mi m4">
        <span class="dot"><el-icon><Picture /></el-icon></span>
        <span>合照识别</span>
      </el-menu-item>
      <el-menu-item v-if="isTeacher" index="/emotion" class="mi m5">
        <span class="dot"><el-icon><Histogram /></el-icon></span>
        <span>情绪统计</span>
      </el-menu-item>
    </el-menu>

    <div class="asideFooter">
      <el-tag effect="light" type="info">{{ isTeacher ? "教师模式" : "学生模式" }}</el-tag>
    </div>

  </el-aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Histogram, Picture, Search, Tickets, User, VideoCamera } from "@element-plus/icons-vue";

const props = defineProps({
  role: {
    type: String,
    default: "student"
  }
});

const route = useRoute();
const router = useRouter();
const isTeacher = computed(() => props.role === "teacher");
const searchOpen = ref(false);
const kw = ref("");
const picked = ref([]);
const searchWrapRef = ref(null);

const allFeatures = [
  { key: "attendance-camera", label: "考勤 / 摄像头采集区", path: "/attendance", role: "all" },
  { key: "attendance-auto", label: "考勤 / 自动截帧控制", path: "/attendance", role: "all" },
  { key: "attendance-result", label: "考勤 / 识别结果区", path: "/attendance", role: "all" },
  { key: "records-filter", label: "记录查询 / 筛选区", path: "/records", role: "all" },
  { key: "records-table", label: "记录查询 / 表格区", path: "/records", role: "all" },
  { key: "students-actions", label: "学生管理 / 批量操作区", path: "/students", role: "teacher" },
  { key: "students-table", label: "学生管理 / 学生表格区", path: "/students", role: "teacher" },
  { key: "photo-upload", label: "合照识别 / 上传区", path: "/group-photo", role: "teacher" },
  { key: "photo-result", label: "合照识别 / 名单结果区", path: "/group-photo", role: "teacher" },
  { key: "emotion-chart", label: "情绪统计 / 图表区", path: "/emotion", role: "teacher" },
  { key: "emotion-table", label: "情绪统计 / 明细表格区", path: "/emotion", role: "teacher" }
];

const roleFeatures = computed(() =>
  allFeatures.filter((x) => x.role === "all" || (x.role === "teacher" && isTeacher.value))
);

const filteredFeatures = computed(() => {
  const s = kw.value.trim().toLowerCase();
  if (!s) return roleFeatures.value;
  return roleFeatures.value.filter((x) => x.label.toLowerCase().includes(s));
});

async function goFeature() {
  const target = roleFeatures.value.find((x) => x.key === picked.value[0]);
  if (!target) return;
  await router.push({ path: target.path, query: { focus: target.key } });
  searchOpen.value = false;
}

watch(
  picked,
  (v) => {
    if (v.length <= 1) return;
    picked.value = [v[v.length - 1]];
  },
  { deep: true }
);

function onDocMouseDown(e) {
  if (!searchOpen.value) return;
  const root = searchWrapRef.value;
  if (!root) return;
  if (root.contains(e.target)) return;
  searchOpen.value = false;
}

onMounted(() => {
  document.addEventListener("mousedown", onDocMouseDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocMouseDown);
});
</script>

<style scoped>
.aside {
  width: 248px;
  height: calc(100vh - 32px);
  position: sticky;
  top: 16px;
  overflow: auto;
  border-radius: 16px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 10px 26px rgba(44, 62, 80, 0.08);
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
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
.name {
  font-weight: 900;
  line-height: 1.1;
  font-family: "Segoe Script", "STKaiti", "KaiTi", cursive;
  letter-spacing: 0.4px;
}
.desc {
  color: rgba(31, 35, 40, 0.68);
  font-size: 12px;
  margin-top: 2px;
}
.searchBtn {
  width: 100%;
  border: 1px solid rgba(20, 20, 20, 0.1);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.18) 0%, rgba(167, 139, 250, 0.16) 52%, rgba(52, 211, 153, 0.16) 100%);
}
.searchWrap {
  position: relative;
}
.searchPanel {
  margin-top: 8px;
  width: 100%;
  max-width: 100%;
  border-radius: 12px;
  border: 1px solid rgba(20, 20, 20, 0.1);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(10px);
  padding: 8px;
  box-sizing: border-box;
}
.menu {
  border-right: none;
  background: transparent;
}
.mi {
  border-radius: 12px;
  margin-bottom: 4px;
  height: 44px;
  line-height: 44px;
  font-weight: 700;
}
.dot {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: inline-grid;
  place-items: center;
  margin-right: 6px;
  border: 1px solid rgba(20, 20, 20, 0.08);
}
.m1 .dot { background: rgba(122, 167, 255, 0.22); color: #3b82f6; }
.m2 .dot { background: rgba(99, 102, 241, 0.2); color: #4f46e5; }
.m3 .dot { background: rgba(52, 211, 153, 0.2); color: #059669; }
.m4 .dot { background: rgba(167, 139, 250, 0.22); color: #7c3aed; }
.m5 .dot { background: rgba(251, 146, 60, 0.2); color: #ea580c; }

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.26) 0%, rgba(167, 139, 250, 0.24) 55%, rgba(52, 211, 153, 0.24) 100%) !important;
  color: #1f2328;
  box-shadow: inset 0 0 0 1px rgba(122, 167, 255, 0.38);
}
:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.72);
}
.asideFooter {
  margin-top: auto;
  padding: 8px 10px;
  display: flex;
  justify-content: center;
}
.searchBody {
  margin-top: 8px;
  max-height: 220px;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.7);
  padding: 6px;
  box-sizing: border-box;
}
.cbItem {
  width: 100%;
  margin-right: 0;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid transparent;
}
.cbItem:hover {
  background: rgba(122, 167, 255, 0.12);
  border-color: rgba(122, 167, 255, 0.24);
}
.searchActions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.goBtn {
  border: none;
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}
</style>

