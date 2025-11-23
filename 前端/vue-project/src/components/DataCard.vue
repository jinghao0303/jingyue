<template>
  <el-card shadow="hover" class="data-card" :style="{ borderLeft: `5px solid ${color}` }">
    <div class="card-content">
      <el-icon :size="30" :color="color" class="card-icon"><component :is="icon" /></el-icon>
      <div class="card-details">
        <div class="card-title">{{ title }}</div>
        <div class="card-value-wrapper">
          <span class="card-value">{{ value }}</span>
          <span class="card-unit">{{ unit }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  color: {
    type: String,
    default: '#409EFF'
  },
  icon: {
    type: String,
    required: true
  },
  unit: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.data-card {
  height: 120px;
  border-radius: 8px;
  transition: transform 0.3s;
}

.data-card:hover {
  transform: translateY(-5px);
}

.card-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.card-icon {
  margin-right: 15px;
  padding: 10px;
  border-radius: 50%;
  background-color: rgba(64, 158, 255, 0.1); /* 默认淡蓝色背景 */
}

.card-details {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value-wrapper {
  display: flex;
  align-items: baseline;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  color: #303133;
  margin-right: 5px;
}

.card-unit {
  font-size: 16px;
  color: #606266;
  font-weight: 500;
}
</style>