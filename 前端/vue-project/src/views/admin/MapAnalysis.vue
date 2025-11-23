<template>
  <div class="map-analysis">
    <el-card shadow="hover">
      <template #header>
        <div class="flex-between">
          <span>🗺️ 都市疫情热力分布</span>
          <el-radio-group v-model="mapType" size="small">
            <el-radio-button label="confirmed">确诊分布</el-radio-button>
            <el-radio-button label="risk">风险等级</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div style="height: 600px;">
        <!-- 复用你的 ChartBox 组件 -->
        <chart-box :options="mapOptions" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import ChartBox from '@/components/ChartBox.vue';

const mapType = ref('confirmed');
const mapOptions = ref({});

// 模拟生成一个随机的散点/热力图配置
// 真实开发需要引入 geoJSON 格式的地图数据
const initMap = () => {
  // 这里用 ECharts 的散点图模拟城市区块
  const data = Array.from({ length: 50 }).map(() => [
    Math.random() * 100, // X坐标
    Math.random() * 100, // Y坐标
    Math.floor(Math.random() * 1000) // 确诊数值
  ]);

  mapOptions.value = {
    tooltip: {},
    visualMap: {
      min: 0,
      max: 1000,
      inRange: { color: ['#50a3ba', '#eac736', '#d94e5d'] }
    },
    xAxis: { show: false, min: 0, max: 100 },
    yAxis: { show: false, min: 0, max: 100 },
    series: [{
      symbolSize: 20,
      data: data,
      type: 'scatter',
      itemStyle: { opacity: 0.8 }
    }]
  };
};

onMounted(initMap);
</script>