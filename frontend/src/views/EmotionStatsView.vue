<template>
  <el-card>
    <template #header>
      <span>情绪分析统计</span>
    </template>

    <div class="filters">
      <el-date-picker
        v-model="statsRange"
        type="daterange"
        range-separator="至"
        start-placeholder="统计开始"
        end-placeholder="统计结束"
        style="width: 320px"
        @change="loadStats"
      />
      <el-button :loading="loadingStats" type="primary" @click="loadStats">刷新统计</el-button>
    </div>

    <el-descriptions v-if="stats" :column="1" border>
      <el-descriptions-item label="样本数">{{ stats.total }}</el-descriptions-item>
      <el-descriptions-item label="分布">
        <pre style="margin: 0">{{ JSON.stringify(stats.distribution, null, 2) }}</pre>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <div class="filters">
      <el-input v-model="recQ" placeholder="学号/姓名" clearable style="width: 200px" @keyup.enter="loadRecords" />
      <el-select v-model="recEmotion" placeholder="情绪" filterable allow-create style="width: 180px" @change="loadRecords">
        <el-option label="全部" value="all" />
        <el-option v-for="k in mergedEmotionOpts" :key="k" :label="k" :value="k" />
      </el-select>
      <el-date-picker
        v-model="recRange"
        type="daterange"
        range-separator="至"
        start-placeholder="记录开始"
        end-placeholder="记录结束"
        style="width: 320px"
        @change="onRecRangeChange"
      />
      <el-button :loading="loadingRec" @click="loadRecords">查询记录</el-button>
    </div>

    <el-table :data="recRows" v-loading="loadingRec" size="small" stripe style="width: 100%; margin-top: 12px">
      <el-table-column prop="student_no" label="学号" width="120" />
      <el-table-column prop="student_name" label="姓名" width="100" />
      <el-table-column prop="emotion" label="情绪" width="100" />
      <el-table-column prop="confidence" label="置信度" width="100" />
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="record_time" label="时间" min-width="180" />
    </el-table>

    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :page-size="pageSize"
        :total="recTotal"
        v-model:current-page="recPage"
        @current-change="loadRecords"
      />
    </div>

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
import { computed, onMounted, ref } from "vue";
import { fetchEmotionRecords, fetchEmotionStats } from "../api/emotion";
import { getErrorMessage } from "../api/client";

const stats = ref(null);
const statsRange = ref([]);
const loadingStats = ref(false);

const recRows = ref([]);
const recTotal = ref(0);
const recPage = ref(1);
const pageSize = 10;
const recQ = ref("");
const recEmotion = ref("all");
const recRange = ref([]);
const loadingRec = ref(false);

const err = ref("");

const emotionKeys = computed(() => (stats.value?.distribution ? Object.keys(stats.value.distribution) : []));
const mergedEmotionOpts = computed(() => {
  const base = ["neutral", "happy", "sad", "angry", "surprise"];
  const set = new Set([...emotionKeys.value, ...base]);
  return Array.from(set);
});

function fmtDate(d) {
  if (!d) return undefined;
  const x = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(x.getTime())) return undefined;
  const y = x.getFullYear();
  const m = String(x.getMonth() + 1).padStart(2, "0");
  const day = String(x.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

async function loadStats() {
  err.value = "";
  loadingStats.value = true;
  try {
    const params = {};
    if (statsRange.value?.length === 2) {
      params.date_from = fmtDate(statsRange.value[0]);
      params.date_to = fmtDate(statsRange.value[1]);
    }
    stats.value = await fetchEmotionStats(params);
  } catch (e) {
    err.value = getErrorMessage(e);
  } finally {
    loadingStats.value = false;
  }
}

function onRecRangeChange() {
  recPage.value = 1;
  loadRecords();
}

async function loadRecords() {
  err.value = "";
  loadingRec.value = true;
  try {
    const params = {
      q: recQ.value.trim(),
      emotion: recEmotion.value,
      page: recPage.value,
      page_size: pageSize
    };
    if (recRange.value?.length === 2) {
      params.date_from = fmtDate(recRange.value[0]);
      params.date_to = fmtDate(recRange.value[1]);
    }
    const data = await fetchEmotionRecords(params);
    recRows.value = (data.items || []).map((x) => ({
      ...x,
      record_time: x.record_time ? new Date(x.record_time).toLocaleString() : "-",
      confidence: typeof x.confidence === "number" ? x.confidence.toFixed(3) : "-"
    }));
    recTotal.value = Number(data.total || 0);
  } catch (e) {
    err.value = getErrorMessage(e);
  } finally {
    loadingRec.value = false;
  }
}

onMounted(async () => {
  await loadStats();
  await loadRecords();
});
</script>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
