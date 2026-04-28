<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div>
          <div class="t">考勤记录查询</div>
          <div class="s">支持按日期与状态筛选；导出与列表使用相同筛选条件。</div>
        </div>
        <div class="hdrBtns">
          <el-button class="btnGrad" type="primary" :loading="exportingA" @click="onExportAttendance">
            导出考勤 Excel
          </el-button>
          <el-button type="primary" plain :loading="exportingAct" @click="onExportActivity">
            导出活动 Excel
          </el-button>
        </div>
      </div>
    </template>

    <div class="filters glass">
      <div class="fi">
        <div class="k">日期范围</div>
        <el-date-picker
          v-model="range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 100%"
        />
      </div>
      <div class="fi small">
        <div class="k">状态</div>
        <el-select v-model="status" placeholder="状态" style="width: 100%">
          <el-option label="全部" value="all" />
          <el-option label="成功" value="present" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <div class="fi">
        <div class="k">关键字</div>
        <el-input v-model="keyword" placeholder="学号 / 姓名" />
      </div>
      <div class="act">
        <el-button @click="onReset">重置</el-button>
        <el-button class="btnGrad" type="primary" @click="onSearch">查询</el-button>
      </div>
    </div>

    <el-table :data="rows" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="student_id" label="学号" width="140" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="time" label="考勤时间" min-width="180" />
      <el-table-column prop="emotion" label="情绪" width="100" />
      <el-table-column prop="confidence" label="置信度" width="100" />
    </el-table>

    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :page-size="pageSize"
        :total="total"
        v-model:current-page="page"
        @current-change="load"
      />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchAttendanceRecords } from "../api/attendance";
import { downloadActivityExcel, downloadAttendanceExcel } from "../api/export";
import { getErrorMessage } from "../api/client";

const range = ref([]);
const status = ref("all");
const keyword = ref("");
const loading = ref(false);
const page = ref(1);
const pageSize = 10;
const total = ref(0);

const rows = ref([]);
const exportingA = ref(false);
const exportingAct = ref(false);

function onSearch() {
  page.value = 1;
  load();
}

function onReset() {
  range.value = [];
  status.value = "all";
  keyword.value = "";
  page.value = 1;
  load();
}

function fmtTime(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}

function fmtDateBoundary(d) {
  if (!d) return undefined;
  const x = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(x.getTime())) return undefined;
  const y = x.getFullYear();
  const m = String(x.getMonth() + 1).padStart(2, "0");
  const day = String(x.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function listParams() {
  const params = {
    q: keyword.value.trim(),
    status: status.value,
    page: page.value,
    page_size: pageSize
  };
  if (range.value?.length === 2) {
    params.date_from = fmtDateBoundary(range.value[0]);
    params.date_to = fmtDateBoundary(range.value[1]);
  }
  return params;
}

async function load() {
  loading.value = true;
  try {
    const data = await fetchAttendanceRecords(listParams());
    rows.value = (data.items || []).map((x) => ({
      student_id: x.student_no || "-",
      name: x.student_name || "-",
      status: x.status,
      time: fmtTime(x.check_time),
      emotion: x.emotion || "-",
      confidence: typeof x.confidence === "number" ? x.confidence.toFixed(3) : "-"
    }));
    total.value = Number(data.total || 0);
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    loading.value = false;
  }
}

async function onExportAttendance() {
  exportingA.value = true;
  try {
    const { page: _p, page_size: _ps, ...rest } = listParams();
    await downloadAttendanceExcel(rest);
    ElMessage.success("已开始下载");
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    exportingA.value = false;
  }
}

async function onExportActivity() {
  exportingAct.value = true;
  try {
    const params = {};
    if (range.value?.length === 2) {
      params.date_from = fmtDateBoundary(range.value[0]);
      params.date_to = fmtDateBoundary(range.value[1]);
    }
    if (keyword.value.trim()) params.q = keyword.value.trim();
    await downloadActivityExcel(params);
    ElMessage.success("已开始下载");
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    exportingAct.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.hdrBtns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.t {
  font-weight: 900;
}
.s {
  font-size: 12px;
  color: var(--app-subtext);
}
.filters {
  margin-bottom: 14px;
  padding: 12px;
  border-radius: 12px;
  display: grid;
  grid-template-columns: minmax(260px, 1.35fr) minmax(120px, 0.7fr) minmax(260px, 1.35fr) auto;
  gap: 10px;
  align-items: end;
}
.fi {
  display: grid;
  gap: 6px;
}
.fi.small {
  min-width: 120px;
}
.k {
  font-size: 12px;
  color: var(--app-subtext);
}
.act {
  display: flex;
  gap: 8px;
  margin-bottom: 0;
  align-self: end;
}
.btnGrad {
  border: none;
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
@media (max-width: 1100px) {
  .filters {
    grid-template-columns: 1fr 1fr;
  }
  .act {
    justify-content: flex-end;
  }
}
</style>

