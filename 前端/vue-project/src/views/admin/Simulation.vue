<template>
  <div>
    <el-alert title="操作提示：您可以同时设置多组参数，对比不同管控措施下的疫情发展趋势。" type="info" show-icon style="margin-bottom: 20px;" />
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card header="场景 A：现状延续 (Baseline)">
          <el-form label-position="top">
            <el-form-item label="R0 值"><el-input v-model="sceneA.r0" disabled /></el-form-item>
            <el-tag type="warning">中风险</el-tag>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card header="场景 B：严格管控 (Lockdown)">
          <el-form label-position="top">
             <el-form-item label="预计 R0 值"><el-slider v-model="sceneB.r0" :min="0.5" :max="3" :step="0.1" /></el-form-item>
             <el-button type="primary" size="small" @click="runCompare">加入推演</el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <div style="height: 450px;">
        <chart-box :options="compareChartOptions" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import ChartBox from '@/components/ChartBox.vue';

const sceneA = reactive({ r0: 2.5 });
const sceneB = reactive({ r0: 0.9 });
const compareChartOptions = ref({});

// 初始化对比图
const runCompare = () => {
  // 这里可以调用 predictAPI 两次，分别传入不同的 R0，然后把两条线画在一个图里
  compareChartOptions.value = {
    title: { text: '不同防控力度下的感染趋势预测' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['场景A(现状)', '场景B(管控)'] },
    xAxis: { type: 'category', data: ['W1', 'W2', 'W3', 'W4', 'W5'] },
    yAxis: { type: 'value' },
    series: [
      { name: '场景A(现状)', type: 'line', data: [100, 250, 600, 1200, 2000], smooth: true, lineStyle: {color: '#F56C6C'} },
      { name: '场景B(管控)', type: 'line', data: [100, 120, 130, 110, 50], smooth: true, lineStyle: {color: '#67C23A'} }
    ]
  };
};
runCompare();
</script>