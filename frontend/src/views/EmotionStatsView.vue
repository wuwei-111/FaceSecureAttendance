<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div>
          <div class="title">情绪分析统计</div>
          <div class="sub">班级情绪分布可视化（当前基于已有 `/emotion/stats`）</div>
        </div>
        <el-button class="btnGrad" :loading="loadingStats" type="primary" :disabled="!isTeacher" @click="loadStats">
          刷新
        </el-button>
      </div>
    </template>

    <el-alert
      v-if="!isTeacher"
      type="warning"
      :closable="false"
      show-icon
      title="当前账号无教师权限，仅可查看页面占位内容"
      style="margin-bottom: 12px"
    />

    <div class="filtersWrap" v-if="isTeacher">
      <div class="filters glass">
        <div class="fi">
          <div class="k">学号筛选</div>
          <el-input v-model="studentNo" clearable placeholder="输入学号（记录筛选用）" />
        </div>
        <div class="fi">
          <div class="k">日期范围</div>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </div>
        <div class="act">
          <el-button @click="onResetFilter">重置</el-button>
          <el-button class="btnGrad" type="primary" :loading="loadingStats" @click="loadStats">应用筛选</el-button>
        </div>
      </div>
    </div>

    <el-alert
      v-if="isTeacher && (studentNo || dateRange.length)"
      type="info"
      :closable="false"
      show-icon
      title="注意：/emotion/stats 当前仅支持日期范围；学号筛选会作用于下方“记录列表”。"
      style="margin-bottom: 12px"
    />

    <div class="statsRow" v-if="stats">
      <div class="statCard">
        <div class="k">总记录数</div>
        <div class="v">{{ stats.total || 0 }}</div>
      </div>
      <div class="statCard">
        <div class="k">情绪类别数</div>
        <div class="v">{{ pieData.length }}</div>
      </div>
    </div>

    <div class="charts" data-feature="emotion-chart">
      <div class="chartCard">
        <div class="chartTitle">情绪分布（饼图）</div>
        <div ref="pieEl" class="chart"></div>
      </div>
      <div class="chartCard">
        <div class="chartTitle">情绪占比（柱状图）</div>
        <div ref="barEl" class="chart"></div>
      </div>
    </div>

    <el-table v-if="tableRows.length > 0" :data="tableRows" stripe style="width: 100%; margin-top: 12px" data-feature="emotion-table">
      <el-table-column prop="emotion" label="情绪" width="160" />
      <el-table-column prop="count" label="数量" width="120" />
      <el-table-column prop="ratio" label="占比" />
    </el-table>

    <el-divider />

    <div class="recFilters glass">
      <div class="recFi">
        <div class="k">关键字</div>
        <el-input v-model="recQ" placeholder="学号/姓名" clearable @keyup.enter="loadRecords" />
      </div>
      <div class="recFi">
        <div class="k">情绪</div>
        <el-select v-model="recEmotion" placeholder="情绪" filterable allow-create @change="loadRecords">
          <el-option label="全部" value="all" />
          <el-option v-for="k in mergedEmotionOpts" :key="k" :label="k" :value="k" />
        </el-select>
      </div>
      <div class="recFi">
        <div class="k">记录时间</div>
        <el-date-picker
          v-model="recRange"
          type="daterange"
          range-separator="至"
          start-placeholder="记录开始"
          end-placeholder="记录结束"
          @change="onRecRangeChange"
        />
      </div>
      <div class="recAct">
        <el-button :loading="loadingRec" @click="loadRecords">查询记录</el-button>
      </div>
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { fetchEmotionRecords, fetchEmotionStats } from "../api/emotion";
import { isTeacherRole } from "../utils/auth";
import { getErrorMessage } from "../api/client";

const stats = ref(null);
const err = ref("");
const loadingStats = ref(false);
const isTeacher = isTeacherRole();
const studentNo = ref("");
const dateRange = ref([]);

const pieEl = ref(null);
const barEl = ref(null);
let pieChart = null;
let barChart = null;

const pieData = computed(() => {
  const dist = stats.value?.distribution || {};
  return Object.entries(dist)
    .map(([name, value]) => ({ name, value: Number(value || 0) }))
    .sort((a, b) => b.value - a.value);
});

const tableRows = computed(() => {
  const total = Math.max(1, Number(stats.value?.total || 0));
  return pieData.value.map((x) => ({
    emotion: x.name,
    count: x.value,
    ratio: `${((x.value / total) * 100).toFixed(1)}%`
  }));
});

function renderCharts() {
  if (!pieEl.value || !barEl.value) return;
  if (!pieChart) pieChart = echarts.init(pieEl.value);
  if (!barChart) barChart = echarts.init(barEl.value);

  pieChart.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["42%", "70%"],
        center: ["50%", "46%"],
        data: pieData.value,
        label: { formatter: "{b}: {d}%" }
      }
    ]
  });

  barChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: pieData.value.map((x) => x.name), axisLabel: { interval: 0 } },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: pieData.value.map((x) => x.value),
        barMaxWidth: 42,
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#7aa7ff" },
            { offset: 0.55, color: "#a78bfa" },
            { offset: 1, color: "#34d399" }
          ])
        }
      }
    ]
  });
}

const recRows = ref([]);
const recTotal = ref(0);
const recPage = ref(1);
const pageSize = 10;
const recQ = ref("");
const recEmotion = ref("all");
const recRange = ref([]);
const loadingRec = ref(false);

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
    if (dateRange.value?.length === 2) {
      params.date_from = fmtDate(dateRange.value[0]);
      params.date_to = fmtDate(dateRange.value[1]);
    }
    stats.value = await fetchEmotionStats(params);
    await nextTick();
    renderCharts();
  } catch (e) {
    err.value = getErrorMessage(e);
  } finally {
    loadingStats.value = false;
  }
}

function onResetFilter() {
  studentNo.value = "";
  dateRange.value = [];
  loadStats();
  recQ.value = "";
  recEmotion.value = "all";
  recRange.value = [];
  recPage.value = 1;
  loadRecords();
}

function onResize() {
  pieChart?.resize();
  barChart?.resize();
}

onMounted(async () => {
  if (isTeacher) {
    await loadStats();
    await loadRecords();
    window.addEventListener("resize", onResize);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  pieChart?.dispose();
  barChart?.dispose();
  pieChart = null;
  barChart = null;
});

function onRecRangeChange() {
  recPage.value = 1;
  loadRecords();
}

async function loadRecords() {
  err.value = "";
  loadingRec.value = true;
  try {
    const params = {
      q: (recQ.value || studentNo.value || "").trim(),
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
  margin-top: 2px;
  color: var(--app-subtext);
  font-size: 12px;
}
.btnGrad {
  border: none;
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}
.filtersWrap {
  display: flex;
  justify-content: flex-start;
}
.filters {
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
  align-items: end;
  width: min(680px, 100%);
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.09) 0%, rgba(167, 139, 250, 0.07) 55%, rgba(52, 211, 153, 0.07) 100%);
}
.fi {
  display: grid;
  gap: 6px;
}
.act {
  display: flex;
  gap: 8px;
}
.recFilters {
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.09) 0%, rgba(167, 139, 250, 0.07) 55%, rgba(52, 211, 153, 0.07) 100%);
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(150px, 0.8fr) minmax(320px, 1.5fr) auto;
  gap: 10px;
  align-items: end;
  width: 100%;
  box-sizing: border-box;
}
.recFi {
  min-width: 0;
  display: grid;
  gap: 6px;
}
.recAct {
  display: flex;
  align-items: flex-end;
}
.recFilters :deep(.el-select),
.recFilters :deep(.el-date-editor) {
  width: 100%;
  min-width: 0;
}
.recFilters :deep(.el-date-editor .el-input__wrapper) {
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
.statsRow {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}
.statCard {
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.12) 0%, rgba(255, 255, 255, 0.84) 45%, rgba(167, 139, 250, 0.12) 100%);
}
.k {
  color: var(--app-subtext);
  font-size: 12px;
}
.v {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 900;
}
.charts {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.chartCard {
  border-radius: 12px;
  padding: 10px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.1) 0%, rgba(255, 255, 255, 0.86) 48%, rgba(52, 211, 153, 0.1) 100%);
}
:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.08) 0%, rgba(255, 255, 255, 0.9) 100%);
}
.chartTitle {
  font-weight: 800;
  margin-bottom: 8px;
}
.chart {
  height: 320px;
}
@media (max-width: 1100px) {
  .filters {
    grid-template-columns: 1fr;
  }
  .recFilters {
    grid-template-columns: 1fr;
  }
  .recAct {
    justify-content: flex-end;
  }
  .charts {
    grid-template-columns: 1fr;
  }
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
