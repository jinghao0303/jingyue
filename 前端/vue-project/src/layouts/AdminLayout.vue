<template>
  <el-container class="layout-container">
    <!-- 左侧菜单 -->
    <el-aside width="220px" class="aside-menu">
      <div class="logo-box">
        <el-icon :size="24" color="#409EFF"><TrendCharts /></el-icon>
        <span v-if="!isCollapse">IDPS 预测中心</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        :collapse="isCollapse"
        style="border-right: none;" 
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>疫情态势总览</span>
        </el-menu-item>
        <el-menu-item index="/admin/map">
          <el-icon><MapLocation /></el-icon>
          <span>区域风险地图</span>
        </el-menu-item>
        <el-menu-item index="/admin/data">
          <el-icon><Document /></el-icon>
          <span>病例数据管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/simulation">
          <el-icon><Cpu /></el-icon>
          <span>多场景推演</span>
        </el-menu-item>
        <el-menu-item index="/admin/resources">
          <el-icon><FirstAidKit /></el-icon>
          <span>医疗资源监控</span>
        </el-menu-item>
        <el-menu-item index="/admin/model-config">
          <el-icon><Setting /></el-icon>
          <span>模型配置管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/data-monitor">
          <el-icon><DataAnalysis /></el-icon>
          <span>训练数据监控</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主体 (删除了 el-header，直接显示内容) -->
    <el-container>
      <el-main class="layout-main">
        <!-- 路由出口：各个页面会显示在这里 -->
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
// 删除了 ArrowDown 等不需要的图标引入
import { TrendCharts, Odometer, MapLocation, Document, Cpu, FirstAidKit, Setting, DataAnalysis } from '@element-plus/icons-vue';

const route = useRoute();
// 保持菜单高亮逻辑
const activeMenu = computed(() => route.path);
const isCollapse = ref(false);
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
}

.aside-menu {
  background-color: #001529;
  color: white;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}

.logo-box {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 18px;
  gap: 10px;
  background-color: #002140; /*稍微深一点的背景区分Logo区*/
}

/* 修改 main 的样式，去掉内边距限制，让子页面全屏填充 */
.layout-main {
  background-color: #f0f2f5;
  padding: 0; /* 去掉 padding，由子页面自己控制布局 */
  height: 100%;
  overflow-y: auto; /* 内容过多时出现滚动条 */
}

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>