<template>
  <el-card>
    <template #header>
      <span>基础考勤</span>
    </template>

    <CameraCapture @captured="onCaptured" />

    <el-divider />

    <el-descriptions v-if="result" :column="1" border>
      <el-descriptions-item label="status">{{ result.status }}</el-descriptions-item>
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
import { ref } from "vue";
import CameraCapture from "../components/CameraCapture.vue";
import { checkinWithImageBlob } from "../api/attendance";

const result = ref(null);
const err = ref("");

async function onCaptured(blob) {
  err.value = "";
  result.value = null;
  try {
    result.value = await checkinWithImageBlob(blob);
  } catch (e) {
    err.value = e?.response?.data?.detail || e?.message || "请求失败";
  }
}
</script>
