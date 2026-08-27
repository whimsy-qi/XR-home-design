<template>
  <section class="hero-section">
     <div class="hero-icon-container">
      <img src="https://img.icons8.com/fluency/96/sofa.png" alt="home icon" class="hero-icon">
    </div>
    <h1> Vision 智能家装专家</h1>
    <p class="subtitle">您的专属AI室内设计师，将您的灵感变为现实。</p>
    
    <form class="chat-input-container" @submit.prevent="startChat">
      <input 
        v-model="chatMessage"
        type="text" 
        placeholder="有什么家装问题问我，也可以从下方的功能模块开始探索..."
        :disabled="isSending"
      >
      <button type="submit" class="send-btn" :disabled="isSending" title="发送">
        <div v-if="isSending" class="spinner"></div>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13H2l3.5-6.5L2 2l20 0Z"/><path d="M22 2 13 22l-2-7-7-2 18-11Z"/></svg>
      </button>
    </form>
  </section>

  <section class="function-grid">
    <router-link to="/tools/plan-generator" class="function-card-link">
      <div class="function-card">
        <div class="card-icon" style="background-color: rgba(255, 213, 79, 0.2);">💡</div>
        <h4>智能方案生成</h4>
        <p>通过填写表单，AI为您量身定制一份专业的文字设计方案。</p>
      </div>
    </router-link>
    <router-link to="/tools/image-generator" class="function-card-link">
      <div class="function-card">
        <div class="card-icon" style="background-color: rgba(255, 167, 38, 0.2);">🖼️</div>
        <h4>AI效果图创作</h4>
        <p>用简单的文字描述，快速生成媲美真实照片的家装效果图。</p>
      </div>
    </router-link>
    <router-link to="/tools/model-generator" class="function-card-link">
      <div class="function-card">
        <div class="card-icon" style="background-color: rgba(255, 184, 77, 0.2);">🧊</div>
        <h4>AI生成3D模型</h4>
        <p>输入文字或上传图片，快速生成可用于VR/MR的3D模型资产。</p>
      </div>
    </router-link>
  </section>

  <!-- <section class="featured-cases">
    <h3>精选家装案例</h3>
    <div class="cases-grid">
      <div class="case-card">
         <img src="https://i.pinimg.com/1200x/bf/30/e1/bf30e1d552aa348cd5724c26f25cf77e.jpg" alt="现代简约客厅">
         <p>现代简约客厅</p>
      </div>
      <div class="case-card">
        <img src="https://i.pinimg.com/736x/4a/18/d8/4a18d89b437d65b75c66606194d4ff10.jpg" alt="舒适北欧风卧室">
        <p>舒适北欧风卧室</p>
      </div>
       <div class="case-card">
        <img src="https://i.pinimg.com/1200x/79/e8/e9/79e8e95aa7aa01f80125a8c69b1e0ee7.jpg" alt="日式侘寂风客厅">
        <p>日式侘寂风客厅</p>
      </div>
    </div>
  </section> -->
  <HomePage></HomePage>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useChatStore } from '@/stores/chat';
import HomePage from '@/components/vue2/HomePage.vue'; 
const chatMessage = ref(''); 
const isSending = ref(false); 
const router = useRouter();
const chatStore = useChatStore();

const startChat = async () => {
  if (!chatMessage.value.trim() || isSending.value) return;
  isSending.value = true;
  try {
    chatStore.startNewChat();
    await chatStore.sendMessage(chatMessage.value);
    const newSessionId = chatStore.activeSession.id;
    if (newSessionId) {
      router.push(`/chat/${newSessionId}`);
    } else {
      throw new Error('未能获取到新的会话ID');
    }
  } catch (error) {
    console.error("发起新对话失败:", error);
    alert("发起对话失败，请稍后再试。");
  } finally {
    isSending.value = false;
    chatMessage.value = '';
  }
};
</script>

<style scoped>
.hero-section { text-align: center; margin-bottom: 4rem; }
.hero-icon-container { width: 80px; height: 80px; margin: 0 auto 1.5rem; background-color: #fff; border-radius: 24px; display: grid; place-items: center; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
.hero-icon { width: 50px; height: 50px; }
.hero-section h1 { font-size: 2.2rem; margin-bottom: 0.5rem; }
.hero-section .subtitle { font-size: 1rem; color: #757575; margin-top: 0; margin-bottom: 2rem; }
.chat-input-container { max-width: 600px; margin: 0 auto; position: relative; }
.chat-input-container input { width: 100%; padding: 1.1rem 3.5rem 1.1rem 1.5rem; border-radius: 2rem; border: 1px solid #E0E0E0; font-size: 1rem; box-sizing: border-box; }
.chat-input-container .send-btn { 
    position: absolute; 
    right: 8px; 
    top: 50%; 
    transform: translateY(-50%); 
    width: 40px; 
    height: 40px; 
    border-radius: 50%; 
    border: none; 
    background-color: #FFA726; 
    color: white; 
    cursor: pointer; 
    display: grid;
    place-items: center;
    transition: all 0.2s;
}
.send-btn:hover:not(:disabled) { background-color: #FB8C00; }
.send-btn .spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.function-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
  /* 【核心修改】确保卡片顶部对齐，而不是默认的拉伸对齐 */
  align-items: start;
}
.function-card-link { 
  text-decoration: none; 
  color: inherit; 
  display: flex; 
  /* 【核心修改】让链接本身（作为flex项）可以被拉伸 */
  align-self: stretch; 
}
.function-card {
  background-color: #FFFFFF;
  padding: 1.5rem; /* 稍微增加内边距，让内容更舒展 */
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s;
  height: 100%; /* 确保卡片撑满链接的高度 */
  box-sizing: border-box;
  display: flex; /* 【核心修改】使用flex布局让卡片内部元素可以灵活排列 */
  flex-direction: column; /* 垂直排列 */
}
.function-card p {
  flex-grow: 1; /* 【核心修改】让描述文本占据所有剩余空间，从而将不同卡片的高度推到一致 */
}

.function-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
.card-icon { width: 48px; height: 48px; border-radius: 10px; display: grid; place-items: center; font-size: 1.8rem; margin-bottom: 1rem; }
.function-card h4 { margin: 0 0 0.5rem 0; color: #333; }
.function-card p { font-size: 0.9rem; color: #757575; line-height: 1.6; margin: 0; }

.featured-cases { margin-bottom: 4rem;}
.featured-cases h3 { text-align: left; font-size: 1.5rem; color: #333; margin-bottom: 1.5rem; }
.cases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 2rem;
}

.case-card { cursor: pointer; }
.case-card img { width: 100%; height: 220px; object-fit: cover; border-radius: 12px; transition: box-shadow 0.3s; }
.case-card:hover img { box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
.case-card p { font-weight: 500; margin-top: 0.8rem; text-align: center; color: #333; }

</style>