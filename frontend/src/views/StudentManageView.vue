<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div class="left">
          <div class="t">学生人脸库管理</div>
          <div class="s">管理学生信息与人脸照片。</div>
        </div>
        <div class="right">
          <el-input
            v-model="q"
            clearable
            placeholder="搜索：学号 / 姓名 / 班级"
            style="width: 260px"
            @keyup.enter="load"
          />
          <el-button class="btnGrad" type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon>
            新增学生
          </el-button>
          <el-button
            type="primary"
            plain
            :disabled="selectedRows.length !== 1"
            @click="openEdit"
          >
            编辑学生
          </el-button>
          <el-upload
            :show-file-list="false"
            accept=".csv,text/csv"
            :auto-upload="false"
            @change="onCsvPicked"
          >
            <el-button :loading="importing">批量导入 CSV</el-button>
          </el-upload>
          <el-button :loading="loading" @click="load">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="6" animated />

    <template v-else>
      <el-alert
        v-if="offlineTip"
        type="warning"
        show-icon
        :closable="false"
        title="学生列表加载失败：请确认后端已启动并已使用教师账号登录。"
        style="margin-bottom: 12px"
      />

      <div class="tableActions">
        <el-button class="opBtn" size="small" :disabled="selectedRows.length !== 1 || isBusy(selectedPrimary?.id)" @click="openDetail(selectedPrimary)">
          查看详情
        </el-button>
        <el-button
          class="opBtn opBtnPri"
          size="small"
          :disabled="selectedRows.length !== 1 || isBusy(selectedPrimary?.id)"
          :loading="selectedPrimary ? isUploading(selectedPrimary.id) : false"
          @click="openUploadForSelected"
        >
          上传人脸
        </el-button>
        <el-button
          class="opBtn opBtnDanger"
          size="small"
          :disabled="selectedRows.length === 0"
          @click="onDeleteSelected"
        >
          删除学生{{ selectedRows.length > 1 ? `(${selectedRows.length})` : "" }}
        </el-button>
        <el-button class="opBtn" size="small" :disabled="selectedRows.length === 0" @click="clearSelected">
          取消选中
        </el-button>
      </div>

      <el-table
        ref="tableRef"
        :data="items"
        size="small"
        stripe
        row-key="id"
        style="width: 100%"
        :row-class-name="rowClassName"
        @row-dblclick="openDetail"
        @selection-change="onSelectionChange"
        @row-click="onRowClick"
        @row-mousedown="onRowMouseDown"
        @row-mouseup="onRowMouseUp"
      >
        <el-table-column type="selection" width="42" />
        <el-table-column prop="student_id" label="学号" width="116" />
        <el-table-column prop="name" label="姓名" width="96" />
        <el-table-column prop="class_name" label="班级" min-width="120" />
        <el-table-column label="人脸" width="86">
          <template #default="{ row }">
            <el-tag v-if="row.face_path" type="success" effect="light">已上传</el-tag>
            <el-tag v-else type="info" effect="light">未上传</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-progress
        v-if="selectedPrimary && uploadPct[selectedPrimary.id] != null"
        :percentage="uploadPct[selectedPrimary.id]"
        :stroke-width="6"
        :show-text="false"
        style="margin-top: 10px"
      />

      <div class="ft">
        <el-pagination
          background
          layout="prev, pager, next"
          :page-size="pageSize"
          :total="total"
          v-model:current-page="page"
          @current-change="load"
        />
      </div>
    </template>
  </el-card>

  <el-drawer v-model="createOpen" title="新增学生" size="420px">
    <el-form ref="createFormRef" label-width="90px" :model="createForm" :rules="rules">
      <el-form-item label="学号" prop="student_id">
        <el-input
          v-model="createForm.student_id"
          placeholder="例如：20231234"
          autocomplete="off"
        />
      </el-form-item>
      <el-form-item label="姓名" prop="name">
        <el-input v-model="createForm.name" placeholder="例如：张三" autocomplete="off" />
      </el-form-item>
      <el-form-item label="班级">
        <el-input v-model="createForm.class_name" placeholder="例如：计科 1 班" autocomplete="off" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div style="display: flex; gap: 10px; justify-content: flex-end">
        <el-button @click="createOpen = false">取消</el-button>
        <el-button class="btnGrad" type="primary" :loading="saving" @click="onCreate">保存</el-button>
      </div>
    </template>
  </el-drawer>

  <el-drawer v-model="editOpen" title="编辑学生" size="420px">
    <el-form ref="editFormRef" label-width="90px" :model="editForm" :rules="rules">
      <el-form-item label="学号" prop="student_id">
        <el-input v-model="editForm.student_id" placeholder="学号" autocomplete="off" />
      </el-form-item>
      <el-form-item label="姓名" prop="name">
        <el-input v-model="editForm.name" placeholder="姓名" autocomplete="off" />
      </el-form-item>
      <el-form-item label="班级">
        <el-input v-model="editForm.class_name" placeholder="班级（可选）" autocomplete="off" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div style="display: flex; gap: 10px; justify-content: flex-end">
        <el-button @click="editOpen = false">取消</el-button>
        <el-button class="btnGrad" type="primary" :loading="editSaving" @click="onEditSave">
          保存
        </el-button>
      </div>
    </template>
  </el-drawer>

  <el-drawer v-model="detailOpen" title="学生详情" size="520px">
    <template v-if="current">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="ID">{{ current.id }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ current.student_id }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ current.name }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ current.class_name || "-" }}</el-descriptions-item>
        <el-descriptions-item label="face_path">{{ current.face_path || "-" }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <div class="preview">
        <div class="pTitle">人脸预览</div>
        <div class="pBox">
          <el-image v-if="previewUrl" class="previewImage" :src="previewUrl" fit="contain" :preview-src-list="[previewUrl]" />
          <el-empty v-else description="未选择/未上传" />
        </div>
        <div class="pAct">
          <el-upload
            :show-file-list="false"
            :auto-upload="false"
            accept="image/*"
            @change="(f) => onPickFace(current, f, true)"
          >
            <el-button class="btnSoft" type="primary" plain :loading="isUploading(current.id)">
              <el-icon><Upload /></el-icon>
              选择图片
            </el-button>
          </el-upload>
          <el-button
            class="opBtn opBtnDanger"
            plain
            :disabled="!current.face_path || isBusy(current.id)"
            @click="onRemoveFace(current)"
          >
            取消已上传人脸
          </el-button>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Refresh, Upload } from "@element-plus/icons-vue";
import {
  batchImportStudents,
  createStudent,
  deleteStudent,
  deleteStudentFace,
  listStudents,
  updateStudent,
  uploadStudentFace
} from "../api/students";
import { api, getErrorMessage } from "../api/client";

const loading = ref(false);
const saving = ref(false);
const editSaving = ref(false);
const importing = ref(false);
const offlineTip = ref(false);

const q = ref("");
const page = ref(1);
const pageSize = 10;
const total = ref(0);

const createOpen = ref(false);
const editOpen = ref(false);
const detailOpen = ref(false);
const current = ref(null);
const previewUrl = ref("");
const createFormRef = ref(null);
const editFormRef = ref(null);
const tableRef = ref(null);
const selectedRows = ref([]);
const longPressTimer = ref(null);
const longPressHandled = ref(false);

const uploadPct = ref({});
const busyIds = ref(new Set());

const createForm = ref({
  student_id: "",
  name: "",
  class_name: ""
});

const editForm = ref({
  id: null,
  student_id: "",
  name: "",
  class_name: ""
});

const rules = {
  student_id: [
    { required: true, message: "请输入学号", trigger: "blur" },
    { min: 4, max: 32, message: "学号长度 4-32", trigger: "blur" }
  ],
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }]
};

const items = ref([]);

function openCreate() {
  createForm.value = { student_id: "", name: "", class_name: "" };
  createOpen.value = true;
  createFormRef.value?.clearValidate?.();
}

function openEdit() {
  const row = selectedPrimary.value;
  if (!row) return;
  editForm.value = {
    id: row.id,
    student_id: row.student_id,
    name: row.name,
    class_name: row.class_name || ""
  };
  editOpen.value = true;
  editFormRef.value?.clearValidate?.();
}

async function onEditSave() {
  const ok = await editFormRef.value?.validate?.().catch(() => false);
  if (!ok) return;
  editSaving.value = true;
  try {
    const payload = {
      student_id: editForm.value.student_id.trim(),
      name: editForm.value.name.trim(),
      class_name: editForm.value.class_name.trim()
    };
    const data = await updateStudent(editForm.value.id, payload);
    editOpen.value = false;
    ElMessage.success("已保存");
    await load();
    if (current.value?.id === data?.id) {
      current.value = data;
      previewUrl.value = resolveFacePreview(data, true);
    }
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    editSaving.value = false;
  }
}

async function onCsvPicked(uploadFile) {
  const file = fileFromUploadChange(uploadFile);
  if (!file) return;
  importing.value = true;
  try {
    const res = await batchImportStudents(file);
    const parts = [
      `新增 ${res.created ?? 0}`,
      `跳过 ${res.skipped ?? 0}`,
      `失败 ${res.failed ?? 0}`
    ];
    ElMessage.success(parts.join("，"));
    if (Array.isArray(res.errors) && res.errors.length) {
      ElMessage.warning(res.errors.slice(0, 5).join("\n"));
    }
    await load();
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    importing.value = false;
  }
}

function openDetail(row) {
  if (!row) return;
  current.value = row;
  previewUrl.value = resolveFacePreview(row, true);
  detailOpen.value = true;
}

async function load() {
  loading.value = true;
  offlineTip.value = false;
  try {
    const data = await listStudents({
      q: q.value.trim(),
      page: page.value,
      page_size: pageSize
    });
    if (Array.isArray(data?.items)) {
      items.value = data.items;
      total.value = Number(data.total || 0);
    }
  } catch (e) {
    offlineTip.value = true;
    ElMessage.warning(getErrorMessage(e));
  } finally {
    loading.value = false;
  }
}

async function onCreate() {
  const payload = {
    student_id: createForm.value.student_id.trim(),
    name: createForm.value.name.trim(),
    class_name: createForm.value.class_name.trim()
  };
  const ok = await createFormRef.value?.validate?.().catch(() => false);
  if (!ok) return;

  saving.value = true;
  try {
    await createStudent(payload);
    createOpen.value = false;
    ElMessage.success("已创建");
    page.value = 1;
    await load();
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    saving.value = false;
  }
}

async function onDelete(row) {
  try {
    busyIds.value.add(row.id);
    await deleteStudent(row.id);
    items.value = items.value.filter((x) => x.id !== row.id);
    total.value = Math.max(0, total.value - 1);
    ElMessage.success("已删除");
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    busyIds.value.delete(row.id);
  }
}

async function onRemoveFace(row) {
  if (!row) return;
  try {
    await ElMessageBox.confirm("确定取消该学生已上传的人脸图片与编码吗？", "确认", {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消"
    });
    busyIds.value.add(row.id);
    await deleteStudentFace(row.id);
    row.face_path = null;
    if (current.value?.id === row.id) {
      previewUrl.value = "";
    }
    ElMessage.success("已取消该学生人脸数据");
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.warning(getErrorMessage(e));
    }
  } finally {
    busyIds.value.delete(row.id);
  }
}

function onSelectionChange(rows) {
  selectedRows.value = rows || [];
}

function openUploadForSelected() {
  if (!selectedPrimary.value) return;
  current.value = selectedPrimary.value;
  detailOpen.value = true;
}

const selectedPrimary = computed(() => selectedRows.value[0] || null);

function toggleRowSelected(row) {
  if (!tableRef.value || !row) return;
  const exists = selectedRows.value.some((x) => x.id === row.id);
  tableRef.value.toggleRowSelection(row, !exists);
}

function onRowClick(row) {
  if (longPressHandled.value) {
    longPressHandled.value = false;
    return;
  }
  toggleRowSelected(row);
}

function onRowMouseDown(row) {
  longPressHandled.value = false;
  if (longPressTimer.value) clearTimeout(longPressTimer.value);
  longPressTimer.value = setTimeout(() => {
    toggleRowSelected(row);
    longPressHandled.value = true;
  }, 420);
}

function onRowMouseUp() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value);
    longPressTimer.value = null;
  }
}

function clearSelected() {
  tableRef.value?.clearSelection?.();
}

async function onDeleteSelected() {
  if (selectedRows.value.length === 0) return;
  const names = selectedRows.value.map((x) => x.name).join("、");
  try {
    await ElMessageBox.confirm(
      `确定删除 ${selectedRows.value.length} 名学生？\n${names}`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消"
      }
    );
    for (const row of [...selectedRows.value]) {
      await onDelete(row);
    }
    clearSelected();
  } catch {
    // 用户取消
  }
}

function rowClassName({ row }) {
  return selectedRows.value.some((x) => x.id === row.id) ? "row-selected" : "";
}

function fileFromUploadChange(f) {
  // element-plus 上传 change 事件在不同版本结构略不同，这里做兼容取值
  return f?.raw || f?.file?.raw || f?.file || null;
}

async function onPickFace(row, f, inDetail = false) {
  const file = fileFromUploadChange(f);
  if (!file) return;

  if (inDetail) {
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = URL.createObjectURL(file);
  }

  try {
    busyIds.value.add(row.id);
    uploadPct.value = { ...uploadPct.value, [row.id]: 0 };
    const resp = await uploadStudentFace(row.id, file, (pct) => {
      uploadPct.value = { ...uploadPct.value, [row.id]: pct };
    });
    row.face_path = resp?.face_path || row.face_path;
    if (inDetail) {
      previewUrl.value = resolveFacePreview(row, true);
    }
    ElMessage.success("已上传（待后端处理编码）");
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    busyIds.value.delete(row.id);
    setTimeout(() => {
      const next = { ...uploadPct.value };
      delete next[row.id];
      uploadPct.value = next;
    }, 400);
  }
}

function resolveFacePreview(row, bustCache = false) {
  const p = row?.face_path;
  if (!p) return "";
  if (/^https?:\/\//i.test(p)) return p;
  let normalized = String(p).replace(/\\/g, "/");
  const idx = normalized.indexOf("/face_uploads/");
  if (idx >= 0) normalized = normalized.slice(idx);
  if (!normalized.startsWith("/")) normalized = `/${normalized}`;
  const base = String(api.defaults.baseURL || "").replace(/\/+$/, "");
  const url = `${base}${normalized}`;
  return bustCache ? `${url}?t=${Date.now()}` : url;
}

function isBusy(id) {
  return busyIds.value.has(id);
}

function isUploading(id) {
  return uploadPct.value[id] != null;
}

watch(q, () => {
  page.value = 1;
  load();
});

onMounted(load);
</script>

<style scoped>
.hdr {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}
.left {
  display: grid;
  gap: 2px;
}
.t {
  font-weight: 900;
}
.s {
  font-size: 12px;
  color: var(--app-subtext);
}
.right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.ft {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
.tableActions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.opBtn {
  border-radius: 10px;
  border: 1px solid rgba(20, 20, 20, 0.12);
  background: rgba(255, 255, 255, 0.65);
}
.opBtnPri {
  border: none;
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.92) 0%, rgba(167, 139, 250, 0.86) 55%, rgba(52, 211, 153, 0.9) 110%);
  color: #fff;
}
.opBtnDanger {
  border: none;
  background: linear-gradient(135deg, rgba(251, 113, 133, 0.95) 0%, rgba(248, 113, 113, 0.88) 55%, rgba(251, 146, 60, 0.92) 120%);
  color: #fff;
}

.btnGrad {
  border: none;
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}
.btnSoft {
  border: 1px solid rgba(20, 20, 20, 0.12);
  background: rgba(255, 255, 255, 0.65);
}
.preview {
  display: grid;
  gap: 10px;
}
.pTitle {
  font-weight: 800;
}
.pBox {
  min-height: 260px;
  border-radius: 12px;
  border: 1px dashed rgba(20, 20, 20, 0.18);
  background: rgba(255, 255, 255, 0.55);
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}
.previewImage {
  max-width: 100%;
  max-height: 420px;
  width: auto;
  height: auto;
}
.pAct {
  display: flex;
  gap: 10px;
}

:deep(.el-table .row-selected > td) {
  background: rgba(122, 167, 255, 0.18) !important;
}

:deep(.el-table .cell) {
  padding-left: 6px;
  padding-right: 6px;
}
</style>

