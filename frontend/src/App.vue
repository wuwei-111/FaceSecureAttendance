<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="title">FaceSecureAttendance</div>
      <el-menu mode="horizontal" :default-active="$route.path" router>
        <el-menu-item index="/">考勤</el-menu-item>
        <el-menu-item index="/photo">合照识别</el-menu-item>
        <el-menu-item index="/emotion">情绪统计</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  font-weight: 700;
  color: #303133;
  min-width: 220px;
}
</style>
