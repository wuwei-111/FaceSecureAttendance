<template>
  <el-card class="glass">
    <template #header>
      <div class="hdr">
        <div class="left">
          <div class="t">学生人脸库管理</div>
          <div class="s">管理学生信息与人脸照片。</div>
        </div>
        <div class="right">
          <div class="searchShell">
            <el-input
              v-model="q"
              clearable
              class="searchInput"
              placeholder="搜索：学号 / 姓名 / 班级"
              @keyup.enter="load"
            />
          </div>
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
          <el-button class="btnSoft" @click="openCsvImport">
            <el-icon><Upload /></el-icon>
            CSV 导入
          </el-button>
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

      <div class="tableActions" data-feature="students-actions">
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

      <div class="studentGrid" data-feature="students-table">
        <div
          v-for="row in items"
          :key="row.id"
          class="studentItem"
          :class="{ selected: isSelected(row.id) }"
          @click="toggleSelected(row)"
          @dblclick.stop="openDetail(row)"
        >
          <div class="studentHead">
            <el-checkbox :model-value="isSelected(row.id)" @change="() => toggleSelected(row)" @click.stop />
            <el-tag v-if="row.face_path" type="success" effect="light">已上传</el-tag>
            <el-tag v-else type="info" effect="light">未上传</el-tag>
          </div>
          <div class="studentMeta">
            <div><span class="mk">学号</span><span>{{ row.student_id || "-" }}</span></div>
            <div><span class="mk">姓名</span><span>{{ row.name || "-" }}</span></div>
            <div><span class="mk">班级</span><span>{{ row.class_name || "-" }}</span></div>
          </div>
          <div class="studentOps">
            <el-button class="opBtn" size="small" :disabled="isBusy(row.id)" @click.stop="openDetail(row)">详情</el-button>
            <el-button class="opBtn opBtnPri" size="small" :disabled="isBusy(row.id)" @click.stop="openUploadForRow(row)">
              上传人脸
            </el-button>
          </div>
        </div>
      </div>

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

  <el-dialog v-model="csvOpen" title="CSV 批量导入" width="560px">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="文件格式：学号,姓名,班级（首行可为表头）"
      style="margin-bottom: 10px"
    />
    <el-segmented v-model="csvInputMode" :options="csvModeOptions" style="margin-bottom: 10px" />

    <template v-if="csvInputMode === 'file'">
      <el-upload
        drag
        :show-file-list="false"
        :auto-upload="false"
        accept=".csv,text/csv"
        @change="onCsvPicked"
      >
        <div>拖拽或点击上传 CSV</div>
      </el-upload>
      <div class="csvMeta" v-if="csvFile">
        <span>{{ csvFile.name }}</span>
        <span>{{ csvUploadPct }}%</span>
      </div>
    </template>

    <template v-else>
      <el-input
        v-model="csvText"
        type="textarea"
        :rows="8"
        placeholder="可直接粘贴：学号,姓名,班级（支持首行表头）"
      />
    </template>

    <el-progress v-if="csvUploading || csvUploadPct > 0" :percentage="csvUploadPct" :stroke-width="8" />
    <div v-if="csvStats" class="csvStats">
      <el-tag type="success" effect="light">成功 {{ csvStats.success }}</el-tag>
      <el-tag type="info" effect="light">跳过 {{ csvStats.skipped }}</el-tag>
      <el-tag type="danger" effect="light">失败 {{ csvStats.failed }}</el-tag>
    </div>
    <el-input
      v-if="csvFeedback"
      v-model="csvFeedback"
      type="textarea"
      :rows="6"
      readonly
      style="margin-top: 10px"
    />
    <template #footer>
      <el-button @click="downloadCsvTemplate">下载模板</el-button>
      <el-button @click="csvOpen = false">关闭</el-button>
      <el-button class="btnGrad" type="primary" :disabled="submitDisabled" :loading="csvUploading" @click="submitCsvImport">
        开始导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Refresh, Upload } from "@element-plus/icons-vue";
import {
  createStudent,
  batchImportStudentsCsv,
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
const offlineTip = ref(false);

const q = ref("");
const page = ref(1);
const pageSize = 10;
const total = ref(0);

const createOpen = ref(false);
const editOpen = ref(false);
const detailOpen = ref(false);
const csvOpen = ref(false);
const csvInputMode = ref("file");
const csvModeOptions = [
  { label: "选择文件", value: "file" },
  { label: "复制粘贴", value: "paste" }
];
const csvFile = ref(null);
const csvText = ref("");
const csvUploadPct = ref(0);
const csvUploading = ref(false);
const csvFeedback = ref("");
const csvStats = ref(null);
const current = ref(null);
const previewUrl = ref("");
const createFormRef = ref(null);
const editFormRef = ref(null);
const selectedRows = ref([]);
const selectedIds = ref(new Set());

const uploadPct = ref({});
const busyIds = ref(new Set());
const submitDisabled = computed(() => {
  if (csvInputMode.value === "file") return !csvFile.value;
  return !csvText.value.trim();
});

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

function openCsvImport() {
  csvOpen.value = true;
  csvInputMode.value = "file";
  csvFile.value = null;
  csvText.value = "";
  csvFeedback.value = "";
  csvUploadPct.value = 0;
  csvStats.value = null;
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

function openDetail(row) {
  if (!row) return;
  current.value = row;
  previewUrl.value = resolveFacePreview(row, true);
  detailOpen.value = true;
}

function onCsvPicked(fileInfo) {
  const file = fileInfo?.raw || fileInfo?.file?.raw || fileInfo?.file;
  if (!file) return;
  csvFile.value = file;
  csvUploadPct.value = 0;
  csvFeedback.value = `已选择文件：${file.name}`;
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

function openUploadForSelected() {
  if (!selectedPrimary.value) return;
  current.value = selectedPrimary.value;
  detailOpen.value = true;
}

const selectedPrimary = computed(() => selectedRows.value[0] || null);

function syncSelectedRows() {
  selectedRows.value = items.value.filter((x) => selectedIds.value.has(x.id));
}

function toggleSelected(row) {
  if (!row?.id) return;
  const next = new Set(selectedIds.value);
  if (next.has(row.id)) next.delete(row.id);
  else next.add(row.id);
  selectedIds.value = next;
  syncSelectedRows();
}

function isSelected(id) {
  return selectedIds.value.has(id);
}

function clearSelected() {
  selectedIds.value = new Set();
  selectedRows.value = [];
}

function openUploadForRow(row) {
  if (!row) return;
  current.value = row;
  detailOpen.value = true;
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

function parseCsvLines(text) {
  return String(text || "")
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean);
}

function toStudentFromCsvLine(line) {
  const parts = line.split(/[，,]/).map((x) => x.trim());
  if (parts.length < 2) return null;
  const [student_id, name, class_name = ""] = parts;
  if (!student_id || !name) return null;
  return { student_id, name, class_name };
}

function downloadCsvTemplate() {
  const content = ["学号,姓名,班级", "20230001,张三,计科1班", "20230002,李四,计科1班"].join("\n");
  const blob = new Blob([`\uFEFF${content}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "students_template.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function submitCsvImport() {
  if (csvInputMode.value === "file" && !csvFile.value) return;
  if (csvInputMode.value === "paste" && !csvText.value.trim()) return;
  csvUploading.value = true;
  csvUploadPct.value = 0;
  csvFeedback.value = "";
  csvStats.value = null;
  try {
    if (csvInputMode.value === "file") {
      const data = await batchImportStudentsCsv(csvFile.value, (pct) => {
        csvUploadPct.value = pct;
      });
      csvUploadPct.value = 100;
      csvStats.value = { success: 0, skipped: 0, failed: 0 };
      csvFeedback.value = `后端导入成功：${JSON.stringify(data, null, 2)}`;
      await load();
      ElMessage.success("CSV 导入完成");
      return;
    }
    throw new Error("paste_mode_local_parse");
  } catch (e) {
    // 后端未实现时，本地解析演示
    try {
      const text = csvInputMode.value === "paste" ? csvText.value : await csvFile.value.text();
      const lines = parseCsvLines(text);
      const body = lines[0]?.includes("学号") ? lines.slice(1) : lines;
      let inserted = 0;
      let skipped = 0;
      let failed = 0;
      for (const rawLine of body) {
        const row = toStudentFromCsvLine(rawLine);
        if (!row) {
          failed += 1;
          continue;
        }
        const exists = items.value.some((x) => x.student_id === row.student_id);
        if (exists) {
          skipped += 1;
          continue;
        }
        const nextId = Math.max(0, ...items.value.map((x) => x.id || 0)) + 1 + inserted;
        items.value.unshift({ id: nextId, face_path: "", ...row });
        inserted += 1;
      }
      total.value += inserted;
      offlineTip.value = true;
      csvUploadPct.value = 100;
      csvStats.value = { success: inserted, skipped, failed };
      csvFeedback.value = `后端未接入，本地导入完成：成功 ${inserted}，跳过 ${skipped}，失败 ${failed}（刷新会丢失）。`;
      ElMessage.warning(csvInputMode.value === "paste" ? "已按粘贴内容本地导入演示数据" : getErrorMessage(e) || "已本地导入演示数据");
    } catch (parseErr) {
      csvFeedback.value = `导入失败：${getErrorMessage(parseErr)}`;
      ElMessage.error(getErrorMessage(parseErr));
    }
  } finally {
    csvUploading.value = false;
  }
}

watch(q, () => {
  page.value = 1;
  load();
});
watch(items, syncSelectedRows);

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
.searchShell {
  width: 260px;
  padding: 5px 8px;
  border-radius: 12px;
  border: 1px solid rgba(20, 20, 20, 0.08);
  background: linear-gradient(135deg, rgba(122, 167, 255, 0.1) 0%, rgba(167, 139, 250, 0.08) 45%, rgba(52, 211, 153, 0.08) 100%);
}
.searchInput :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.26) inset;
}
.searchInput :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.5) inset;
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
.studentGrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.studentItem {
  border-radius: 12px;
  padding: 10px;
  border: 1px solid rgba(20, 20, 20, 0.1);
  background: rgba(255, 255, 255, 0.65);
  display: grid;
  gap: 10px;
  transition: box-shadow 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}
.studentItem:hover {
  transform: translateY(-1px);
  border-color: rgba(122, 167, 255, 0.32);
  box-shadow: 0 8px 20px rgba(44, 62, 80, 0.08);
}
.studentItem.selected {
  border-color: rgba(122, 167, 255, 0.45);
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.24) inset;
}
.studentHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.studentMeta {
  display: grid;
  gap: 6px;
}
.studentMeta > div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}
.mk {
  color: var(--app-subtext);
  font-size: 12px;
}
.studentOps {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
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
.csvMeta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--app-subtext);
}
.csvStats {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

@media (max-width: 1400px) {
  .studentGrid {
    grid-template-columns: 1fr;
  }
}
</style>

