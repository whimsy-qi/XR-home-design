// src/main.js
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth' // 【新增】导入auth store

const app = createApp(App)
const pinia = createPinia() // 【修改】先创建pinia实例

app.use(pinia) // 使用pinia

// 【新增】在挂载应用前，先初始化认证状态
const authStore = useAuthStore()
authStore.initializeAuth()

app.use(router)
app.mount('#app')