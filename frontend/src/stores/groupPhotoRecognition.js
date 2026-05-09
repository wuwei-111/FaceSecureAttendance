/**
 * 合照识别会话状态：路由切换不销毁，刷新页面才清空内存。
 * 识别请求在后台继续，回到页面仍能看到进度或结果。
 */
import { reactive } from "vue";
import { recognizeGroupPhoto } from "../api/photo";
import { getErrorMessage } from "../api/client";

export const groupPhotoRecognition = reactive({
  activityName: "",
  result: null,
  err: "",
  loading: false,
  uploadPct: 0,
  /** @type {File | null} */
  pickedFile: null,
  previewUrl: ""
});

/** 重置或重新选图时递增，丢弃已过期的识别 Promise 回写 */
let submitGeneration = 0;

function revokePreviewUrl() {
  if (groupPhotoRecognition.previewUrl?.startsWith("blob:")) {
    URL.revokeObjectURL(groupPhotoRecognition.previewUrl);
  }
  groupPhotoRecognition.previewUrl = "";
}

export function groupPhotoPickFile(file) {
  if (!file) return;
  groupPhotoRecognition.err = "";
  const mime = (file.type || "").toLowerCase();
  if (mime && !mime.startsWith("image/")) {
    groupPhotoRecognition.err = "请选择图片文件（JPG、PNG 等）";
    return;
  }
  if (Number(file.size || 0) <= 0) {
    groupPhotoRecognition.err = "文件为空或无法读取，请重新选择";
    return;
  }
  revokePreviewUrl();
  submitGeneration += 1;
  groupPhotoRecognition.pickedFile = file;
  groupPhotoRecognition.result = null;
  groupPhotoRecognition.err = "";
  groupPhotoRecognition.previewUrl = URL.createObjectURL(file);
}

export async function groupPhotoSubmit() {
  const file = groupPhotoRecognition.pickedFile;
  if (!file) return;

  const gen = ++submitGeneration;
  groupPhotoRecognition.err = "";
  groupPhotoRecognition.result = null;
  groupPhotoRecognition.uploadPct = 0;
  groupPhotoRecognition.loading = true;

  try {
    const data = await recognizeGroupPhoto(file, {
      activityName: groupPhotoRecognition.activityName,
      onProgress: (pct) => {
        if (gen === submitGeneration) {
          groupPhotoRecognition.uploadPct = pct;
        }
      }
    });
    if (gen !== submitGeneration) return;
    groupPhotoRecognition.result = data;
    groupPhotoRecognition.uploadPct = 100;
  } catch (ex) {
    if (gen !== submitGeneration) return;
    groupPhotoRecognition.err = getErrorMessage(ex);
    groupPhotoRecognition.uploadPct = 0;
  } finally {
    if (gen === submitGeneration) {
      groupPhotoRecognition.loading = false;
    }
  }
}

/** 仅移除当前选择的图片预览（与原版「×」一致） */
export function groupPhotoClearPickedImage() {
  revokePreviewUrl();
  groupPhotoRecognition.pickedFile = null;
}

/** 重置识别结果与上传区；保留活动名称 */
export function groupPhotoResetAll() {
  submitGeneration += 1;
  groupPhotoRecognition.result = null;
  groupPhotoRecognition.err = "";
  groupPhotoRecognition.uploadPct = 0;
  groupPhotoRecognition.loading = false;
  revokePreviewUrl();
  groupPhotoRecognition.pickedFile = null;
}

/** 退出登录时调用，避免账号切换看到他人缓存 */
export function resetGroupPhotoRecognitionStore() {
  submitGeneration += 1;
  groupPhotoRecognition.activityName = "";
  groupPhotoRecognition.result = null;
  groupPhotoRecognition.err = "";
  groupPhotoRecognition.uploadPct = 0;
  groupPhotoRecognition.loading = false;
  revokePreviewUrl();
  groupPhotoRecognition.pickedFile = null;
}
