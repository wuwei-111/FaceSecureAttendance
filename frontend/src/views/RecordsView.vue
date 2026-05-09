<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div>
          <div class="t">考勤记录查询</div>
          <div class="s">支持按日期与状态筛选；导出与列表使用相同筛选条件。</div>
        </div>
        <div class="hdrBtns">
          <el-tooltip v-if="!isTeacher" content="仅教师可导出">
            <el-button class="btnGrad" type="primary" disabled>导出考勤 Excel</el-button>
          </el-tooltip>
          <el-button
            v-else
            class="btnGrad"
            type="primary"
            :loading="exportingA"
            :disabled="rows.length === 0"
            @click="onExportAttendance"
          >
            导出考勤 Excel
          </el-button>

          <el-tooltip v-if="!isTeacher" content="仅教师可导出">
            <el-button type="primary" plain disabled>导出活动 Excel</el-button>
          </el-tooltip>
          <el-button
            v-else
            type="primary"
            plain
            :loading="exportingAct"
            :disabled="rows.length === 0"
            @click="onExportActivity"
          >
            导出活动 Excel
          </el-button>
        </div>
      </div>
    </template>

    <div class="filters glass" data-feature="records-filter">
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
      <div class="fi">
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
    </div>
    <div class="act">
      <el-button @click="onReset">重置</el-button>
      <el-button class="btnGrad" type="primary" @click="onSearch">查询</el-button>
    </div>

    <el-table :data="rows" stripe style="width: 100%" v-loading="loading" data-feature="records-table">
      <el-table-column prop="student_id" label="学号" width="140" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="status_display" label="状态" width="120" />
      <el-table-column prop="time" label="考勤时间" min-width="180" />
      <el-table-column prop="emotion" label="情绪" width="100" />
      <el-table-column prop="confidence" label="置信度" width="100" />
      <el-table-column v-if="isTeacher" label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-popconfirm title="确认删除这条考勤记录吗？" @confirm="onDelete(row)">
            <template #reference>
              <el-button type="danger" link :disabled="deletingId === row.record_id">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
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
import { deleteAttendanceRecord, fetchAttendanceRecords } from "../api/attendance";
import { downloadActivityExcel, downloadAttendanceExcel } from "../api/export";
import { getErrorMessage } from "../api/client";
import { isTeacherRole } from "../utils/auth";

const range = ref([]);
const status = ref("all");
const keyword = ref("");
const loading = ref(false);
const page = ref(1);
const pageSize = 10;
const total = ref(0);
const exportingA = ref(false);
const exportingAct = ref(false);
const deletingId = ref(null);

const rows = ref([]);
const isTeacher = isTeacherRole();

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

function formatRecordStatus(s) {
  if (!s) return "-";
  if (s === "present") return "成功";
  if (s === "failed") return "未匹配";
  if (s === "failed_ambiguous") return "无法唯一确认";
  if (String(s).startsWith("failed_liveness")) return "活体未通过";
  return s;
}

function fmtTime(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(d);
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
      record_id: x.record_id,
      student_id: x.student_no || "-",
      name: x.student_name || "-",
      status: x.status,
      status_display: formatRecordStatus(x.status),
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

async function onDelete(row) {
  if (!isTeacher || !row?.record_id) return;
  deletingId.value = row.record_id;
  try {
    await deleteAttendanceRecord(row.record_id);
    ElMessage.success("删除成功");
    if (rows.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    await load();
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    deletingId.value = null;
  }
}

async function onExportAttendance() {
  if (!isTeacher) return;
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
  if (!isTeacher) return;
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
  grid-template-columns: minmax(320px, 1.5fr) minmax(140px, 0.6fr) minmax(240px, 1fr);
  gap: 14px;
  align-items: end;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.09) 0%, rgba(167, 139, 250, 0.07) 55%, rgba(52, 211, 153, 0.07) 100%);
}
.fi {
  display: grid;
  gap: 6px;
  min-width: 0;
}
.k {
  font-size: 12px;
  color: var(--app-subtext);
}
.act {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  justify-content: flex-end;
}
.filters :deep(.el-date-editor) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}
.filters :deep(.el-date-editor .el-input__wrapper) {
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}
.filters :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.22) inset;
}
.filters :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.45) inset;
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
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>

