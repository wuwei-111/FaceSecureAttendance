<template>
  <el-card class="glass">
    <template #header>
      <div class="pageTitle">基础考勤</div>
    </template>

    <div class="pageGrid">
      <div class="leftPane" data-feature="attendance-camera">
        <CameraCapture
          ref="cameraRef"
          :busy="loading"
          :show-actions="false"
          @captured="onCaptured"
          @running-change="onCameraRunningChange"
        />
      </div>

      <div class="rightPane">
        <div class="autoPanel glass" data-feature="attendance-auto">
          <div class="autoHead">
            <div>
              <div class="autoTitle">自动截帧</div>
              <div class="autoSub">开启后按固定间隔自动提交当前视频帧</div>
            </div>
            <el-switch v-model="autoMode" :disabled="loading" inline-prompt active-text="开" inactive-text="关" />
          </div>
          <div class="autoBody">
            <div class="stepper">
              <span class="hint">采样间隔</span>
              <el-input-number
                v-model="autoIntervalSec"
                :min="2"
                :max="10"
                :step="1"
                :disabled="!autoMode || loading"
              />
              <span class="hint">秒/次</span>
            </div>
            <el-tag effect="light" :type="autoMode ? 'success' : 'info'">
              {{ autoMode ? "自动模式运行中" : "手动模式" }}
            </el-tag>
          </div>
        </div>

        <el-alert
          v-if="loading"
          type="info"
          :closable="false"
          show-icon
          title="正在检测活体并匹配人脸，请稍候..."
        />

        <el-descriptions v-if="result" :column="1" border data-feature="attendance-result">
          <el-descriptions-item label="状态">
            <el-tag :type="statusType">{{ statusLabel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="record_id">{{ result.record_id }}</el-descriptions-item>
          <el-descriptions-item label="matched_student_no">{{
            result.matched_student_no ?? "-"
          }}</el-descriptions-item>
          <el-descriptions-item label="emotion">{{ result.emotion ?? "-" }}</el-descriptions-item>
          <el-descriptions-item label="timestamp">{{ displayTimestamp }}</el-descriptions-item>
        </el-descriptions>

        <el-alert
          v-if="err"
          type="error"
          :closable="false"
          show-icon
          :title="err"
        />

        <div class="spacer" />

        <div class="opsPanel glass">
          <div class="opsHead">
            <div class="opsTitle">操作</div>
            <el-tag effect="light" :type="cameraRunning ? 'success' : 'info'">
              {{ cameraRunning ? "摄像头运行中" : "摄像头未开启" }}
            </el-tag>
          </div>
          <div class="opsBtns">
            <el-button
              class="btnGlass btnStart"
              :disabled="loading || cameraRunning"
              type="primary"
              @click="onStartCamera"
            >
              <span class="label">打开摄像头</span>
            </el-button>
            <el-button class="btnGlass btnStop" :disabled="loading || !cameraRunning" @click="onStopCamera">
              <span class="label">关闭摄像头</span>
            </el-button>
            <el-button
              class="btnGlass btnCapture"
              :disabled="loading || !cameraRunning"
              type="success"
              @click="onManualCapture"
            >
              <span class="label">{{ loading ? "上传中..." : "截帧上传" }}</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import dayjs from "dayjs";
import { useRoute, useRouter } from "vue-router";
import CameraCapture from "../components/CameraCapture.vue";
import { checkinWithImageBlob } from "../api/attendance";
import { getErrorMessage } from "../api/client";
import { ElMessage } from "element-plus";

const result = ref(null);
const err = ref("");
const loading = ref(false);
const cameraRef = ref(null);
const autoMode = ref(false);
const autoIntervalSec = ref(3);
const autoTimer = ref(null);
const cameraRunning = ref(false);
const route = useRoute();
const router = useRouter();

const statusType = computed(() => {
  const s = result.value?.status || "";
  if (s.startsWith("present")) return "success";
  if (s.startsWith("failed_liveness")) return "warning";
  if (s.startsWith("failed_ambiguous")) return "warning";
  if (s.startsWith("failed")) return "danger";
  return "info";
});

const statusLabel = computed(() => {
  const s = result.value?.status || "";
  if (s === "present") return "识别成功";
  if (s === "failed") return "未匹配到学生";
  if (s === "failed_ambiguous") return "存在多名相似学生，无法唯一确认";
  if (s.startsWith("failed_liveness:")) {
    const reason = s.split(":")[1] || "活体检测未通过";
    return `活体失败（${reason}）`;
  }
  return s || "-";
});

const displayTimestamp = computed(() => {
  const raw = result.value?.timestamp;
  if (!raw) return "-";
  const value = dayjs(raw);
  return value.isValid() ? value.format("YYYY-MM-DD HH:mm:ss") : String(raw);
});

async function onCaptured(blob) {
  if (loading.value) return;
  err.value = "";
  result.value = null;
  loading.value = true;
  try {
    result.value = await checkinWithImageBlob(blob);
  } catch (e) {
    const status = e?.response?.status;
    if (status === 503) {
      const backendMsg = getErrorMessage(e);
      err.value =
        backendMsg && backendMsg !== "请求失败"
          ? backendMsg
          : "CV / 活体服务不可用：请在 backend 安装 requirements-cv.txt 后重启，或查看后端日志。";
    } else if (status === 422) {
      err.value = "未检测到可用人脸，请调整光线并正视摄像头后重试";
    } else {
      err.value = getErrorMessage(e);
    }
  } finally {
    loading.value = false;
  }
}

function onStartCamera() {
  cameraRef.value?.start?.();
}
function onStopCamera() {
  cameraRef.value?.stop?.();
}
function onManualCapture() {
  cameraRef.value?.capture?.();
}
function onCameraRunningChange(v) {
  cameraRunning.value = !!v;
}

function clearAutoTimer() {
  if (autoTimer.value) {
    clearInterval(autoTimer.value);
    autoTimer.value = null;
  }
}

function setupAutoCapture() {
  clearAutoTimer();
  if (!autoMode.value) return;
  autoTimer.value = setInterval(() => {
    if (loading.value) return;
    if (!cameraRunning.value) return;
    cameraRef.value.capture();
  }, autoIntervalSec.value * 1000);
}

watch([autoMode, autoIntervalSec], () => {
  setupAutoCapture();
});

watch(cameraRunning, (running) => {
  if (running && autoMode.value) setupAutoCapture();
});

onBeforeUnmount(clearAutoTimer);

onMounted(() => {
  if (route.query.forbidden === "1") {
    ElMessage.warning("当前账号无权限访问该页面");
    const nextQuery = { ...route.query };
    delete nextQuery.forbidden;
    router.replace({ path: route.path, query: nextQuery });
  }
});
</script>

<style scoped>
.pageTitle {
  font-weight: 900;
}
.pageGrid {
  display: grid;
  grid-template-columns: minmax(520px, 1.35fr) minmax(320px, 0.85fr);
  gap: 14px;
  align-items: stretch;
}
.leftPane {
  min-width: 0;
}
.rightPane {
  min-width: 0;
  display: grid;
  gap: 12px;
  grid-template-rows: auto auto auto 1fr auto;
}
.spacer {
  min-height: 10px;
}
.opsPanel {
  border-radius: 14px;
  padding: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.52);
}
.opsHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.opsTitle {
  font-weight: 900;
}
.opsBtns {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.btnGlass {
  height: 38px;
  border-radius: 12px;
  border: 1px solid rgba(20, 20, 20, 0.1);
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 18px rgba(31, 35, 40, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
.btnGlass:deep(span.label) {
  font-weight: 800;
  letter-spacing: 0.2px;
}
.btnStart {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.96) 0%, rgba(167, 139, 250, 0.92) 48%, rgba(52, 211, 153, 0.95) 100%);
}
.btnCapture {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.95) 0%, rgba(96, 165, 250, 0.9) 56%, rgba(244, 114, 182, 0.92) 110%);
}
.btnStop {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82) 0%, rgba(243, 244, 246, 0.88) 100%);
}
.autoPanel {
  border-radius: 14px;
  padding: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.1) 0%, rgba(167, 139, 250, 0.08) 45%, rgba(52, 211, 153, 0.08) 100%);
}
.autoHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.autoTitle {
  font-weight: 900;
}
.autoSub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--app-subtext, #6b7280);
}
.autoBody {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.stepper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(20, 20, 20, 0.08);
}
.hint {
  color: var(--app-subtext, #6b7280);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .pageGrid {
    grid-template-columns: 1fr;
  }
}
</style>
