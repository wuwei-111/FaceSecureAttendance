<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div>
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

      <div class="previewBox" v-if="previewUrl">
        <el-button class="removePreviewBtn" circle @click="clearPickedImage">×</el-button>
        <el-image class="previewImage" :src="previewUrl" fit="contain" :preview-src-list="[previewUrl]" />
      </div>

      <el-upload
        class="uploader"
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
      <el-divider />

      <div class="stats" data-feature="photo-result">
        <div class="statCard">
          <div class="k">合照记录 ID</div>
          <div class="v">{{ result.group_photo_id }}</div>
        </div>
        <div class="statCard">
          <div class="k">成功匹配人数</div>
          <div class="v">{{ result.count }}</div>
        </div>
        <div class="statCard">
          <div class="k">匹配率</div>
          <div class="v">{{ matchedRate }}%</div>
        </div>
      </div>

      <div class="listTitle">识别名单</div>
      <el-empty v-if="matchedStudents.length === 0" description="当前返回结果为空" />

      <div v-else class="studentGrid">
        <div v-for="(item, idx) in matchedStudents" :key="`${item.student_id}-${idx}`" class="studentCard">
          <div class="nm">{{ item.name || "-" }}</div>
          <div class="id">学号：{{ item.student_id || "-" }}</div>
          <el-progress :percentage="toPct(item.confidence)" :stroke-width="6" :show-text="false" />
          <div class="cf">置信度 {{ toPct(item.confidence) }}%</div>
        </div>
      </div>
    </template>
  </el-card>
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
.hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.title {
  font-weight: 900;
}
.sub {
  font-size: 12px;
  color: var(--app-subtext);
}
.hdrActions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.uploadPanel {
  display: grid;
  gap: 12px;
}
.uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 360px;
  border-radius: 14px;
  border: 1px dashed rgba(20, 20, 20, 0.14);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.09) 0%, rgba(167, 139, 250, 0.08) 50%, rgba(52, 211, 153, 0.08) 100%);
}
.upTitle {
  font-weight: 800;
}
.upSub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--app-subtext);
}
.previewBox {
  position: relative;
  border: 1px solid rgba(20, 20, 20, 0.1);
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  min-height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.previewImage {
  max-width: 100%;
  max-height: 500px;
  width: auto;
  height: auto;
}
.removePreviewBtn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid rgba(20, 20, 20, 0.12);
  background: rgba(255, 255, 255, 0.92);
  color: #1f2937;
  font-size: 18px;
  line-height: 1;
  z-index: 2;
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
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.65);
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
  border-radius: 12px;
  padding: 10px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: rgba(255, 255, 255, 0.65);
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
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}
.btnSoft {
  border: 1px solid rgba(20, 20, 20, 0.12);
  background: rgba(255, 255, 255, 0.65);
}
.metaRow {
  display: grid;
  gap: 6px;
}
.metaRow .k {
  font-size: 12px;
  color: var(--app-subtext);
}
</style>
