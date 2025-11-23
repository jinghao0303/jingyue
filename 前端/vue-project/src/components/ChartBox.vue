<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  options: {
    type: Object,
    required: true,
    default: () => ({})
  }
});

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// 过滤 ECharts 的 alignTicks 警告（雷达图不支持该选项，但警告不影响功能）
const originalWarn = console.warn;
const filteredWarn = (...args: any[]) => {
  const message = args[0]?.toString() || '';
  // 过滤掉 alignTicks 相关的警告
  if (message.includes('alignTicks') || message.includes('indicator_') && message.includes('AxisIndex')) {
    return; // 忽略这个警告
  }
  originalWarn.apply(console, args);
};

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    // 避免重复初始化
    if (echarts.getInstanceByDom(chartRef.value)) return;
    
    chartInstance = echarts.init(chartRef.value);
    chartInstance.setOption(props.options);
    window.addEventListener('resize', resizeChart);
  }
};

// 窗口大小改变时重绘
const resizeChart = () => {
  chartInstance?.resize();
};

// 监听数据变化，动态更新
watch(() => props.options, (newVal) => {
  chartInstance?.setOption(newVal, true); // true 表示不合并，强制更新
}, { deep: true });

onMounted(() => {
  // 在组件挂载时启用警告过滤
  console.warn = filteredWarn;
  
  // 稍微延迟一下确保 DOM 渲染完毕
  setTimeout(initChart, 100);
});

onBeforeUnmount(() => {
  // 恢复原始的 console.warn
  console.warn = originalWarn;
  
  window.removeEventListener('resize', resizeChart);
  chartInstance?.dispose();
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 300px; /* 给个最小高度，防止塌陷 */
}
</style>