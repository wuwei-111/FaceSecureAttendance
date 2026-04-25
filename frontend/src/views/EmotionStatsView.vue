<template>
  <el-card>
    <template #header>
      <span>情绪分析统计</span>
    </template>

    <el-button :loading="loading" type="primary" @click="load">刷新</el-button>

    <el-divider />

    <el-descriptions v-if="stats" :column="1" border>
      <el-descriptions-item label="total">{{ stats.total }}</el-descriptions-item>
      <el-descriptions-item label="distribution">
        <pre style="margin: 0">{{ JSON.stringify(stats.distribution, null, 2) }}</pre>
      </el-descriptions-item>
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
import { onMounted, ref } from "vue";
import { fetchEmotionStats } from "../api/emotion";

const stats = ref(null);
const err = ref("");
const loading = ref(false);

async function load() {
  err.value = "";
  loading.value = true;
  try {
    stats.value = await fetchEmotionStats();
  } catch (e) {
    err.value = e?.response?.data?.detail || e?.message || "请求失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
