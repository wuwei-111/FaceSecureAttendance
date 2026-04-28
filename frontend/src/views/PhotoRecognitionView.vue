<template>
  <div class="pageWrap">
    <el-card class="glass pageCard">
      <template #header>
        <div class="hdr">
          <div class="hdrLeft">
            <div class="title">合照学生识别</div>
            <div class="sub">上传班级合照，返回匹配名单与统计结果</div>
          </div>
          <div class="hdrActions">
            <el-button
              class="btnSoft"
              :disabled="!result || loading || !isTeacher"
              :loading="exporting"
              @click="onExportActivity"
            >
              导出 Excel
            </el-button>
            <el-button class="btnSoft" :disabled="!pickedFile || loading || !isTeacher" @click="resetAll">
              重置
            </el-button>
          </div>
        </div>
      </template>

    <el-alert
      v-if="!isTeacher"
      type="warning"
      :closable="false"
      show-icon
      title="当前账号无教师权限，仅可查看页面结果"
      style="margin-bottom: 12px"
    />

      <div class="uploadPanel" data-feature="photo-upload">
        <div class="metaRow">
          <div class="k">活动名称（可选）</div>
          <el-input v-model="activityName" clearable placeholder="例如：第 3 次实验" :disabled="loading || !isTeacher" />
        </div>

        <div class="uploadGrid">
          <div class="previewBox" v-if="previewUrl">
            <el-button class="removePreviewBtn" circle @click="clearPickedImage">×</el-button>
            <el-image class="previewImage" :src="previewUrl" fit="contain" :preview-src-list="[previewUrl]" />
          </div>

          <el-upload
            class="uploader"
            :class="{ uploading: loading }"
            drag
            :show-file-list="false"
            :auto-upload="false"
            accept="image/*"
            :disabled="loading || !isTeacher"
            @change="onPickUpload"
          >
            <div class="upTitle">拖拽或点击上传合照</div>
            <div class="upSub">支持 JPG/PNG，建议清晰正面合照</div>
          </el-upload>
        </div>

        <div class="actionRow">
          <el-button
            class="btnGrad"
            type="primary"
            :loading="loading"
            :disabled="!pickedFile || !isTeacher"
            @click="submit"
          >
            {{ loading ? "识别中..." : "开始识别" }}
          </el-button>
          <span class="fileMeta" v-if="pickedFile">
            {{ pickedFile.name }}（{{ fileSizeLabel }}）
          </span>
        </div>

        <el-progress
          v-if="loading || uploadPct > 0"
          :percentage="uploadPct"
          :stroke-width="8"
          :show-text="true"
          status="success"
        />
      </div>

      <el-table
        v-if="result?.matched_students?.length"
        class="glassTable"
        :data="result.matched_students"
        size="small"
        stripe
        style="width: 100%; margin-top: 12px"
      >
        <el-table-column prop="student_no" label="学号" width="140" />
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="confidence" label="置信度" width="120" />
      </el-table>

    <el-alert
      v-if="err"
      type="error"
      :closable="false"
      show-icon
      :title="err"
      style="margin-top: 12px"
    />

      <template v-if="result">
        <el-divider class="glassDivider" />

        <div class="stats" data-feature="photo-result">
          <div class="statCard glassTile">
            <div class="k">合照记录 ID</div>
            <div class="v mono">{{ result.group_photo_id }}</div>
          </div>
          <div class="statCard glassTile">
            <div class="k">成功匹配人数</div>
            <div class="v">{{ result.count }}</div>
          </div>
          <div class="statCard glassTile">
            <div class="k">匹配率</div>
            <div class="v">{{ matchedRate }}%</div>
          </div>
        </div>

        <div class="listTitle">识别名单</div>
        <el-empty v-if="matchedStudents.length === 0" class="glassEmpty" description="当前返回结果为空" />

        <div v-else class="studentGrid">
          <div v-for="(item, idx) in matchedStudents" :key="`${item.student_no}-${idx}`" class="studentCard glassTile">
            <div class="nm">{{ item.student_name || "-" }}</div>
            <div class="id mono">学号：{{ item.student_no || "-" }}</div>
            <el-progress :percentage="toPct(item.confidence)" :stroke-width="6" :show-text="false" />
            <div class="cf">置信度 {{ toPct(item.confidence) }}%</div>
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { recognizeGroupPhoto } from "../api/photo";
import { isTeacherRole } from "../utils/auth";
import { getErrorMessage } from "../api/client";
import { exportActivityExcel } from "../api/export";
import { ElMessage } from "element-plus";

const result = ref(null);
const err = ref("");
const loading = ref(false);
const uploadPct = ref(0);
const pickedFile = ref(null);
const previewUrl = ref("");
const exporting = ref(false);
const isTeacher = isTeacherRole();
const activityName = ref("");

const matchedStudents = computed(() => result.value?.matched_students || []);
const matchedRate = computed(() => {
  const total = Math.max(1, matchedStudents.value.length);
  const matched = Number(result.value?.count || 0);
  return Math.min(100, Math.round((matched / total) * 100));
});
const fileSizeLabel = computed(() => {
  const size = Number(pickedFile.value?.size || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
});

function toPct(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0;
  if (n <= 1) return Math.max(0, Math.min(100, Math.round(n * 100)));
  return Math.max(0, Math.min(100, Math.round(n)));
}

function onPickUpload(fileInfo) {
  if (!isTeacher) return;
  const file = fileInfo?.raw || fileInfo?.file?.raw || fileInfo?.file;
  if (!file) return;
  pickedFile.value = file;
  result.value = null;
  err.value = "";
  if (previewUrl.value.startsWith("blob:")) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = URL.createObjectURL(file);
}

async function submit() {
  if (!isTeacher || !pickedFile.value) return;
  err.value = "";
  result.value = null;
  uploadPct.value = 0;
  loading.value = true;
  try {
    result.value = await recognizeGroupPhoto(pickedFile.value, {
      activityName: activityName.value,
      onProgress: (pct) => {
        uploadPct.value = pct;
      }
    });
    uploadPct.value = 100;
  } catch (ex) {
    err.value = getErrorMessage(ex);
  } finally {
    loading.value = false;
  }
}

function resetAll() {
  result.value = null;
  err.value = "";
  uploadPct.value = 0;
  clearPickedImage();
}

function clearPickedImage() {
  pickedFile.value = null;
  if (previewUrl.value.startsWith("blob:")) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
}

async function onExportActivity() {
  if (!isTeacher || !result.value) return;
  exporting.value = true;
  try {
    await exportActivityExcel({
      group_photo_id: result.value.group_photo_id
    });
    ElMessage.success("活动名单导出已开始");
  } catch (e) {
    ElMessage.warning(`导出接口未就绪或失败：${getErrorMessage(e)}`);
  } finally {
    exporting.value = false;
  }
}
</script>

<style scoped>
.pageWrap {
  padding: 18px 14px 28px;
  max-width: 1100px;
  margin: 0 auto;
}

.pageCard {
  border-radius: var(--r-lg);
  animation: fadeUp 260ms ease both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.hdrLeft {
  display: grid;
  gap: 2px;
}
.title {
  font-weight: 950;
  letter-spacing: 0.2px;
}
.sub {
  font-size: 12px;
  color: var(--app-subtext);
}
.hdrActions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.uploadPanel {
  display: grid;
  gap: 12px;
}

.uploadGrid {
  display: grid;
  gap: 12px;
}

.uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 430px;
  border-radius: var(--r-lg);
  border: 1px dashed rgba(20, 20, 20, 0.16);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.11) 0%, rgba(167, 139, 250, 0.09) 50%, rgba(52, 211, 153, 0.09) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 36px 26px;
  box-sizing: border-box;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease;
  position: relative;
  overflow: hidden;
}
.uploader :deep(.el-upload-dragger:hover) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  border-color: rgba(122, 167, 255, 0.38);
}
.uploader.uploading :deep(.el-upload-dragger) {
  border-color: rgba(167, 139, 250, 0.45);
  box-shadow: var(--focus-ring);
}
.uploader.uploading :deep(.el-upload-dragger::after) {
  content: "";
  position: absolute;
  inset: -60% -30%;
  background: conic-gradient(
    from 180deg,
    rgba(122, 167, 255, 0.0),
    rgba(122, 167, 255, 0.18),
    rgba(167, 139, 250, 0.18),
    rgba(52, 211, 153, 0.18),
    rgba(122, 167, 255, 0.0)
  );
  animation: spinGlow 1.6s linear infinite;
  filter: blur(18px);
  opacity: 0.8;
  pointer-events: none;
}

@keyframes spinGlow {
  to {
    transform: rotate(360deg);
  }
}

.upTitle {
  font-weight: 800;
  font-size: 22px;
  line-height: 1.5;
}
.upSub {
  margin-top: 10px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--app-subtext);
}
.previewBox {
  position: relative;
  border: 1px solid var(--glass-border);
  background: var(--glass-surface-strong);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border-radius: var(--r-lg);
  min-height: 340px;
  padding: 12px;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm), var(--shadow-inset);
}
.previewImage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  height: min(70vh, 560px);
  max-height: 560px;
}
.previewImage :deep(.el-image__inner) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.previewImage :deep(.el-image__wrapper) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.removePreviewBtn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid var(--glass-border-strong);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  color: #1f2937;
  font-size: 18px;
  line-height: 1;
  z-index: 2;
  box-shadow: var(--shadow-sm);
  transition: transform 140ms ease, background 140ms ease;
}
.removePreviewBtn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.86);
}
.actionRow {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.fileMeta {
  font-size: 12px;
  color: var(--app-subtext);
}
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}
.statCard {
  border-radius: var(--r-md);
  padding: 12px;
}
.glassTile {
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--shadow-sm), var(--shadow-inset);
  transition: transform 160ms ease, box-shadow 160ms ease;
}
.glassTile:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md), var(--shadow-inset);
}
.k {
  font-size: 12px;
  color: var(--app-subtext);
}
.v {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 900;
}
.mono {
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
.listTitle {
  margin-top: 14px;
  margin-bottom: 8px;
  font-weight: 800;
}
.studentGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}
.studentCard {
  border-radius: var(--r-md);
  padding: 10px;
  animation: fadeUp 260ms ease both;
}
.nm {
  font-weight: 800;
}
.id {
  margin-top: 2px;
  margin-bottom: 8px;
  color: var(--app-subtext);
  font-size: 12px;
}
.cf {
  margin-top: 6px;
  text-align: right;
  font-size: 12px;
  color: var(--app-subtext);
}
.btnGrad {
  border: none;
  background: var(--accent-grad);
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(122, 167, 255, 0.18), 0 18px 44px rgba(167, 139, 250, 0.14);
  transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
  position: relative;
  overflow: hidden;
}
.btnGrad:hover {
  transform: translateY(-1px);
  filter: saturate(1.05);
  box-shadow: 0 14px 34px rgba(122, 167, 255, 0.22), 0 22px 60px rgba(167, 139, 250, 0.16);
}
.btnGrad:active {
  transform: translateY(0) scale(0.985);
}
.btnGrad::after {
  content: "";
  position: absolute;
  inset: -60%;
  background: radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.0) 60%);
  opacity: 0;
  transform: scale(0.6);
  transition: opacity 220ms ease, transform 220ms ease;
  pointer-events: none;
}
.btnGrad:active::after {
  opacity: 0.95;
  transform: scale(1);
}
.btnSoft {
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border-radius: 12px;
  transition: transform 140ms ease, box-shadow 140ms ease;
  position: relative;
  overflow: hidden;
}
.btnSoft:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.btnSoft:active {
  transform: translateY(0) scale(0.985);
}
.btnSoft::after {
  content: "";
  position: absolute;
  inset: -80%;
  background: radial-gradient(circle at 50% 50%, rgba(122, 167, 255, 0.22) 0%, rgba(167, 139, 250, 0.0) 62%);
  opacity: 0;
  transform: scale(0.6);
  transition: opacity 220ms ease, transform 220ms ease;
  pointer-events: none;
}
.btnSoft:active::after {
  opacity: 1;
  transform: scale(1);
}
.metaRow {
  display: grid;
  gap: 6px;
}
.metaRow .k {
  font-size: 12px;
  color: var(--app-subtext);
}

.glassDivider {
  opacity: 0.7;
}

.glassEmpty {
  border-radius: var(--r-md);
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--shadow-sm), var(--shadow-inset);
  padding: 10px 0;
}

.glassTable :deep(.el-table) {
  border-radius: var(--r-md);
  overflow: hidden;
}
.glassTable :deep(.el-table__inner-wrapper) {
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-sm), var(--shadow-inset);
}
.glassTable :deep(.el-table__header-wrapper th.el-table__cell) {
  background: rgba(255, 255, 255, 0.35);
}
.glassTable :deep(.el-table__row) {
  transition: background 120ms ease;
}
.glassTable :deep(.el-table__row:hover > td.el-table__cell) {
  background: rgba(122, 167, 255, 0.08);
}

.pageCard :deep(.el-card__header) {
  border-bottom: 1px solid rgba(20, 20, 20, 0.06);
}
.pageCard :deep(.el-card__body) {
  padding-top: 14px;
}

.uploadPanel :deep(.el-input__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(20, 20, 20, 0.08);
  box-shadow: var(--shadow-inset);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
}
.uploadPanel :deep(.el-progress-bar__outer) {
  background: rgba(255, 255, 255, 0.38);
  border-radius: 999px;
}
.uploadPanel :deep(.el-progress-bar__inner) {
  border-radius: 999px;
}
</style>
