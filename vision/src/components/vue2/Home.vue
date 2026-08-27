<template>
  <div class="home">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <nav class="nav-right">
        <router-link to="/">首页</router-link>
        <a href="#">关于我们</a>
        <router-link to="/home-page">主营业务</router-link>
        <router-link to="/dashboard">智能助手</router-link>
        <router-link to="/furniture">家具库</router-link>
        <a href="#" @click="showLoginModal">登录</a>
      </nav>
    </header>

    <!-- 公司名称标题 -->
    <div class="company-title">立方视觉工坊家装设计有限公司</div>

    <!-- 中间图片部分 -->
    <main class="main-content">
      <video
        :src="videoSrc"
        class="home-video"
        autoplay
        muted
        playsinline
        ref="mainVideo"
      />
    </main>

    <!-- 登录模态框 -->
    <LoginModal ref="loginModal" />
  </div>
</template>

<script>
import LoginModal from "@/components/vue2/LoginModal.vue";
import videoSrc from "@/assets/main.mp4";
export default {
  name: "HomePage",
  components: { LoginModal },
  data() {
    return {
      videoSrc: videoSrc,
    };
  },
  methods: {
    showLoginModal() {
      this.$refs.loginModal.showModal();
    },
  },
  mounted() {
    this.$refs.mainVideo.onended = () => {
      console.log("视频播放完毕");
      // 可以在这里执行后续逻辑，比如显示某个按钮
    };
  },
};
</script>

<style scoped>
/* === 全局锁定 === */
.home-video {
  width: 1248px;
  max-width: 100%;
  height: auto;
  object-fit: contain;
  display: block;
}




.home {
  position: fixed !important;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #fff9e5;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
}

/* === 导航栏 === */
.navbar {
  height: 60px;
  flex-shrink: 0;
  background: white;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 40px;
  border-bottom: 1px solid white;
}

.nav-right a,
.nav-right router-link {
  margin-left: 30px;
  text-decoration: none;
  color: #2b2b2b;
  font-size: 20px;
}

/* === 公司标题 === */
.company-title {
  flex-shrink: 0;
  text-align: right;
  font-size: 50px;
  font-weight: bold;
  padding: 10px 40px 0 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #2b2b2b;   

}

/* === 主内容区 === */
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;  /* 去掉内边距 */
}

.home-image {
  max-height: calc(100vh - 180px); /* 动态计算：视口高度 - 导航和标题高度 */
  max-width: 45%;
  object-fit: contain;
}

/* === 滚动条隐藏 === */
body {
  overflow: hidden !important;
  position: fixed;
  width: 100%;
  height: 100%;
}
</style>