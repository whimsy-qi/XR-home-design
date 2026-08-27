<template>
  <div class="upload-furniture">

    <div class="tab-nav">
          
      <div class="home-arrow" @click="goToHome">
     <span class="arrow">&#171;</span>
     </div>
      <span 
        class="tab-item" 
        :class="{ active: activeTab === 'local' }" 
        @click="activeTab = 'local'">
        本地模型
      </span>
      <span 
        class="tab-item" 
        :class="{ active: activeTab === 'ai' }" 
        @click="activeTab = 'ai'">
        AI建模
      </span>
    </div>

    <!-- 根据 activeTab 动态渲染对应组件 -->
    <component :is="activeComponent" />
  </div>
</template>

<script>
import LocalModel from './LocalModel.vue';
import AIModel from './AIModel.vue';

export default {
  components: {
    LocalModel,
    AIModel
  },
  data() {
    return {
      activeTab: 'local'
    };
  },
  computed: {
    activeComponent() {
      return this.activeTab === 'local' ? LocalModel : AIModel;
    }
  },
 methods: {
    goToHome() {
      this.$router.push({ name: 'PersonRoom' });
    }
  }
};
</script>

<style scoped>
.upload-furniture {
  min-height: 120vh;
  padding: 30px;
  box-sizing: border-box;
  background-color: #fff9e5;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  min-width: 1400px; 
  min-width: 1400px; 
}
.tab-nav {
  display: flex;
  align-items: center;  /* 关键：使所有子项垂直居中 */
  margin-bottom: 20px;
  gap: 20px;  /* 添加项间距 */
}

.home-arrow {
  cursor: pointer;
  display: flex;  /* 使用flex确保箭头垂直居中 */
  align-items: center;
  height: 100%;  /* 确保高度与其他元素一致 */
}

.arrow {
  font-size: 30px;
  font-weight: bold;
  /* 移除line-height，改用flex对齐 */
}

.tab-item {
  padding: 10px 20px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;  /* 添加过渡效果 */
  color: #000;
  font-size: 30px;
  display: flex;  /* 使文字也能垂直居中 */
  align-items: center;
}
.tab-item.active {
  border-bottom-color: #FFA726;
  color: #FFA726;
  
}
.arrow {
  font-size: 30px; /* 调整箭头大小 */
  font-weight: bold; /* 可选：加粗 */
  line-height: 1; /* 确保垂直对齐 */
}
</style>