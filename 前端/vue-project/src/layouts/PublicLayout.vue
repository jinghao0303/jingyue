<template>
  <div class="mobile-layout">
    <!-- 顶部内容区 (可滚动) -->
    <div class="content-area">
      <router-view v-slot="{ Component }">
        <transition name="slide-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- 底部导航栏 -->
    <div class="bottom-nav">
      <router-link to="/public/home" class="nav-item" active-class="active">
        <el-icon :size="24"><HomeFilled /></el-icon>
        <span>首页</span>
      </router-link>
      <router-link to="/public/map" class="nav-item" active-class="active">
        <el-icon :size="24"><LocationFilled /></el-icon>
        <span>附近</span>
      </router-link>
      <router-link to="/public/guide" class="nav-item" active-class="active">
        <el-icon :size="24"><Reading /></el-icon>
        <span>指南</span>
      </router-link>
      <router-link to="/public/profile" class="nav-item" active-class="active">
        <el-icon :size="24"><User /></el-icon>
        <span>我的</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { HomeFilled, LocationFilled, Reading, User } from '@element-plus/icons-vue';
</script>

<style scoped>
.mobile-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f8fa;
  max-width: 480px; /* 限制最大宽度，模拟手机效果 */
  margin: 0 auto;   /* 居中显示 */
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  position: relative;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 60px; /* 防止被底部栏遮挡 */
}

.bottom-nav {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 55px;
  background: white;
  border-top: 1px solid #ebedf0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: #c8c9cc;
  text-decoration: none;
}

.nav-item.active {
  color: #409EFF; /* 选中颜色 */
}

.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.3s ease; }
.slide-fade-enter-from { transform: translateX(20px); opacity: 0; }
.slide-fade-leave-to { transform: translateX(-20px); opacity: 0; }
</style>