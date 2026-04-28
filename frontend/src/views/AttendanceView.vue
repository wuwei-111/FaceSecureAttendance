<template>
  <el-card>
    <template #header>
      <span>基础考勤</span>
    </template>

    <CameraCapture ref="cameraRef" :busy="loading" @captured="onCaptured" />

    <div class="autoBar">
      <el-switch v-model="autoMode" :disabled="loading" active-text="自动截帧" />
      <el-input-number v-model="autoIntervalSec" :min="2" :max="10" :step="1" :disabled="!autoMode || loading" />
      <span class="hint">秒/次（摄像头开启后生效）</span>
    </div>

    <el-divider />

    <el-alert
      v-if="loading"
      type="info"
      :closable="false"
      show-icon
      title="正在检测活体并匹配人脸，请稍候..."
      style="margin-bottom: 12px"
    />

    <el-descriptions v-if="result" :column="1" border>
      <el-descriptions-item label="状态">
        <el-tag :type="statusType">{{ statusLabel }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="record_id">{{ result.record_id }}</el-descriptions-item>
      <el-descriptions-item label="matched_student_no">{{
        result.matched_student_no ?? "-"
      }}</el-descriptions-item>
      <el-descriptions-item label="emotion">{{ result.emotion ?? "-" }}</el-descriptions-item>
      <el-descriptions-item label="timestamp">{{ result.timestamp }}</el-descriptions-item>
    </el-descriptions>

    <el-alert
      v-if="err"
      type="error"
      :closable="false"
      show-icon
      :title="err"
      style="margin-top: 12px"
    />
  </el-card>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import CameraCapture from "../components/CameraCapture.vue";
import { checkinWithImageBlob } from "../api/attendance";
import { getErrorMessage } from "../api/client";

const result = ref(null);
const err = ref("");
const loading = ref(false);
const cameraRef = ref(null);
const autoMode = ref(false);
const autoIntervalSec = ref(3);
const autoTimer = ref(null);

const statusType = computed(() => {
  const s = result.value?.status || "";
  if (s.startsWith("present")) return "success";
  if (s.startsWith("failed_liveness")) return "warning";
  if (s.startsWith("failed")) return "danger";
  return "info";
});

const statusLabel = computed(() => {
  const s = result.value?.status || "";
  if (s === "present") return "识别成功";
  if (s === "failed") return "未匹配到学生";
  if (s.startsWith("failed_liveness:")) {
    const reason = s.split(":")[1] || "活体检测未通过";
    return `活体失败（${reason}）`;
  }
  return s || "-";
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
    if (!cameraRef.value?.running?.value) return;
    cameraRef.value.capture();
  }, autoIntervalSec.value * 1000);
}

watch([autoMode, autoIntervalSec], () => {
  setupAutoCapture();
});

watch(
  () => cameraRef.value?.running?.value,
  (running) => {
    if (running && autoMode.value) setupAutoCapture();
  }
);

onBeforeUnmount(clearAutoTimer);
</script>

<style scoped>
.autoBar {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.hint {
  color: var(--app-subtext, #6b7280);
  font-size: 12px;
}
</style>
