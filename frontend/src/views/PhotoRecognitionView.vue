<template>
  <el-card>
    <template #header>
      <span>合照学生识别</span>
    </template>

    <el-form label-width="100px" class="toolbar">
      <el-form-item label="活动名称">
        <el-input v-model="activityName" placeholder="可选，便于统计归类" clearable style="max-width: 420px" />
      </el-form-item>
      <el-form-item label="合照图片">
        <input type="file" accept="image/*" @change="onPick" />
      </el-form-item>
    </el-form>

    <el-alert
      v-if="loading"
      type="info"
      :closable="false"
      show-icon
      title="正在检测人脸并比对学号，请稍候..."
      style="margin-bottom: 12px"
    />

    <el-descriptions v-if="result" :column="1" border>
      <el-descriptions-item label="group_photo_id">{{ result.group_photo_id }}</el-descriptions-item>
      <el-descriptions-item label="检测到人脸数">{{ result.total_faces_detected }}</el-descriptions-item>
      <el-descriptions-item label="匹配学生数">{{ result.count }}</el-descriptions-item>
    </el-descriptions>

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
  </el-card>
</template>

<script setup>
import { ref } from "vue";
import { recognizeGroupPhoto } from "../api/photo";
import { getErrorMessage } from "../api/client";

const result = ref(null);
const err = ref("");
const loading = ref(false);
const activityName = ref("");

async function onPick(e) {
  err.value = "";
  result.value = null;
  const file = e?.target?.files?.[0];
  if (!file) return;
  loading.value = true;
  try {
    result.value = await recognizeGroupPhoto(file, activityName.value);
  } catch (ex) {
    err.value = getErrorMessage(ex);
  } finally {
    loading.value = false;
    e.target.value = "";
  }
}
</script>

<style scoped>
.toolbar {
  margin-bottom: 8px;
}
</style>
