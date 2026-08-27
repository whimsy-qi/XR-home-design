<template>
  <div class="plan-generator-page">
    <div class="content-wrapper">
      <header class="page-header">
        <router-link to="/dashboard" class="back-link">← 返回主页</router-link>
        <h1>智能方案生成</h1>
        <p>请填写您的详细需求，Vision AI 将为您量身定制一份专业的设计方案。</p>
      </header>

      <form v-if="planStore.taskStatus === 'idle'" @submit.prevent="submitForm" class="plan-form">
        <div class="form-grid">
            <div class="form-group">
              <label for="room_type">房间类型</label>
              <select id="room_type" v-model="formData.room_type" required>
                <option disabled value="">请选择</option>
                <option>客厅</option><option>卧室</option><option>书房</option><option>厨房</option><option>卫生间</option><option>阳台</option>
              </select>
            </div>
            <div class="form-group">
              <label for="style">装修风格</label>
              <input type="text" id="style" v-model="formData.style" placeholder="例如: 现代简约、奶油风..." required>
            </div>
            <div class="form-group">
              <label for="area_size">房间面积 (㎡)</label>
              <input type="number" id="area_size" v-model="formData.area_size" placeholder="例如: 25" required>
            </div>
            <div class="form-group">
              <label for="budget">装修预算 (万元)</label>
              <input type="text" id="budget" v-model="formData.budget" placeholder="例如: 5-8" required>
            </div>
            <div class="form-group full-width">
              <label for="color_tone">偏好色调</label>
              <input type="text" id="color_tone" v-model="formData.color_tone" placeholder="例如: 原木色、白色为主" required>
            </div>
            <div class="form-group full-width">
              <label for="special_needs">其他特殊需求</label>
              <textarea id="special_needs" v-model="formData.special_needs" placeholder="例如: 需要一个独立的阅读角，家有宠物..."></textarea>
            </div>
        </div>
        <button type="submit" class="submit-btn">开始生成</button>
      </form>

      <div v-if="planStore.taskStatus === 'loading'" class="loading-view">
         <div class="loader"></div>
         <p>AI正在为您挥洒创意，请稍候...</p>
         <div class="progress-bar">
           <div class="progress-bar-inner" :style="{ width: planStore.progress + '%' }"></div>
         </div>
         <p class="progress-text">{{ planStore.progress }}%</p>
      </div>

      <div v-if="planStore.taskStatus === 'success' && planStore.planResult" class="result-view">
        <PlanDisplay :plan="planStore.planResult" />
        <button @click="planStore.reset()" class="submit-btn again-btn">再生成一个</button>
      </div>

      <div v-if="planStore.taskStatus === 'error'" class="error-view">
          <p class="error-icon">😕</p>
          <p>糟糕，出错了！</p>
          <p class="error-message">{{ planStore.error }}</p>
          <button @click="planStore.reset()" class="submit-btn">重试</button>
      </div>

    </div>
  </div>
</template>

<script setup>
// script 部分保持不变
import { ref, onUnmounted } from 'vue';
import PlanDisplay from '@/components/PlanDisplay.vue';
import { usePlanStore } from '@/stores/plan';

const planStore = usePlanStore();

const formData = ref({
  room_type: '',
  style: '',
  area_size: '',
  color_tone: '',
  budget: '',
  special_needs: '',
});

const submitForm = () => {
  if (!formData.value.room_type || !formData.value.style || !formData.value.area_size || !formData.value.budget || !formData.value.color_tone) {
      alert('请填写所有必填项！');
      return;
  }
  planStore.generatePlan(formData.value);
};

onUnmounted(() => {
    planStore.reset();
})
</script>

<style scoped>
/* style 部分保持不变 */
.plan-generator-page { background-color: #FFF8E1; min-height: 100vh; padding: 2rem 4rem; box-sizing: border-box; }
.content-wrapper { max-width: 900px; margin: 0 auto; }
.page-header { text-align: center; margin-bottom: 3rem; color: #333; position: relative; }
.back-link { position: absolute; left: 0; top: 50%; transform: translateY(-50%); text-decoration: none; color: #555; font-weight: 500; }
.page-header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
.page-header p { font-size: 1rem; color: #757575; }
.plan-form .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; background-color: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { display: block; margin-bottom: 0.75rem; font-weight: 500; color: #424242; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.9rem 1rem; border: 1px solid #E0E0E0; border-radius: 8px; box-sizing: border-box; font-family: inherit; font-size: 1rem; background-color: #fafafa; transition: border-color 0.2s, box-shadow 0.2s; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: #FFA726; box-shadow: 0 0 0 3px rgba(255, 167, 38, 0.2); }
.form-group textarea { min-height: 120px; resize: vertical; }
.submit-btn { display: block; width: 220px; margin: 2rem auto 0; padding: 1rem; border: none; border-radius: 8px; background-color: #FFA726; color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.submit-btn:hover { background-color: #FB8C00; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(251, 140, 0, 0.3); }
.loading-view, .error-view { text-align: center; padding: 4rem 0; background-color: #fff; border-radius: 12px; }
.loader { border: 4px solid #f3f3f3; border-top: 4px solid #FFA726; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 1.5rem; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.progress-bar { width: 80%; max-width: 400px; height: 8px; background-color: #eee; border-radius: 4px; margin: 1rem auto; overflow: hidden; }
.progress-bar-inner { height: 100%; background-color: #FFA726; border-radius: 4px; transition: width 0.3s ease-in-out; }
.progress-text { font-size: 0.9rem; color: #757575; }
.error-icon { font-size: 3rem; margin-bottom: 1rem; }
.error-message { color: #D32F2F; background-color: #ffebee; padding: 1rem; border-radius: 8px; display: inline-block; max-width: 80%; margin-bottom: 2rem; }
.result-view { animation: fadeIn 0.5s ease-in-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.again-btn { margin-top: 2rem; }
</style>