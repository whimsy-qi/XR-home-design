// src/api/axios.js

import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

// 创建一个axios实例，并设置基础URL
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 设置请求拦截器，在每次请求前都附上Token
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.accessToken;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 设置响应拦截器，处理401认证失败
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore();
    
    // 如果后端返回401错误，说明Token已失效
    if (error.response && error.response.status === 401) {
      console.log('检测到401未授权错误，执行自动登出...');
      
      // 调用登出动作，清除本地的无效Token
      authStore.logout();
      
      // 使用router强制跳转到登录页面
      // 使用replace可以防止用户通过浏览器“后退”按钮回到之前的页面
      await router.replace('/home'); 
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;