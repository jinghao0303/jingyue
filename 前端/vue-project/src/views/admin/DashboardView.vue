<template>
  <div class="dashboard-container">
    <!-- 1. 顶部导航栏 -->
    <header class="main-header">
      <div class="header-left">
        <el-icon :size="24" class="logo-icon"><TrendCharts /></el-icon>
        <span class="system-title">IDPS 传染病预测中心</span>
      </div>
      
      <div class="header-right">
        <div class="user-profile">
          <span class="welcome-text">欢迎, {{ userInfo.username }} ({{ userInfo.role === 'admin' ? '管理员' : '研究员' }})</span>
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="avatar-wrapper">
              <!-- 使用 Element Plus 的头像 -->
              <el-avatar :size="36" icon="UserFilled" class="user-avatar" />
              <el-icon class="el-icon--right"><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" disabled>个人中心</el-dropdown-item>
                <!-- 只有 admin 才能看到用户管理 -->
                <el-dropdown-item v-if="isSuperAdmin" command="manage_users" divided>
                  <el-icon><Tools /></el-icon>用户管理
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided style="color: #F56C6C;">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 2. 主内容区 -->
    <div class="main-content">
      <!-- 顶部数据卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6"><data-card title="累计确诊" value="12,450" unit="例" color="#F56C6C" icon="WarningFilled" /></el-col>
        <el-col :span="6"><data-card title="模型准确率" :value="modelAccuracy" :unit="typeof modelAccuracy === 'number' ? '%' : ''" color="#409EFF" icon="DataAnalysis" /></el-col>
        <el-col :span="6"><data-card title="当前 R0 值" :value="modelParams.r0" unit="" color="#E6A23C" icon="TrendCharts" /></el-col>
        <el-col :span="6"><data-card title="风险预测" value="高风险" unit="" color="#F56C6C" icon="BellFilled" /></el-col>
      </el-row>

      <el-row :gutter="20" class="content-row">
        <!-- 左侧：大图表 -->
        <el-col :span="16">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>流行性感冒实时趋势预测</span>
                <el-tag type="danger" effect="plain" size="small">实时推演中</el-tag>
              </div>
            </template>
            <!-- 这里的 style height 很重要，决定了图表高度 -->
            <div class="chart-wrapper" style="height: 400px;">
              <chart-box :options="mainChartOption" />
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：控制面板 + 雷达图 -->
        <el-col :span="8">
          <!-- 控制面板 -->
          <el-card shadow="hover" class="control-card">
            <template #header>
              <div class="card-header"><span>🛠️ 模型调控</span></div>
            </template>
            
            <el-form label-position="top" size="default">
              <el-form-item label="R0 (基本传染数)">
                <div class="slider-block">
                  <el-slider v-model="modelParams.r0" :min="0.5" :max="5" :step="0.1" show-input />
                </div>
              </el-form-item>
              
              <el-form-item label="预测天数 (Days)">
                <el-input-number v-model="modelParams.days" :min="1" :max="5" style="width: 100%;" />
              </el-form-item>

              <el-form-item label="模型算法选择">
                <el-select v-model="modelParams.algorithm" placeholder="请选择" style="width: 100%;">
                  <el-option label="SEIR 动力学模型" value="seir" />
                  <el-option label="LSTM 深度学习" value="lstm" />
                  <el-option label="Prophet 时序预测" value="prophet" />
                </el-select>
              </el-form-item>

              <el-button type="primary" class="w-100" @click="handleRunPrediction" :loading="loading">
                调用 Python 模型重新预测
              </el-button>
            </el-form>
          </el-card>

          <!-- 风险雷达图 (补充界面空白) -->
          <el-card shadow="hover" class="control-card" style="margin-top: 20px;">
            <template #header>
              <div class="card-header"><span>📊 风险雷达图</span></div>
            </template>
             <div class="radar-chart-wrapper">
               <chart-box :options="radarChartOption" />
             </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 3. 用户管理弹窗 (Admin 专属) -->
    <el-dialog v-model="dialogVisible" title="系统用户管理" width="700px">
      <el-table :data="userList" v-loading="dialogLoading" stripe style="width: 100%">
        <el-table-column prop="user_id" label="ID" width="80" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="120">
           <template #default="scope">{{ scope.row.real_name || '未设置' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'success' : 'info'">
              {{ scope.row.role }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- 操作列：三级权限管理 -->
        <el-table-column label="操作" align="right" width="220">
          <template #default="scope">
            
            <!-- 情况1: 如果是普通大众(public) -> 显示“批准入职” -->
            <el-button 
              v-if="scope.row.role === 'public'" 
              type="success" 
              size="small"
              @click="approveUser(scope.row)"
            >
              批准入职
            </el-button>

            <!-- 情况2: 如果是研究员(researcher) -> 显示“设为管理员” -->
            <el-button 
              v-else-if="scope.row.role === 'researcher'" 
              type="primary" 
              size="small"
              @click="promoteUser(scope.row)"
            >
              设为管理员
            </el-button>
            
            <!-- 情况3: 如果是管理员(admin) -> 显示“降级” -->
            <el-button 
              v-else-if="scope.row.role === 'admin'" 
              type="danger" 
              size="small"
              @click="demoteUser(scope.row)"
            >
              移除权限
            </el-button>

          </template>
        </el-table-column>
        
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
// 引入图标
import { TrendCharts, UserFilled, CaretBottom, SwitchButton, Tools, WarningFilled, DataAnalysis, BellFilled } from '@element-plus/icons-vue';
// 引入组件
import DataCard from '@/components/DataCard.vue';
import ChartBox from '@/components/ChartBox.vue';
// 引入 API (注意引入 demoteUserAPI)
import { predictAPI, getUserListAPI, promoteUserAPI, demoteUserAPI, approveUserAPI } from '@/api/index';

// [新增] 批准入职 (Public -> Researcher)
const approveUser = async (user: any) => {
  try {
    await approveUserAPI(user.user_id);
    ElMessage.success(`已批准 ${user.username} 为研究员`);
    openUserDialog(); // 刷新
  } catch (e) { console.error(e) }
};

const router = useRouter();
const loading = ref(false);

// --- 1. 用户信息逻辑 ---
const userInfo = ref({
  username: '',
  role: 'researcher'
});

// 计算属性：是否是超级管理员 (你的数据库里 admin 账号就是超级管理员)
const isSuperAdmin = computed(() => userInfo.value.username === 'admin');

// --- 2. 模型控制逻辑 ---
const modelParams = reactive({
  r0: 1.4,
  days: 3,  // 默认3天
  algorithm: 'seir',
  city_name: ''  // 城市名称，根据用户位置获取
});

// --- 3. 图表配置 (ECharts Option) ---
const mainChartOption = ref({});
const radarChartOption = ref({});
// 保存原始日期数组，用于tooltip显示
const originalDates = ref<string[]>([]);

// --- 3.5 模型准确率 ---
const modelAccuracy = ref<number | string>(0);

// --- 4. 用户管理逻辑 ---
const dialogVisible = ref(false);
const dialogLoading = ref(false);
const userList = ref([]);

// --- 生命周期 ---
onMounted(async () => {
  // 1. 检查登录
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('userInfo');
  
  if (!token || !userStr) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  userInfo.value = JSON.parse(userStr);
  
  // 2. 获取用户位置
  try {
    const { getCompleteLocation } = await import('@/utils/location');
    const locationResult = await getCompleteLocation();
    if (locationResult.success && locationResult.city) {
      // 提取城市名称（去掉"市"后缀，如果有）
      let cityName = locationResult.city;
      if (cityName.endsWith('市')) {
        cityName = cityName.slice(0, -1) + '市';  // 保留"市"
      }
      modelParams.city_name = cityName;
    } else {
      // 定位失败，使用默认城市
      modelParams.city_name = '清远市';
    }
  } catch (error) {
    console.error('获取位置失败:', error);
    modelParams.city_name = '清远市';  // 默认城市
  }
  
  // 3. 初始化加载一次图表 (使用默认参数)
  handleRunPrediction();
  initRadarChart();
});

// --- 方法集合 ---

// 菜单命令处理
const handleCommand = (cmd: string) => {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定要退出系统吗？', '提示', { type: 'warning' })
      .then(() => {
        localStorage.clear(); // 清除 token 和 userInfo
        router.push('/login');
        ElMessage.success('已退出登录');
      }).catch(() => {});
  } 
  else if (cmd === 'manage_users') {
    openUserDialog();
  }
};

// 调用预测 API
const handleRunPrediction = async () => {
  loading.value = true;
  try {
    // 这里的 API 调用你的后端 /api/predict/run
    const res: any = await predictAPI(modelParams);
    
    if (res.code === 200) {
      const { dates, predicted_values, actual_values, values } = res.data;
      // 使用新的数据结构，如果没有则使用旧的
      const predictedValues = predicted_values || values || [];
      const actualValues = actual_values || [];
      
      // 检查数据是否为空或全为0/null
      const validPredicted = predictedValues.filter(v => v !== null && v !== undefined && v !== 0);
      const validActual = actualValues.filter(v => v !== null && v !== undefined && v !== 0);
      
      if (validPredicted.length === 0 && validActual.length === 0) {
        ElMessage.warning('预测数据异常，所有值都为0，请检查数据源');
      }
      
      // 计算模型准确率
      calculateModelAccuracy(predictedValues, actualValues);
      
      updateMainChart(dates, predictedValues, actualValues);
      ElMessage.success('模型推演完成');
    }
  } catch (error: any) {
    console.error(error);
    
    // 检查是否是网络连接错误
    if (error.code === 'ERR_NETWORK' || error.message?.includes('ERR_CONNECTION_REFUSED')) {
      ElMessage.warning('无法连接到后端服务，请确保后端服务已启动（端口 5010）');
      // 如果后端没通，使用模拟数据防止页面空白
      mockChartData();
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器内部错误，请检查后端日志');
      mockChartData();
    } else {
      ElMessage.error('预测请求失败，使用模拟数据');
      mockChartData();
    }
  } finally {
    loading.value = false;
  }
};

// 计算模型准确率
const calculateModelAccuracy = (predictedValues: (number | null)[], actualValues: (number | null)[]) => {
  // 找到有实际值的日期对应的预测值和实际值
  const pairs: Array<{ predicted: number; actual: number }> = [];
  
  for (let i = 0; i < Math.min(predictedValues.length, actualValues.length); i++) {
    const predicted = predictedValues[i];
    const actual = actualValues[i];
    
    // 只有当预测值和实际值都不为null/undefined且大于0时才计算
    if (predicted !== null && predicted !== undefined && 
        actual !== null && actual !== undefined && 
        predicted > 0 && actual > 0) {
      pairs.push({
        predicted: Number(predicted),
        actual: Number(actual)
      });
    }
  }
  
  if (pairs.length === 0) {
    modelAccuracy.value = '--';
    return;
  }
  
  // 计算MAPE (平均绝对百分比误差)
  let totalMAPE = 0;
  for (const pair of pairs) {
    const error = Math.abs(pair.predicted - pair.actual) / pair.actual;
    totalMAPE += error;
  }
  const mape = totalMAPE / pairs.length;
  
  // 准确率 = (1 - MAPE) * 100%，确保不低于0
  const accuracy = Math.max(0, (1 - mape) * 100);
  modelAccuracy.value = Math.round(accuracy * 10) / 10; // 保留一位小数
};

// 更新主图表
const updateMainChart = (dates: string[], predictedValues: (number | null)[], actualValues?: (number | null)[]) => {
  // 保存原始日期数组
  originalDates.value = dates;
  
  // 处理数据：确保null值被正确处理，避免显示为0
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
  let yearMonth = '';
  let dayLabels: string[] = [];
  
  if (dates.length > 0) {
    const firstDate = dates[0];
    if (firstDate) {
      // 处理日期格式：可能是 "2025-11-23" 或 "2025/11/23" 等格式
      const dateMatch = firstDate.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
      if (dateMatch && dateMatch[1] && dateMatch[2]) {
        const year = dateMatch[1];
        const month = dateMatch[2].padStart(2, '0');
        yearMonth = `${year}-${month}`;
        
        // 提取所有日期的日部分
        dayLabels = dates.map(date => {
          const match = date.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
          return match && match[3] ? match[3].padStart(2, '0') : date;
        });
      } else {
        dayLabels = dates;
      }
    } else {
      // 如果日期格式不匹配，使用原日期
      dayLabels = dates;
    }
  } else {
    dayLabels = dates;
  }
  
  mainChartOption.value = {
    backgroundColor: 'transparent',
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
      data: ['预测感染人数', '实际感染人数'],
      top: 8,
      right: 20,
      orient: 'horizontal',
      itemGap: 20,
      textStyle: {
        fontSize: 13,
        color: '#606266',
        fontWeight: 500
      },
      icon: 'roundRect'
    },
    // 添加副标题显示年份和月份（放在右上角，图例下方）
    subtitle: yearMonth ? {
      text: yearMonth,
      top: 32,
      right: 20,
      textAlign: 'right',
      textStyle: {
        fontSize: 12,
        color: '#909399',
        fontWeight: 'normal'
      },
      show: true
    } : undefined,
    grid: { 
      left: '12%', 
      right: '8%', 
      top: yearMonth ? '15%' : '12%',
      bottom: '8%', 
      containLabel: true 
    },
    xAxis: { 
      type: 'category', 
      boundaryGap: false, 
      data: dayLabels,
      axisLine: {
        show: true,
        lineStyle: {
          color: '#E4E7ED',
          width: 1
        }
      },
      axisTick: {
        show: false
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
      type: 'value',
      name: '感染人数',
      nameLocation: 'middle',
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
      axisTick: {
        show: false
      },
      axisLabel: {
        fontSize: 12,
        color: '#909399',
        fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
        margin: 10,
        formatter: (value: number) => {
          // 格式化数值显示，避免科学计数法
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
      // 自动计算Y轴范围，确保数据正确显示
      scale: false,
      min: yAxisMin,
      max: yAxisMax
    },
    series: [
      {
        name: '预测感染人数',
        type: 'line',
        smooth: true,
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
        symbol: 'circle',
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
        name: '实际感染人数',
        type: 'line',
        smooth: true,
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
        symbol: 'circle',
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

// 备用：如果后端没开，用这个造假数据演示
const mockChartData = () => {
  const dates = ['Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7'];
  const values = [120, 132, 101, 134, 90, 230, 210].map(v => v * modelParams.r0);
  updateMainChart(dates, values, []);
};

// 初始化雷达图
const initRadarChart = () => {
  radarChartOption.value = {
    radar: {
      indicator: [
        { name: '传播速度', max: 100, min: 0 },
        { name: '医疗负荷', max: 100, min: 0 },
        { name: '物资缺口', max: 100, min: 0 },
        { name: '社会恐慌', max: 100, min: 0 },
        { name: '经济影响', max: 100, min: 0 }
      ],
      radius: '60%', // 减小半径，为文字留出更多空间
      center: ['50%', '55%'], // 稍微下移，为上方文字留空间
      axisNameGap: 8, // 标签与雷达图中心的距离（修复：nameGap -> axisNameGap）
      splitNumber: 4, // 分割段数
      axisName: { // 修复：name -> axisName，并直接在 axisName 上设置样式
        color: '#606266',
        fontSize: 12,
        fontWeight: 'normal',
        padding: [2, 4] // 文字内边距
      },
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250, 250, 250, 0.3)', 'rgba(200, 200, 200, 0.1)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{ 
        value: [80, 60, 40, 70, 50], 
        name: '当前风险',
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: { 
          color: 'rgba(64, 158, 255, 0.3)' 
        },
        lineStyle: {
          color: '#409EFF',
          width: 2
        }
      }]
    }]
  };
};

// 打开用户弹窗
const openUserDialog = async () => {
  dialogVisible.value = true;
  dialogLoading.value = true;
  try {
    const res: any = await getUserListAPI();
    if (res.code === 200) {
      // 过滤掉 admin 自己
      userList.value = res.data.filter((u: any) => u.username !== 'admin');
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败');
  } finally {
    dialogLoading.value = false;
  }
};

// 提升用户
const promoteUser = async (user: any) => {
  try {
    await promoteUserAPI(user.user_id);
    ElMessage.success(`用户 ${user.username} 已设为管理员`);
    openUserDialog(); // 刷新列表
  } catch (error) {
    console.error(error);
  }
};

// [新增] 移除权限 (降级)
const demoteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除用户 ${user.username} 的管理员权限吗？\n移除后该用户将无法管理其他用户。`, 
      '降级警告', 
      { 
        type: 'warning', 
        confirmButtonText: '确定移除', 
        cancelButtonText: '取消' 
      }
    );
    
    await demoteUserAPI(user.user_id);
    ElMessage.success(`已移除用户 ${user.username} 的管理员权限`);
    openUserDialog(); // 刷新列表
  } catch (error) {
    // 用户点击取消或请求失败，不做处理
  }
};
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  display: flex;
  flex-direction: column;
}

/* 顶部 Header */
.main-header {
  height: 60px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}
.logo-icon { margin-right: 8px; color: #409EFF; }

.header-right .user-profile {
  display: flex;
  align-items: center;
  cursor: pointer;
}
.welcome-text {
  font-size: 14px;
  color: #606266;
  margin-right: 12px;
}
.avatar-wrapper {
  display: flex;
  align-items: center;
}
.user-avatar { background-color: #409EFF; }

/* 主内容 */
.main-content {
  padding: 20px;
  flex: 1;
}
.stats-row { margin-bottom: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.w-100 { width: 100%; }
.text-gray { color: #909399; font-size: 12px; }

/* 适配 Element UI 的 Slider */
.slider-block {
  padding: 0 10px;
}

/* 雷达图容器 */
.radar-chart-wrapper {
  height: 350px;
  width: 100%;
  min-height: 350px;
  padding: 10px;
  box-sizing: border-box;
}

.radar-chart-wrapper :deep(.chart-container) {
  height: 100% !important;
  width: 100% !important;
}

/* 图表容器居中 */
.chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.chart-wrapper :deep(.chart-container) {
  width: 100% !important;
  height: 100% !important;
}
</style>