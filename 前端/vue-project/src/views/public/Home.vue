<template>
  <div class="home-page">
    <!-- 头部：定位与天气 -->
    <div class="header-bg">
      <div class="location-row">
        <div class="city" @click="refreshLocation">
          <el-icon :class="{ 'is-loading': locating }"><Position /></el-icon>
          <!-- 这里只显示城市名，更简洁 -->
          <span class="city-text">{{ locationState.city }}</span>
          

        </div>
        <div class="weather">
          <span v-if="weatherLoading">🌡️ 获取中...</span>
          <span v-else-if="weatherInfo">
            🌡️ {{ weatherInfo.temperature }}°C {{ fluTransmissionText }}
          </span>
          <span v-else>🌡️ --°C 温度获取失败</span>
        </div>
      </div>
      <div class="title-area">
        <h2>都市流感态势感知</h2>
        <p>基于 IDPS 模型 · 实时预测未来 7 天趋势</p>
      </div>
    </div>

    <!-- 核心预测卡片 -->
    <div class="prediction-card-wrapper">
      <el-card class="prediction-card" shadow="hover">
        <div class="card-title">未来 3 天趋势预测</div>
        <div class="prediction-result text-danger">
          <el-icon :size="24"><Top /></el-icon>
          <span class="big-text">{{ predictionCardInfo.trend }}</span>
        </div>
        <div class="prediction-desc" v-if="predictionLoading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在加载预测数据...</span>
        </div>
        <div class="prediction-desc" v-else>
          模型分析显示，<strong>{{ locationState.simpleCity }}</strong> 流感病毒活跃度{{ predictionCardInfo.trend.includes('快速') ? '快速' : '' }}上升，
          预计未来三天新增病例约 <strong>{{ predictionCardInfo.newCases }}</strong> 例。
          {{ predictionCardInfo.suggestion }}
        </div>
      </el-card>
    </div>

    <!-- 趋势图表 -->
    <div class="section-box">
      <div class="section-header">
        <h3>📈 {{ locationState.simpleCity }}流行性感冒感染人数预测</h3>
        <span class="year-month" v-if="yearMonth">{{ yearMonth }}</span>
      </div>
      <div class="chart-wrapper" v-loading="predictionLoading">
        <chart-box :options="trendChartOption" />
      </div>
    </div>

    <!-- 风险区域预警 -->
    <div class="section-box">
      <div class="section-header">
        <h3>⚠️ 重点风险行政区</h3>
        <el-link type="primary" @click="router.push('/public/map')">查看地图 ></el-link>
      </div>
      <div class="risk-district-list">
        <div class="district-item high-risk">
          <span class="d-name">{{ districts[0] }}</span>
          <span class="d-tag">高风险</span>
        </div>
        <div class="district-item mid-risk">
          <span class="d-name">{{ districts[1] }}</span>
          <span class="d-tag">中风险</span>
        </div>
        <div class="district-item mid-risk">
          <span class="d-name">{{ districts[2] }}</span>
          <span class="d-tag">中风险</span>
        </div>
      </div>
    </div>

    <!-- 快捷服务 -->
    <div class="quick-actions">
      <div class="action-btn" @click="router.push('/public/map')">
        <div class="icon-box blue"><el-icon><MapLocation /></el-icon></div>
        <span>发热门诊</span>
      </div>
      <div class="action-btn" @click="router.push('/public/guide')">
        <div class="icon-box green"><el-icon><FirstAidKit /></el-icon></div>
        <span>疫苗接种</span>
      </div>
      <div class="action-btn" @click="router.push('/public/guide')">
        <div class="icon-box orange"><el-icon><Reading /></el-icon></div>
        <span>流感科普</span>
      </div>
      <div class="action-btn" @click="router.push('/login')">
        <div class="icon-box purple"><el-icon><User /></el-icon></div>
        <span>专家入口</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Position, Top, MapLocation, FirstAidKit, Reading, User, Loading } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import ChartBox from '@/components/ChartBox.vue';
import { getCompleteLocation, watchLocation, clearLocationWatch, type LocationWatchCallback } from '@/utils/location';
import { getWeatherByCoordinates, getFluTransmissionText, type WeatherInfo } from '@/utils/weather';
import { getPublicPredictAPI, getDefaultModelConfigAPI } from '@/api/index';

const router = useRouter();
const locating = ref(false);
const locationWatchId = ref<number | null>(null);
const isWatchingLocation = ref(false);

// --- 1. 智能定位逻辑 ---
const locationState = reactive({
  city: '定位中...',
  simpleCity: '本市', // 用于显示的简称
  coords: null as { lat: number; lng: number } | null
});

// --- 2. 天气信息 ---
const weatherInfo = ref<WeatherInfo | null>(null);
const weatherLoading = ref(false);
const weatherUpdateTimer = ref<number | null>(null);

// 计算属性：流感传播描述
const fluTransmissionText = computed(() => {
  if (!weatherInfo.value) return '温度获取失败';
  return getFluTransmissionText(weatherInfo.value.temperature);
});

// 获取天气信息
const fetchWeather = async (lat?: number, lng?: number, cityName?: string) => {
  // 如果没有提供坐标，使用当前位置
  if (!lat || !lng) {
    if (locationState.coords) {
      lat = locationState.coords.lat;
      lng = locationState.coords.lng;
    } else {
      return;
    }
  }
  
  weatherLoading.value = true;
  try {
    const weather = await getWeatherByCoordinates(lat, lng, cityName || locationState.simpleCity);
    if (weather) {
      weatherInfo.value = weather;
    }
  } catch (error) {
    // 静默处理错误，不显示控制台信息
  } finally {
    weatherLoading.value = false;
  }
};

// 定期更新天气（每30分钟）
const startWeatherUpdate = () => {
  // 清除旧的定时器
  if (weatherUpdateTimer.value !== null) {
    clearInterval(weatherUpdateTimer.value);
  }
  
  // 立即获取一次
  if (locationState.coords) {
    fetchWeather();
  }
  
  // 每30分钟更新一次
  weatherUpdateTimer.value = window.setInterval(() => {
    if (locationState.coords) {
      fetchWeather();
    }
  }, 30 * 60 * 1000); // 30分钟
};

// 停止天气更新
const stopWeatherUpdate = () => {
  if (weatherUpdateTimer.value !== null) {
    clearInterval(weatherUpdateTimer.value);
    weatherUpdateTimer.value = null;
  }
};

// 动态行政区显示（根据定位变化，这里先做简单的模拟映射）
const districts = computed(() => {
  if (locationState.city.includes('广州')) return ['天河区', '海珠区', '越秀区'];
  if (locationState.city.includes('深圳')) return ['福田区', '南山区', '罗湖区'];
  if (locationState.city.includes('北京')) return ['朝阳区', '海淀区', '丰台区'];
  if (locationState.city.includes('清远')) return ['清城区', '清新区', '英德市'];
  return ['核心商务区', '老城区', '大学城区']; // 默认
});

const refreshLocation = async () => {
  locating.value = true;
  locationState.city = '正在获取位置...';

  try {
    // 使用统一的定位工具类
    const result = await getCompleteLocation();
    
    if (result.success) {
      locationState.city = result.fullAddress;
      locationState.simpleCity = result.city;
      
      // 保存坐标用于获取天气
      if (result.coords) {
        locationState.coords = {
          lat: parseFloat(result.coords.lat),
          lng: parseFloat(result.coords.lng)
        };
        // 获取天气信息
        await fetchWeather(locationState.coords.lat, locationState.coords.lng, result.city);
      }
      
      ElMessage.success(`定位成功：${result.city}`);
    } else {
      locationState.city = result.fullAddress;
      ElMessage.warning(result.error || '定位失败');
    }
  } catch (error) {
    console.error('定位过程出错:', error);
    locationState.city = '定位失败';
    ElMessage.error('定位过程发生错误');
  } finally {
    locating.value = false;
  }
};

// 位置变化回调处理
const handleLocationChange: LocationWatchCallback = async (result) => {
  if (result.success) {
    const newCity = result.city || '本市';
    
    // 更新坐标
    if (result.coords) {
      locationState.coords = {
        lat: parseFloat(result.coords.lat),
        lng: parseFloat(result.coords.lng)
      };
    }
    
    // 检测城市是否发生变化
    if (newCity !== locationState.simpleCity) {
      ElMessage.success(`检测到位置变化：${result.fullAddress}`);
      locationState.city = result.fullAddress;
      locationState.simpleCity = newCity;
      
      // 城市变化时更新天气
      if (locationState.coords) {
        await fetchWeather(locationState.coords.lat, locationState.coords.lng, newCity);
      }
    } else {
      // 城市没变，但位置更新了
      locationState.city = result.fullAddress;
      // 位置变化较大时也更新天气（可选）
    }
  }
};

// 开始实时位置跟踪
const startLocationWatch = () => {
  if (isWatchingLocation.value) return;
  
  isWatchingLocation.value = true;
  locationWatchId.value = watchLocation(handleLocationChange, {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 30000, // 30秒
    distanceThreshold: 10000 // 10公里阈值（使用 distanceThreshold 替代 cityChangeThreshold）
  });
  
  if (locationWatchId.value !== null) {
    // 实时位置跟踪已开启
  }
};

// 停止实时位置跟踪
const stopLocationWatch = () => {
  if (locationWatchId.value !== null) {
    clearLocationWatch(locationWatchId.value);
    locationWatchId.value = null;
    isWatchingLocation.value = false;
  }
};



// --- 3. 预测数据 ---
const predictionLoading = ref(false);
const predictionData = ref<{
  dates: string[];
  values: number[];
  meta?: any;
} | null>(null);
// 保存原始日期数组，用于tooltip显示
const originalDates = ref<string[]>([]);
// 保存年份和月份，用于在标题右侧显示
const yearMonth = ref<string>('');

// --- 4. 图表配置 ---
const trendChartOption = ref<Record<string, any>>({
  tooltip: { 
    trigger: 'axis',
    formatter: (params: any) => {
      // 使用原始完整日期显示
      if (Array.isArray(params) && params.length > 0) {
        const index = params[0].dataIndex;
        const fullDate = originalDates.value[index] || params[0].axisValue;
        const value = params[0].value;
        return `${fullDate}<br/>预测感染人数: ${value}`;
      }
      return '';
    }
  },
  legend: { 
    data: ['预测感染人数', '实际感染人数'],
    top: 5,
    right: 20,
    orient: 'horizontal'
  },
  grid: { 
    left: '18%', 
    right: '4%', 
    top: '5%',
    bottom: '3%', 
    containLabel: true 
  },
  xAxis: { 
    type: 'category', 
    boundaryGap: false,
    data: [] as string[],
    axisLine: { show: false },
    axisTick: { show: false }
  },
  yAxis: { 
    type: 'value',
    name: '感染人数',
    nameLocation: 'middle',
    nameGap: 60,
    nameRotate: 90,
    nameTextStyle: {
      fontSize: 14,
      color: '#606266',
      fontWeight: 'normal',
      fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
      padding: [0, 0, 0, 0]
    },
    axisLabel: {
      fontSize: 12,
      color: '#606266',
      fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
      margin: 8
    },
    splitLine: { lineStyle: { type: 'dashed' } } 
  },
  series: [
    { 
      name: '预测感染人数',
      type: 'line', 
      data: [] as (number | null)[],
      smooth: true, 
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#F56C6C' },
      areaStyle: { color: 'rgba(245, 108, 108, 0.1)' }
    },
    {
      name: '实际感染人数',
      type: 'line',
      data: [] as (number | null)[],
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#409EFF' },
      lineStyle: { type: 'dashed' }
    }
  ]
});

// 获取默认模型配置
const defaultModelConfig = ref({
  default_algorithm: 'seir',
  r0: 1.4,
  incubation_period: 5.0,
  infectious_period: 7.0,
  intervention_factor: 1.0,
  days: 3
});

// 模型配置刷新定时器
const modelConfigRefreshTimer = ref<number | null>(null);

const loadDefaultModelConfig = async (silent = false) => {
  try {
    const res: any = await getDefaultModelConfigAPI();
    if (res.code === 200 && res.data) {
      // 保存旧配置用于对比
      const oldConfig = {
        algorithm: defaultModelConfig.value.default_algorithm,
        r0: defaultModelConfig.value.r0,
        incubation_period: defaultModelConfig.value.incubation_period,
        infectious_period: defaultModelConfig.value.infectious_period,
        intervention_factor: defaultModelConfig.value.intervention_factor,
        days: defaultModelConfig.value.days
      };
      
      // 更新配置
      const newAlgorithm = (res.data.default_algorithm && res.data.default_algorithm !== '') ? res.data.default_algorithm : 'seir';
      const newR0 = res.data.r0 || 1.4;
      const newIncubationPeriod = res.data.incubation_period || 5.0;
      const newInfectiousPeriod = res.data.infectious_period || 7.0;
      const newInterventionFactor = res.data.intervention_factor || 1.0;
      const newDays = res.data.days || 3;
      
      // 检查是否有任何参数发生变化
      const algorithmChanged = oldConfig.algorithm !== newAlgorithm;
      const r0Changed = Math.abs(oldConfig.r0 - newR0) > 0.01;
      const incubationChanged = Math.abs(oldConfig.incubation_period - newIncubationPeriod) > 0.01;
      const infectiousChanged = Math.abs(oldConfig.infectious_period - newInfectiousPeriod) > 0.01;
      const interventionChanged = Math.abs(oldConfig.intervention_factor - newInterventionFactor) > 0.01;
      const daysChanged = oldConfig.days !== newDays;
      
      const configChanged = algorithmChanged || r0Changed || incubationChanged || infectiousChanged || interventionChanged || daysChanged;
      
      // 更新配置值
      defaultModelConfig.value.default_algorithm = newAlgorithm;
      defaultModelConfig.value.r0 = newR0;
      defaultModelConfig.value.incubation_period = newIncubationPeriod;
      defaultModelConfig.value.infectious_period = newInfectiousPeriod;
      defaultModelConfig.value.intervention_factor = newInterventionFactor;
      defaultModelConfig.value.days = newDays;
      
      
      // 如果配置发生变化，自动刷新预测数据（确保前台立即使用新配置）
      if (configChanged && !silent) {
        if (locationState.simpleCity && 
            locationState.simpleCity !== '定位中...' && 
            locationState.simpleCity !== '本市') {
          const changes = [];
          if (algorithmChanged) {
            changes.push(`算法: ${oldConfig.algorithm} -> ${newAlgorithm}`);
          }
          if (r0Changed) {
            changes.push(`R0: ${oldConfig.r0} -> ${newR0}`);
          }
          if (incubationChanged) {
            changes.push(`潜伏期: ${oldConfig.incubation_period} -> ${newIncubationPeriod}`);
          }
          if (infectiousChanged) {
            changes.push(`传染期: ${oldConfig.infectious_period} -> ${newInfectiousPeriod}`);
          }
          if (interventionChanged) {
            changes.push(`防控因子: ${oldConfig.intervention_factor} -> ${newInterventionFactor}`);
          }
          if (daysChanged) {
            changes.push(`预测天数: ${oldConfig.days} -> ${newDays}`);
          }
          fetchPrediction();
        }
      }
    } else {
      console.warn('[模型配置] API返回异常:', res);
    }
  } catch (error) {
    console.error('[模型配置] 获取默认模型配置失败:', error);
  }
};

// 启动模型配置自动刷新（每10秒刷新一次，确保及时获取后台配置变化）
const startModelConfigRefresh = () => {
  // 清除旧的定时器
  if (modelConfigRefreshTimer.value !== null) {
    clearInterval(modelConfigRefreshTimer.value);
  }
  
  // 每5秒刷新一次配置，确保后台切换模型后前台能及时更新
  modelConfigRefreshTimer.value = window.setInterval(() => {
    loadDefaultModelConfig();
  }, 5 * 1000); // 5秒
};

// 停止模型配置自动刷新
const stopModelConfigRefresh = () => {
  if (modelConfigRefreshTimer.value !== null) {
    clearInterval(modelConfigRefreshTimer.value);
    modelConfigRefreshTimer.value = null;
  }
};

// 获取预测数据
const fetchPrediction = async () => {
  if (!locationState.simpleCity || locationState.simpleCity === '定位中...' || locationState.simpleCity === '本市') {
    return;
  }
  
  predictionLoading.value = true;
  try {
    // 每次预测前都重新获取最新的模型配置，确保使用后台最新设置的默认算法
    // 传入 silent=true 避免在 fetchPrediction 中触发重复刷新
    await loadDefaultModelConfig(true);
    
    // 使用配置的默认模型和参数
    const params = {
      algorithm: defaultModelConfig.value.default_algorithm,  // 使用配置的默认算法
      r0: defaultModelConfig.value.r0,
      incubation_period: defaultModelConfig.value.incubation_period,
      infectious_period: defaultModelConfig.value.infectious_period,
      intervention_factor: defaultModelConfig.value.intervention_factor,
      days: defaultModelConfig.value.days,  // 使用配置的预测天数
      city_name: locationState.simpleCity  // 根据用户位置获取对应城市的数据
    };
    
    const res: any = await getPublicPredictAPI(params);
    
    if (res.code === 200 && res.data) {
      predictionData.value = {
        dates: res.data.dates || [],
        values: res.data.predicted_values || res.data.values || [],
        meta: res.data.meta
      };
      
      // 更新图表（传入预测值和实际值）
      const predictedValues = res.data.predicted_values || res.data.values || [];
      const actualValues = res.data.actual_values || [];
      updateTrendChart(res.data.dates, predictedValues, actualValues);
      
      // 更新预测卡片信息
      if (res.data.meta) {
        updatePredictionCard(res.data.meta);
      }
    }
  } catch (error) {
    // 如果API调用失败，使用默认数据
    const defaultDates = ['今天', '明天', '周三', '周四', '周五', '周六', '周日'];
    const defaultValues = [120, 135, 160, 190, 210, 205, 198];
    updateTrendChart(defaultDates, defaultValues, []);
  } finally {
    predictionLoading.value = false;
  }
};

// 更新趋势图表
const updateTrendChart = (dates: string[], predictedValues: (number | null)[], actualValues?: (number | null)[]) => {
  // 保存原始日期数组
  originalDates.value = dates;
  
  // 处理数据：确保null值被正确处理
  const processedPredicted = predictedValues.map(v => {
    if (v === null || v === undefined) return null;
    return Number(v);
  });
  
  const processedActual = (actualValues || []).map(v => {
    if (v === null || v === undefined) return null;
    return Number(v);
  });
  
  // 计算Y轴范围（优化：圆整处理，避免浮点数精度问题）
  const allValues = [...processedPredicted, ...processedActual]
    .filter(v => v !== null && v !== undefined && !isNaN(Number(v)))
    .map(v => Number(v));
  
  let yAxisMin: number | undefined = undefined;
  let yAxisMax: number | undefined = undefined;
  
  if (allValues.length > 0) {
    const minVal = Math.min(...allValues);
    const maxVal = Math.max(...allValues);
    
    // 如果最小值大于0，从0开始；否则从最小值向下留10%的边距
    yAxisMin = minVal > 0 ? 0 : Math.floor(minVal * 1.1);
    
    // 向上留15%的边距，并圆整到合适的刻度
    const rawMax = maxVal * 1.15;
    // 根据数值大小选择合适的圆整步长
    let step = 1;
    if (rawMax > 10000) {
      step = 1000;
    } else if (rawMax > 1000) {
      step = 100;
    } else if (rawMax > 100) {
      step = 50;
    } else if (rawMax > 50) {
      step = 10;
    } else {
      step = 5;
    }
    // 向上圆整到最近的step倍数
    yAxisMax = Math.ceil(rawMax / step) * step;
  } else {
    yAxisMin = 0;
    yAxisMax = 100;
  }
  
  // 提取年份和月份（从第一个日期）
  let extractedYearMonth = '';
  let dayLabels: string[] = [];
  
  if (dates.length > 0) {
    const firstDate = dates[0];
    if (firstDate) {
      // 处理日期格式：可能是 "2025-11-23" 或 "2025/11/23" 等格式
      const dateMatch = firstDate.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
      if (dateMatch && dateMatch[1] && dateMatch[2]) {
        const year = dateMatch[1];
        const month = dateMatch[2].padStart(2, '0');
        extractedYearMonth = `${year}-${month}`;
        
        // 提取所有日期的日部分
        dayLabels = dates.map(date => {
          const match = date.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
          return match && match[3] ? match[3].padStart(2, '0') : date;
        });
      } else {
        // 如果日期格式不匹配，使用原日期
        dayLabels = dates;
      }
    } else {
      dayLabels = dates;
    }
  } else {
    dayLabels = dates;
  }
  
  // 更新年份月份显示
  yearMonth.value = extractedYearMonth;
  
  trendChartOption.value = {
    ...trendChartOption.value,
    backgroundColor: 'transparent',
    // 更新tooltip的formatter
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 13
      },
      padding: [10, 15],
      formatter: (params: any) => {
        // 使用原始完整日期显示
        if (Array.isArray(params) && params.length > 0) {
          const index = params[0].dataIndex;
          const fullDate = originalDates.value[index] || params[0].axisValue;
          let tooltipText = `<div style="font-weight: 600; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 5px;">${fullDate}</div>`;
          
          // 显示预测值
          if (params[0] && params[0].value !== null && params[0].value !== undefined) {
            const color = params[0].color || '#F56C6C';
            tooltipText += `<div style="margin: 4px 0;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${color}; border-radius: 50%; margin-right: 6px;"></span>
              <span style="font-weight: 500;">${params[0].seriesName}:</span> 
              <span style="color: ${color}; font-weight: 600;">${params[0].value}</span>
            </div>`;
          }
          
          // 显示实际值（如果有）
          if (params[1] && params[1].value !== null && params[1].value !== undefined) {
            const color = params[1].color || '#409EFF';
            tooltipText += `<div style="margin: 4px 0;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${color}; border-radius: 50%; margin-right: 6px;"></span>
              <span style="font-weight: 500;">${params[1].seriesName}:</span> 
              <span style="color: ${color}; font-weight: 600;">${params[1].value}</span>
            </div>`;
          }
          
          return tooltipText;
        }
        return '';
      }
    },
    legend: {
      ...trendChartOption.value.legend,
      itemGap: 20,
      textStyle: {
        fontSize: 13,
        color: '#606266',
        fontWeight: 500
      },
      icon: 'roundRect'
    },
    grid: {
      ...trendChartOption.value.grid,
      left: '12%',
      right: '8%',
      bottom: '8%'
    },
    xAxis: {
      ...trendChartOption.value.xAxis,
      data: dayLabels,
      axisLine: {
        show: true,
        lineStyle: {
          color: '#E4E7ED',
          width: 1
        }
      },
      axisLabel: {
        fontSize: 12,
        color: '#909399',
        margin: 10
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      ...trendChartOption.value.yAxis,
      nameGap: 55,
      nameRotate: 90,
      nameTextStyle: {
        fontSize: 13,
        color: '#606266',
        fontWeight: 500,
        fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
        padding: [0, 0, 0, 0]
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: '#E4E7ED',
          width: 1
        }
      },
      axisLabel: {
        fontSize: 12,
        color: '#909399',
        fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
        margin: 10,
        formatter: (value: number) => {
          // 格式化数值显示
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + '万';
          }
          return Math.round(value).toString();
        }
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#EBEEF5',
          width: 1
        }
      },
      scale: false,
      min: yAxisMin,
      max: yAxisMax
    },
    series: [
      {
        ...trendChartOption.value.series[0],
        data: processedPredicted,
        itemStyle: {
          color: '#F56C6C',
          borderWidth: 2,
          borderColor: '#fff'
        },
        lineStyle: {
          color: '#F56C6C',
          width: 3
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
              { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
            ]
          }
        },
        symbolSize: 8,
        emphasis: {
          focus: 'series',
          itemStyle: {
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(245, 108, 108, 0.5)'
          }
        }
      },
      {
        ...trendChartOption.value.series[1],
        data: processedActual,
        itemStyle: {
          color: '#409EFF',
          borderWidth: 2,
          borderColor: '#fff'
        },
        lineStyle: {
          type: 'dashed',
          width: 3,
          color: '#409EFF'
        },
        symbolSize: 8,
        connectNulls: false,
        emphasis: {
          focus: 'series',
          itemStyle: {
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(64, 158, 255, 0.5)'
          }
        }
      }
    ]
  };
};

// 更新预测卡片信息
const predictionCardInfo = reactive({
  trend: '呈上升趋势',
  newCases: '3,200',
  suggestion: '建议在公共场所佩戴口罩。'
});

const updatePredictionCard = (meta: any) => {
  if (meta.max_cases) {
    // 计算未来3天新增病例（简单估算）
    const firstThreeDays = predictionData.value?.values.slice(0, 3) || [];
    const totalNewCases = firstThreeDays.reduce((sum, val, idx) => {
      if (idx === 0) return 0;
      return sum + (val - (firstThreeDays[idx - 1] || 0));
    }, 0);
    predictionCardInfo.newCases = totalNewCases.toLocaleString();
  }
  
  if (meta.risk_level) {
    if (meta.risk_level === '高') {
      predictionCardInfo.trend = '呈快速上升趋势';
      predictionCardInfo.suggestion = '建议减少外出，避免聚集，及时就医。';
    } else if (meta.risk_level === '中') {
      predictionCardInfo.trend = '呈上升趋势';
      predictionCardInfo.suggestion = '建议在公共场所佩戴口罩，注意个人卫生。';
    } else {
      predictionCardInfo.trend = '呈平稳趋势';
      predictionCardInfo.suggestion = '保持日常防护，注意个人卫生。';
    }
  }
};

// 监听城市变化，自动更新预测数据
watch(() => locationState.simpleCity, (newCity) => {
  if (newCity && newCity !== '定位中...' && newCity !== '本市') {
    fetchPrediction();
  }
});

// 页面可见性变化处理（当用户切换回页面时立即检查配置）
const handleVisibilityChange = () => {
  if (!document.hidden) {
    // 页面重新可见时，立即检查模型配置是否有变化
    loadDefaultModelConfig();
  }
};

// 窗口焦点变化处理（当窗口重新获得焦点时立即检查）
const handleWindowFocus = () => {
  loadDefaultModelConfig();
};

onMounted(async () => {
  // 1. 先加载默认模型配置
  await loadDefaultModelConfig();
  
  // 2. 获取用户位置
  await refreshLocation();
  
  // 3. 自动开启实时位置跟踪
  startLocationWatch();
  
  // 4. 开启天气自动更新
  startWeatherUpdate();
  
  // 5. 开启模型配置自动刷新（每10秒检查一次，确保实时使用后台最新设置）
  startModelConfigRefresh();
  
  // 6. 监听页面可见性变化（当用户切换回页面时立即检查）
  document.addEventListener('visibilitychange', handleVisibilityChange);
  
  // 7. 监听窗口焦点变化（当窗口重新获得焦点时立即检查）
  window.addEventListener('focus', handleWindowFocus);
  
  // 8. 获取预测数据（使用配置的默认模型）
  if (locationState.simpleCity && locationState.simpleCity !== '定位中...' && locationState.simpleCity !== '本市') {
    fetchPrediction();
  }
});

// 页面卸载时停止位置跟踪、天气更新和配置刷新
onBeforeUnmount(() => {
  stopLocationWatch();
  stopWeatherUpdate();
  stopModelConfigRefresh();
  // 移除事件监听器
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  window.removeEventListener('focus', handleWindowFocus);
});
</script>

<style scoped>
.home-page { 
  min-height: 100%; 
  background: #f5f7fa; 
  padding-bottom: 20px; 
  position: relative;
  overflow-x: hidden;
}

/* 头部样式优化 */
.header-bg {
  background: linear-gradient(120deg, #2c3e50 0%, #4ca1af 100%);
  color: white;
  padding: 20px 20px 80px;
  border-bottom-left-radius: 24px;
  border-bottom-right-radius: 24px;
  position: relative;
  z-index: 1;
  margin-bottom: 0;
}
.location-row { display: flex; justify-content: space-between; margin-bottom: 15px; align-items: flex-start; }

/* 城市名显示优化 */
.city { display: flex; align-items: center; gap: 5px; cursor: pointer; background: rgba(255,255,255,0.15); padding: 5px 10px; border-radius: 20px; backdrop-filter: blur(4px); }
.city-text { font-size: 15px; font-weight: bold; }

.is-loading { animation: rotating 2s linear infinite; }

.title-area h2 { margin: 0; font-size: 22px; letter-spacing: 1px; }
.title-area p { margin: 5px 0 0; opacity: 0.9; font-size: 12px; }

/* 预测卡片 */
.prediction-card-wrapper { 
  padding: 0 20px; 
  margin-top: -60px; 
  margin-bottom: 20px; 
  position: relative;
  z-index: 10;
}
.prediction-card { 
  border-radius: 16px; 
  border: none; 
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
  position: relative;
  z-index: 10;
  background: white;
  overflow: visible;
  margin: 0;
}
.card-title { font-size: 14px; color: #909399; margin-bottom: 10px; font-weight: bold; }
.prediction-result { display: flex; align-items: center; gap: 8px; margin-bottom: 15px; }
.big-text { font-size: 24px; font-weight: 800; }
.text-danger { color: #F56C6C; }
.prediction-desc { font-size: 14px; color: #606266; line-height: 1.6; background: #f9fafc; padding: 10px; border-radius: 8px; }

/* 通用板块 */
.section-box { 
  background: white; 
  margin: 15px 20px; 
  padding: 20px; 
  border-radius: 12px; 
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  overflow: visible;
  min-height: 200px;
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.section-header h3 { margin: 0; font-size: 16px; border-left: 4px solid #4ca1af; padding-left: 10px; flex: 1; }
.year-month { 
  font-size: 12px; 
  color: #909399; 
  font-weight: normal;
  margin-left: 10px;
}
.chart-wrapper { 
  height: 300px; 
  position: relative;
  z-index: 1;
  overflow: visible;
  width: 100%;
  min-height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart-wrapper :deep(.chart-container) {
  width: 100% !important;
  height: 100% !important;
}

/* 风险区列表 */
.district-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }
.district-item:last-child { border-bottom: none; }
.d-name { font-weight: 500; }
.d-tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.high-risk .d-tag { background: #fef0f0; color: #F56C6C; }
.mid-risk .d-tag { background: #fdf6ec; color: #E6A23C; }

/* 快捷按钮 */
.quick-actions { display: flex; justify-content: space-between; padding: 0 20px; margin-top: 20px; }
.action-btn { display: flex; flex-direction: column; align-items: center; width: 22%; cursor: pointer; }
.icon-box { width: 48px; height: 48px; border-radius: 16px; display: flex; justify-content: center; align-items: center; color: white; margin-bottom: 8px; font-size: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.blue { background: #409EFF; }
.green { background: #67C23A; }
.orange { background: #E6A23C; }
.purple { background: #9060df; }
.action-btn span { font-size: 12px; color: #333; }

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>