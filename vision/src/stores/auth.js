import { defineStore } from 'pinia';
import apiClient from '@/api/axios';
// 【重要】不再需要从 vue-router 导入任何东西
// import { useRouter } from 'vue-router'; 

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    user: null,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },

  actions: {
    async login(credentials) {
      this.error = null;
      try {
        const response = await apiClient.post('/api/auth/login/', credentials);
        
        const { access, refresh } = response.data;
        this.accessToken = access;
        this.refreshToken = refresh;
        
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        
        // 【核心修正】移除所有与router相关的代码
        // const router = useRouter(); // <-- 移除
        // router.push('/');           // <-- 移除

      } catch (err) {
        this.error = err.response?.data?.detail || '登录失败，请检查用户名或密码。';
        console.error("登录失败:", err);
        this.logout();
        throw err;
      }
    },

    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete apiClient.defaults.headers.common['Authorization'];
    },

    initializeAuth() {
        const token = localStorage.getItem('access_token');
        if (token) {
            this.accessToken = token;
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
    }
  },
});