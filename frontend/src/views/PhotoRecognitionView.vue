<template>
  <el-card>
    <template #header>
      <span>合照学生识别</span>
    </template>

    <input type="file" accept="image/*" @change="onPick" />

    <el-divider />

    <el-descriptions v-if="result" :column="1" border>
      <el-descriptions-item label="group_photo_id">{{
        result.group_photo_id
      }}</el-descriptions-item>
      <el-descriptions-item label="count">{{ result.count }}</el-descriptions-item>
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
import { ref } from "vue";
import { recognizeGroupPhoto } from "../api/photo";

const result = ref(null);
const err = ref("");

async function onPick(e) {
  err.value = "";
  result.value = null;
  const file = e?.target?.files?.[0];
  if (!file) return;
  try {
    result.value = await recognizeGroupPhoto(file);
  } catch (ex) {
    err.value = ex?.response?.data?.detail || ex?.message || "请求失败";
  } finally {
    e.target.value = "";
  }
}
</script>
