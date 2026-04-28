<template>
  <div class="wrap">
    <div class="videoWrap glass">
      <video ref="videoEl" class="video" autoplay playsinline muted />
      <div v-if="!running" class="placeholder">
        <div class="phIcon">📷</div>
        <div class="phTitle">摄像头未开启</div>
        <div class="phSub">点击“打开摄像头”开始采集</div>
      </div>
    </div>

    <div v-if="showActions" class="actions">
      <el-button
        class="btnGlass btnStart"
        :disabled="busy || starting || running"
        type="primary"
        @click="start"
      >
        <span class="label">打开摄像头</span>
      </el-button>
      <el-button class="btnGlass btnStop" :disabled="busy || starting || !running" @click="stop">
        <span class="label">关闭摄像头</span>
      </el-button>
      <el-button
        class="btnGlass btnCapture"
        :disabled="busy || starting || !running"
        type="success"
        @click="capture"
      >
        <span class="label">{{ busy ? "上传中..." : "截帧上传" }}</span>
      </el-button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from "vue";

defineProps({
  busy: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(["captured", "running-change"]);

const videoEl = ref(null);
const stream = ref(null);
const running = ref(false);
const starting = ref(false);
const error = ref("");

async function start() {
  error.value = "";
  starting.value = true;
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    videoEl.value.srcObject = stream.value;
    running.value = true;
  } catch (e) {
    error.value = e?.message || "摄像头调用失败";
  } finally {
    starting.value = false;
  }
}

function stop() {
  if (!stream.value) return;
  for (const t of stream.value.getTracks()) t.stop();
  stream.value = null;
  running.value = false;
}

async function capture() {
  error.value = "";
  const v = videoEl.value;
  if (!v || v.videoWidth <= 0 || v.videoHeight <= 0) {
    error.value = "视频尚未就绪";
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.width = v.videoWidth;
  canvas.height = v.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(v, 0, 0);

  const blob = await new Promise((resolve) =>
    canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9)
  );
  if (!blob) {
    error.value = "截帧失败";
    return;
  }
  emit("captured", blob);
}

defineExpose({
  start,
  stop,
  capture,
  running
});

watch(
  running,
  (v) => {
    emit("running-change", v);
  },
  { immediate: true }
);

onBeforeUnmount(stop);
</script>

<style scoped>
.wrap {
  display: grid;
  gap: 12px;
}
.videoWrap {
  width: 100%;
  border-radius: 14px;
  overflow: hidden;
  position: relative;
}
.video {
  width: 100%;
  display: block;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}
.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.52);
}
.error {
  color: #f56c6c;
}

.placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 18px;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.55) 0%, rgba(245, 208, 254, 0.35) 55%, rgba(209, 250, 229, 0.45) 100%);
}
.phIcon {
  font-size: 30px;
  line-height: 1;
}
.phTitle {
  margin-top: 6px;
  font-weight: 900;
}
.phSub {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(31, 35, 40, 0.68);
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
</style>

