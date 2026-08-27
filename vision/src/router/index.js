import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardLayout from '../layouts/DashboardLayout.vue' // 导入主页布局
import Home from '@/components/vue2/Home.vue';
import PersonRoom from '@/components/vue2/PersonRoom.vue'; 
import AllFurniture from '@/components/vue2/AllFurniture.vue';
import MyFurniture from '@/components/vue2/MyFurniture.vue';
import UploadFurniture from '@/components/vue2/UploadFurniture.vue';
import PanoramaViewer from '@/components/vue2/PanoramaViewer.vue';
import HomePage from '@/components/vue2/HomePage.vue'; 
import { ElMessage } from 'element-plus';


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      // 主仪表盘布局作为根路径
      path: '/dashboard',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '', // 空路径表示默认子路由
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
        }
      ]
    },
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      // 这个路径匹配 /chat
      path: '/chat',
      name: 'chat-home',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // 这个路径匹配 /chat/具体id
      path: '/chat/:sessionId',
      name: 'chat-session',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // 所有工具页面也都是独立的顶级路由
      path: '/tools/plan-generator',
      name: 'plan-generator',
      component: () => import('../views/PlanGeneratorView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tools/image-generator',
      name: 'image-generator',
      component: () => import('../views/ImageGeneratorView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tools/model-generator',
      name: 'model-generator',
      component: () => import('../views/ModelGeneratorView.vue'),
      meta: { requiresAuth: true }
    },
   
    {
      path: '/furniture',
      name: 'PersonRoom',
      component: PersonRoom 
    },
    {
      path: '/all-furniture',
      name: 'AllFurniture',
      component: AllFurniture,
    },
    {
      path: '/my-furniture',
      name: 'MyFurniture',
      component: MyFurniture,
    },
      {
      path: '/upload-furniture',
      name: 'UploadFurniture',
      component: UploadFurniture,
    },
     {
      path: '/panorama-viewer',
      name: 'PanoramaViewer',
      component: PanoramaViewer,
    },
    {
      path: '/home-page',
      name: 'HomePage',
      component: HomePage,
    },
  ]
})

// 全局导航守卫 (保持不变)
router.beforeEach((to) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    console.log('没有登录')
    ElMessage.error('没有登录')
    if (!localStorage.getItem('access_token')) {
        return { name: 'Home' };
    }
  }
})

export default router;