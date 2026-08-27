<template>
  <div class="container">
    <!-- 顶部导航栏 -->
    <div class="nav-bar">
      <ul class="nav-left">
                <!-- 添加返回首页箭头 -->
        <li class="home-arrow" @click="goToHome">

           <span class="arrow">&#171;</span> <!-- ⬅（向左） -->

        </li>
        <li @click="goToAllFurniture">所有家具</li>
        <li @click="goToMyFurniture">我的家具</li>
        <li @click="goToUploadFurniture">上传家具</li>
      </ul>
      <ul class="nav-right">
        <input type="text" placeholder="搜索">
      </ul>
    </div>

    <!-- 大幅宣传海报区域 -->
    <div class="banner">
      <img src="@/assets/1.png" alt="家具海报">
      <div class="banner-text">
        <p class="date">5.21-6.21 Minotti公司设计</p>
        <p class="title">焕新夏日 质感上线</p>
        <p class="main-hall-text">前往主会场</p>
      </div>
    </div>

    <!-- 近期推荐区域 -->
    <div class="recommendation">
      <h2>近期推荐</h2>
      <div class="recommendation-item">
        <img src="@/assets/2.png" alt="推荐1">
        <div class="item-text">
          <p class="name">当季新品</p>
          <p class="desc">STOCKHOLM斯德哥尔摩2025，向斯堪的纳维亚设计致敬</p>
        </div>
      </div>
      <div class="recommendation-item">
        <img src="@/assets/3.png" alt="推荐2">
        <div class="item-text">
          <p class="name">会员限时特购</p>
          <p class="desc">2025.5.21 - 2025.6.21数量有限，售完为止</p>
        </div>
      </div>
      <div class="recommendation-item">
        <img src="@/assets/4.png" alt="推荐3">
        <div class="item-text">
          <p class="name">更低价格，更多值得</p>
          <p class="desc">用更低的价格，打造更美好的日常生活</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PersonRoom',
  methods: {
    goToAllFurniture() {
      this.$router.push('/all-furniture');
    },
    goToMyFurniture() {
      this.$router.push('/my-furniture');
    },
    goToUploadFurniture() {
      this.$router.push('/upload-furniture');
    },
      // 添加返回首页方法
    goToHome() {

      this.$router.push({ name: 'Home' });
    }
  }
}
</script>

<style scoped>
body {
  margin: 0;
  padding: 0;
  overflow-y: scroll;
}
.container {
  width: 100%;
  font-family: Arial, sans-serif;
}
/* 顶部导航栏样式 */
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 35px 60px;
  background-color: white;
}
.nav-left,
.nav-right {
  list-style-type: none;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
}
.nav-left li,
.nav-right li {
  margin-right: 35px;
  cursor: pointer;
  font-size: 22px;
  font-weight: bold; /* 增加字体粗细 */

}
.nav-right input {
  padding: 12px 15px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 22px;
  width: 220px;
  height: 22px;
  line-height: 22px;
  vertical-align: middle; /* 确保输入框垂直居中 */
}
/* 添加的返回箭头样式 */
.home-arrow {
  margin-right: 30px; /* 控制箭头与菜单的间距 */
  cursor: pointer;
  
}
.arrow {
  font-size: 35px;
  font-weight: bold;
  color: #333;
  
}

/* 大幅宣传海报区域样式 */
.banner {
  position: relative;
  height: 500px;
}
.banner img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.banner-text {
  position: absolute;
  left: 40px;
  top: 50%;
  transform: translateY(-50%);
  color: white;
}
.banner-text .date {
  font-size: 36px;
  margin-bottom: 15px;
}
.banner-text .title {
  font-size: 56px;
  margin-bottom: 25px;
}
.main-hall-text {
  font-size: 32px;
  color: white;
  cursor: pointer;
}
/* 近期推荐区域样式 */
.recommendation {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-around;
  padding: 20px;
}
.recommendation h2 {
  width: 100%;
  text-align: center;
  margin-bottom: 20px;
}
.recommendation-item {
  width: calc(25% - 20px);
  margin-bottom: 30px;
  background-color: #f2f2f2; 
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
  padding: 10px;
}
.recommendation-item img {
  width: 100%;
  height: auto;
  margin-bottom: 10px;
}
.item-text {
  text-align: center;
  background-color: #f2f2f2;
  padding: 10px;
  border-radius: 5px; 
}
.name {
  font-size: 16px;
  margin-bottom: 5px;
}
.desc {
  font-size: 14px;
  color: #666;
}
</style>
