<template>
  <div class="data-monitor-page">
    <el-card class="page-header">
      <h2>📊 训练数据监控</h2>
      <p>查看数据库中用于模型预测和训练的数据情况</p>
    </el-card>

    <!-- 数据统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background: #409EFF;">
            <el-icon :size="24"><Location /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_cities || 0 }}</div>
            <div class="stat-label">总城市数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background: #67C23A;">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_records || 0 }}</div>
            <div class="stat-label">总数据记录</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background: #E6A23C;">
            <el-icon :size="24"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.cities_with_data || 0 }}</div>
            <div class="stat-label">有数据的城市</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background: #F56C6C;">
            <el-icon :size="24"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.recent_records_30d || 0 }}</div>
            <div class="stat-label">近30天记录</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 数据日期范围 -->
    <el-card class="date-range-card" v-if="stats.earliest_date">
      <div class="date-range-info">
        <span><strong>数据日期范围：</strong>{{ stats.earliest_date }} 至 {{ stats.latest_date }}</span>
      </div>
    </el-card>

    <!-- 数据质量表格 -->
    <el-card class="quality-card">
      <template #header>
        <div class="card-header">
          <span>数据质量检查</span>
          <el-button type="primary" size="small" @click="refreshData">刷新数据</el-button>
        </div>
      </template>
      
      <!-- 搜索框 -->
      <div class="search-section">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索城市名称..."
          clearable
          @input="handleSearch"
          @clear="handleSearch"
          style="max-width: 400px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <!-- 城市列表 -->
      <div class="city-list-section">
        <el-empty v-if="!loading && dataQuality.length === 0" description="暂无城市数据" :image-size="100" />
        <el-table v-else :data="dataQuality" border stripe v-loading="loading" style="width: 100%">
          <el-table-column prop="city_name" label="城市名称" width="150" />
          <el-table-column prop="data_count" label="数据条数" width="120" sortable>
            <template #default="{ row }">
              <span :style="{ color: row.data_count === 0 ? '#F56C6C' : '#606266' }">
                {{ row.data_count }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="latest_date" label="最新日期" width="120">
            <template #default="{ row }">
              <span v-if="row.latest_date">{{ row.latest_date }}</span>
              <span v-else style="color: #909399;">无数据</span>
            </template>
          </el-table-column>
          <el-table-column label="数据状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'good' ? 'success' : 'warning'">
                {{ row.status === 'good' ? '良好' : '需更新' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="days_since_last" label="距今天数" width="120">
            <template #default="{ row }">
              <span v-if="row.days_since_last !== null">{{ row.days_since_last }} 天</span>
              <span v-else style="color: #909399;">无数据</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250">
            <template #default="{ row }">
              <el-button 
                link 
                type="primary" 
                size="small" 
                @click="viewCityData(row.city_name)"
                :disabled="row.data_count === 0"
              >
                查看数据
              </el-button>
              <el-button 
                link 
                type="success" 
                size="small" 
                @click="handleTrainModel(row.city_name)"
                :disabled="row.data_count < 30"
                :loading="trainingCities.has(row.city_name)"
              >
                训练模型
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 历史数据图表 -->
    <el-card class="chart-card" v-if="selectedCity">
      <template #header>
        <div class="card-header">
          <span>{{ selectedCity }} - 最近两周数据趋势</span>
          <el-button link type="danger" @click="selectedCity = null">关闭</el-button>
        </div>
      </template>
      <div class="chart-wrapper" v-loading="chartLoading">
        <chart-box v-if="chartOption.xAxis.data.length > 0" :options="chartOption" />
        <el-empty v-else description="暂无数据" :image-size="100" />
      </div>
    </el-card>

    <!-- 数据列表 -->
    <el-card class="list-card" v-if="selectedCity">
      <template #header>
        <div class="card-header">
          <span>{{ selectedCity }} - 最近两周数据列表</span>
          <div>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="loadDailyData"
              style="margin-right: 10px;"
            />
            <el-button link type="primary" size="small" @click="resetToTwoWeeks">重置为最近两周</el-button>
            <el-button link type="danger" @click="selectedCity = null">关闭</el-button>
          </div>
        </div>
      </template>
      <el-table :data="dailyDataList" border stripe v-loading="listLoading" style="width: 100%">
        <el-table-column prop="date" label="日期" width="120" sortable />
        <el-table-column prop="confirmed" label="累计确诊" width="120" />
        <el-table-column prop="active" label="活跃病例" width="120" />
        <el-table-column prop="recovered" label="累计康复" width="120" />
        <el-table-column prop="deaths" label="累计死亡" width="120" />
        <el-table-column prop="severe" label="重症病例" width="120" />
      </el-table>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="totalRecords"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadDailyData"
        @current-change="loadDailyData"
        style="margin-top: 20px;"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Location, Document, DataAnalysis, Clock, Search } from '@element-plus/icons-vue';
import ChartBox from '@/components/ChartBox.vue';
import { getTrainingDataStatsAPI, getCitiesListAPI, getHistoricalDataAPI, getDailyDataListAPI, trainLstmModelAPI } from '@/api/index';
import { printTrainingInfo } from '@/utils/trainLogger';

const loading = ref(false);
const chartLoading = ref(false);
const listLoading = ref(false);
const stats = ref<any>({});
const dataQuality = ref<any[]>([]);
const searchKeyword = ref<string>('');
const selectedCity = ref<string | null>(null);
const dateRange = ref<[Date, Date] | null>(null);
const dailyDataList = ref<any[]>([]);
const currentPage = ref(1);
const pageSize = ref(20);
const totalRecords = ref(0);
const trainingCities = ref(new Set<string>());

// 图表配置
const chartOption = ref({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' }
  },
  legend: {
    data: ['累计确诊', '活跃病例', '累计康复', '累计死亡'],
    top: 10
  },
  grid: {
    left: '10%',
    right: '4%',
    bottom: '3%',
    top: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: []
  },
  yAxis: {
    type: 'value',
    name: '人数',
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
    }
  },
  series: [
    {
      name: '累计确诊',
      type: 'line',
      data: [],
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '活跃病例',
      type: 'line',
      data: [],
      itemStyle: { color: '#F56C6C' }
    },
    {
      name: '累计康复',
      type: 'line',
      data: [],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '累计死亡',
      type: 'line',
      data: [],
      itemStyle: { color: '#909399' }
    }
  ]
});

// 加载统计数据
const loadStats = async () => {
  loading.value = true;
  try {
    const res: any = await getTrainingDataStatsAPI();
    if (res.code === 200) {
      stats.value = res.data.summary || {};
    } else {
      ElMessage.error(res.msg || '加载统计数据失败');
    }
  } catch (error: any) {
    console.error('加载统计数据失败:', error);
    ElMessage.error('加载统计数据失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

// 加载城市列表（默认显示深圳、北京、上海，支持搜索）
const loadCities = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (searchKeyword.value) {
      params.search = searchKeyword.value;
    }
    const res: any = await getCitiesListAPI(undefined, params);
    console.log('城市列表API响应:', res);
    if (res.code === 200) {
      dataQuality.value = res.data || [];
      if (dataQuality.value.length === 0) {
        ElMessage.info(searchKeyword.value ? '未找到匹配的城市' : '暂无城市数据');
      }
    } else {
      ElMessage.error(res.msg || '加载城市数据失败');
      dataQuality.value = [];
    }
  } catch (error: any) {
    console.error('加载城市数据失败:', error);
    ElMessage.error('加载城市数据失败: ' + (error.message || '未知错误'));
    dataQuality.value = [];
  } finally {
    loading.value = false;
  }
};

// 搜索处理（防抖）
let searchTimer: any = null;
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  searchTimer = setTimeout(() => {
    loadCities();
  }, 300);
};

// 查看城市数据
const viewCityData = async (cityName: string) => {
  selectedCity.value = cityName;
  await loadChartData(cityName);
  await loadDailyData();
};

// 加载图表数据（只显示最近两周的数据）
const loadChartData = async (cityName: string) => {
  chartLoading.value = true;
  try {
    const res: any = await getHistoricalDataAPI(cityName, 14);
    console.log('图表数据响应:', res);
    
    if (res.code === 200 && res.data) {
      const dates = res.data.dates || [];
      const confirmed = res.data.confirmed || [];
      const active = res.data.active || [];
      const recovered = res.data.recovered || [];
      const deaths = res.data.deaths || [];
      
      console.log('解析后的数据:', { dates: dates.length, confirmed: confirmed.length, active: active.length });
      
      if (dates.length === 0) {
        ElMessage.warning('该城市暂无历史数据，请先导入数据');
        // 清空图表
        chartOption.value = {
          ...chartOption.value,
          xAxis: {
            ...chartOption.value.xAxis,
            data: []
          },
          series: [
            { ...chartOption.value.series[0], data: [] },
            { ...chartOption.value.series[1], data: [] },
            { ...chartOption.value.series[2], data: [] },
            { ...chartOption.value.series[3], data: [] }
          ]
        };
      } else {
        // 深度复制并更新图表配置
        chartOption.value = {
          tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
          },
          legend: {
            data: ['累计确诊', '活跃病例', '累计康复', '累计死亡'],
            top: 10
          },
          grid: {
            left: '10%',
            right: '4%',
            bottom: '3%',
            top: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates
          },
          yAxis: {
            type: 'value',
            name: '人数',
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
            }
          },
          series: [
            {
              name: '累计确诊',
              type: 'line',
              data: confirmed,
              itemStyle: { color: '#409EFF' }
            },
            {
              name: '活跃病例',
              type: 'line',
              data: active,
              itemStyle: { color: '#F56C6C' }
            },
            {
              name: '累计康复',
              type: 'line',
              data: recovered,
              itemStyle: { color: '#67C23A' }
            },
            {
              name: '累计死亡',
              type: 'line',
              data: deaths,
              itemStyle: { color: '#909399' }
            }
          ]
        };
      }
    } else {
      ElMessage.warning('获取数据失败');
    }
  } catch (error: any) {
    console.error('加载图表数据失败:', error);
    ElMessage.error('加载图表数据失败: ' + (error.message || '未知错误'));
  } finally {
    chartLoading.value = false;
  }
};

// 加载每日数据列表（默认显示最近两周）
const loadDailyData = async () => {
  if (!selectedCity.value) return;
  
  listLoading.value = true;
  try {
    // 如果没有选择日期范围，默认显示最近两周
    let startDate: string;
    let endDate: string;
    
    if (dateRange.value && dateRange.value.length === 2) {
      startDate = dateRange.value[0].toISOString().split('T')[0];
      endDate = dateRange.value[1].toISOString().split('T')[0];
    } else {
      // 默认最近两周
      const today = new Date();
      const twoWeeksAgo = new Date(today);
      twoWeeksAgo.setDate(today.getDate() - 13); // 14天包括今天
      endDate = today.toISOString().split('T')[0];
      startDate = twoWeeksAgo.toISOString().split('T')[0];
    }
    
    const params: any = {
      city_name: selectedCity.value,
      page: currentPage.value,
      page_size: pageSize.value,
      start_date: startDate,
      end_date: endDate
    };
    
    const res: any = await getDailyDataListAPI(params);
    if (res.code === 200) {
      dailyDataList.value = res.data.list;
      totalRecords.value = res.data.total;
    }
  } catch (error) {
    ElMessage.error('加载数据列表失败');
  } finally {
    listLoading.value = false;
  }
};

// 重置为最近两周
const resetToTwoWeeks = () => {
  dateRange.value = null;
  currentPage.value = 1;
  loadDailyData();
};

// 刷新数据
const refreshData = () => {
  loadStats();
  loadCities();
  if (selectedCity.value) {
    loadChartData(selectedCity.value);
    loadDailyData();
  }
};

// 训练LSTM模型
const handleTrainModel = async (cityName: string) => {
  if (trainingCities.value.has(cityName)) {
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要训练 "${cityName}" 的LSTM模型吗？\n训练可能需要几分钟时间，请耐心等待。`,
      '训练LSTM模型',
      {
        type: 'info',
        confirmButtonText: '开始训练',
        cancelButtonText: '取消'
      }
    );
    
    trainingCities.value.add(cityName);
    
    console.log(`\n🚀 开始训练 ${cityName} 的LSTM模型...`);
    ElMessage.info(`开始训练 ${cityName} 的LSTM模型，请查看控制台了解详细信息`);
    
    const trainParams = {
      city_name: cityName,
      epochs: 50,
      batch_size: 32,
      validation_split: 0.2,
      historical_days: 60
    };
    
    const res: any = await trainLstmModelAPI(trainParams);
    
    if (res.code === 200) {
      // 打印训练信息到控制台
      printTrainingInfo(res.data);
      
      ElMessage.success(`✅ ${cityName} 的LSTM模型训练成功！请查看控制台了解详细信息`);
    } else {
      console.error('训练失败:', res.msg);
      ElMessage.error(`训练失败: ${res.msg || '未知错误'}`);
    }
  } catch (error: any) {
    if (error === 'cancel') {
      // 用户取消
      return;
    }
    console.error('训练请求失败:', error);
    ElMessage.error(`训练请求失败: ${error.message || '未知错误'}`);
  } finally {
    trainingCities.value.delete(cityName);
  }
};

onMounted(() => {
  loadStats();
  loadCities();
});
</script>

<style scoped>
.data-monitor-page {
  padding: 20px;
  background: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.page-header p {
  margin: 0;
  color: #909399;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.date-range-card {
  margin-bottom: 20px;
}

.date-range-info {
  font-size: 14px;
  color: #606266;
}

.quality-card,
.chart-card,
.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-wrapper {
  height: 400px;
  width: 100%;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
}

/* 搜索区域样式 */
.search-section {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

/* 城市列表区域 */
.city-list-section {
  padding: 10px 0;
}
</style>

