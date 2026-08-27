<template>
  <div class="dashboard-layout">
    <DashboardSidebar />
    
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// 【核心修正】导入正确的侧边栏组件
import DashboardSidebar from '@/components/DashboardSidebar.vue';
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  background-color: #FFF8E1;
  min-height: 100vh;
}
.main-content {
  flex-grow: 1;
  padding: 3rem 4rem;
  height: 100vh;
  box-sizing: border-box;
}
</style>