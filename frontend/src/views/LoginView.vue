<template>
  <div class="loginPage">
    <el-card class="loginCard glass">
      <div class="title">登录</div>
      <div class="sub">请输入账号与密码</div>

      <el-form ref="formRef" class="loginForm" label-position="top" :model="form" :rules="rules">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            show-password
            type="password"
            placeholder="请输入密码"
            @keyup.enter="onLogin"
          />
        </el-form-item>
      </el-form>

      <el-alert
        title="测试账号：admin、teacher1、teacher2、student1、student2；统一密码 123456"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      />

      <div class="actions">
        <el-button @click="clearToken">清除本地 token</el-button>
        <el-button class="btnGrad" type="primary" :loading="loading" @click="onLogin">
          登录
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute } from "vue-router";
import { login } from "../api/auth";
import { getErrorMessage } from "../api/client";

const route = useRoute();
const formRef = ref(null);
const loading = ref(false);
const form = ref({
  username: "",
  password: ""
});
const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }]
};
const nextPath = computed(() => route.query.next || "/");

async function onLogin() {
  const ok = await formRef.value?.validate?.().catch(() => false);
  if (!ok) return;
  loading.value = true;
  try {
    const data = await login(form.value.username.trim(), form.value.password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user_info", JSON.stringify({ username: data.username, role: data.role }));
    window.location.assign(String(nextPath.value || "/"));
  } catch (e) {
    ElMessage.error(getErrorMessage(e));
  } finally {
    loading.value = false;
  }
}

function clearToken() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_info");
  form.value.password = "";
}
</script>

<style scoped>
.loginPage {
  min-height: 100vh;
  display: grid;
  place-items: center;
}
.loginCard {
  width: min(520px, 92vw);
}
.title {
  font-size: 22px;
  font-weight: 800;
}
.sub {
  margin-top: 4px;
  margin-bottom: 14px;
  color: rgba(31, 35, 40, 0.68);
  font-size: 12px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btnGrad {
  border: none;
  background: linear-gradient(135deg, #7aa7ff 0%, #a78bfa 45%, #34d399 100%);
}

.loginForm :deep(.el-input__wrapper) {
  background: rgba(122, 167, 255, 0.12);
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.28) inset;
}

.loginForm :deep(.el-input__wrapper.is-focus) {
  background: rgba(122, 167, 255, 0.16);
  box-shadow: 0 0 0 1px rgba(122, 167, 255, 0.45) inset;
}

.loginForm :deep(.el-input__inner:-webkit-autofill),
.loginForm :deep(.el-input__inner:-webkit-autofill:hover),
.loginForm :deep(.el-input__inner:-webkit-autofill:focus) {
  -webkit-text-fill-color: #1f2328;
  transition: background-color 9999s ease-in-out 0s;
}
</style>

