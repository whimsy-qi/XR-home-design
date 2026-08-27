<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Vision AI</h1>
      <p class="subtitle">智能家装设计辅助平台</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <input v-model="username" id="username" type="text" placeholder="请输入用户名">
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input v-model="password" id="password" type="password" placeholder="请输入密码">
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="button" :disabled="isLoading">
          {{ isLoading ? '正在登录...' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const username = ref('test2');
const password = ref('1234');
const error = ref('');
const isLoading = ref(false);
const router = useRouter(); // 在组件 setup 中获取 router 实例是正确的
const authStore = useAuthStore();

const handleLogin = async () => {
  error.value = '';
  isLoading.value = true;
  try {
    await authStore.login({
      username: username.value,
      password: password.value
    });
    
    // 【核心修正】登录成功后（即上一行代码没有抛出错误），在这里执行跳转
    router.push('/'); 

  } catch (err) {
    error.value = authStore.error || '登录时发生未知错误';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
  /* 样式保持不变 */
  .login-page { display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #FFF8E1; }
  .login-card { width: 100%; max-width: 400px; padding: 3rem; background: #FFFFFF; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; }
  h1 { color: #333; }
  .subtitle { color: #757575; margin-bottom: 2.5rem; }
  .form-group { margin-bottom: 1.5rem; text-align: left; }
  label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
  input { width: 100%; padding: 0.8rem 1rem; border: 1px solid #E0E0E0; border-radius: 8px; box-sizing: border-box; font-size: 1rem; }
  .button { width: 100%; padding: 1rem; border: none; border-radius: 8px; background-color: #FFA726; color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .button:hover:not(:disabled) { background-color: #FB8C00; }
  .button:disabled { background-color: #E0E0E0; cursor: not-allowed; }
  .error-message { color: #D32F2F; margin-bottom: 1rem; font-size: 0.9rem; }
</style>