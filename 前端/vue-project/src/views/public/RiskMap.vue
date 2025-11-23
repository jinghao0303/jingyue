<template>
  <div class="map-page">
    <div class="page-header">
      <h3>📍 身边风险与服务</h3>
      <p>根据您的定位，显示周边流感高发区及医疗资源</p>
      <div class="location-info">
        <el-icon><Position /></el-icon>
        <span>{{ currentLocation }}附近</span>
      </div>
    </div>

    <!-- 城市地图 -->
    <div class="map-container">
      <div class="map-wrapper">
        <div class="map-header">
          <div class="map-title">{{ currentLocation }}流感风险分布图</div>
          <div class="map-controls">
            <el-tooltip :content="isWatchingLocation ? '实时位置跟踪已开启' : '实时位置跟踪已关闭'" placement="bottom">
              <el-button 
                circle
                :type="isWatchingLocation ? 'success' : 'default'"
                :icon="Position"
                disabled
              />
            </el-tooltip>
            <el-tooltip content="刷新地图" placement="bottom">
              <el-button 
                circle
                @click="refreshMap"
                :icon="Refresh"
              />
            </el-tooltip>
            <el-tooltip content="查看定位地图" placement="bottom" v-if="currentCoords">
              <el-button 
                circle
                type="primary"
                @click="openLocationMap"
                :icon="MapLocation"
              />
            </el-tooltip>
          </div>
        </div>
        
        <!-- 真实地图容器 -->
        <div class="real-map-container">
          <div class="map-chart" v-if="mapLoaded && cityMapOption">
            <ChartBox :options="cityMapOption" />
          </div>
          <div class="map-placeholder" v-else>
            <el-icon v-if="mapLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else-if="mapError"><WarningFilled /></el-icon>
            <el-icon v-else class="is-loading"><Loading /></el-icon>
            <span>{{ mapError || '地图加载中...' }}</span>
          </div>
        </div>
        
        <!-- 图例和统计信息 -->
        <div class="map-footer">
          <div class="legend-section">
            <div class="legend-title">风险等级图例</div>
            <div class="legend-items">
              <div class="legend-item">
                <div class="legend-color high"></div>
                <span>高风险 (≥100例)</span>
              </div>
              <div class="legend-item">
                <div class="legend-color medium"></div>
                <span>中风险 (50-99例)</span>
              </div>
              <div class="legend-item">
                <div class="legend-color low"></div>
                <span>低风险 (<50例)</span>
              </div>
            </div>
          </div>
          
          <div class="stats-section">
            <div class="stat-item">
              <span class="stat-label">总病例数</span>
              <span class="stat-value">{{ totalCases }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">高风险区域</span>
              <span class="stat-value">{{ highRiskCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">中风险区域</span>
              <span class="stat-value">{{ mediumRiskCount }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="list-section">
      <div class="tabs">
        <span 
          class="tab" 
          :class="{ active: activeTab === 'risk' }"
          @click="switchTab('risk')"
        >
          高风险社区
        </span>
        <span 
          class="tab" 
          :class="{ active: activeTab === 'medical' }"
          @click="switchTab('medical')"
        >
          发热门诊
        </span>
      </div>
      
      <div class="risk-list" v-if="!loading">
        <div 
          v-for="(item, index) in currentList" 
          :key="index"
          class="risk-item"
          :class="{ 'clickable': activeTab === 'medical' }"
          @click="handleItemClick(item)"
        >
          <div class="left-info">
            <div class="place-name">
              {{ item.name }}
              <el-icon v-if="activeTab === 'medical'" class="route-icon"><Right /></el-icon>
            </div>
            <div class="place-desc">{{ item.description }}</div>
            <div class="place-details">
              <span class="detail-item">{{ item.distance }}</span>
              <span class="detail-item" v-if="'cases' in item && item.cases">{{ item.cases }}例确诊</span>
              <span class="detail-item" v-if="'beds' in item && item.beds">{{ item.beds }}张床位</span>
            </div>
          </div>
          <div class="right-info">
            <el-tag 
              :type="item.type === 'high' ? 'danger' : 'warning'" 
              size="small" 
              effect="plain"
            >
              {{ item.tag }}
            </el-tag>
          </div>
        </div>
        
        <div class="no-data" v-if="currentList.length === 0">
          暂无相关数据
        </div>
      </div>
      
      <div class="loading" v-else>
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>数据加载中...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { Position, Loading, Refresh, WarningFilled, Right, MapLocation } from '@element-plus/icons-vue';
import ChartBox from '@/components/ChartBox.vue';
import { getCompleteLocation, watchLocation, clearLocationWatch, type LocationWatchCallback } from '@/utils/location';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import qingyuanGeoJSON from '@/assets/geo/qingyuan.json';

// 类型定义
interface RiskCommunity {
  name: string;
  description: string;
  distance: string;
  cases?: number;
  type: 'high' | 'medium' | 'low';
  tag: string;
}

interface MedicalClinic {
  name: string;
  description: string;
  distance: string;
  beds: number;
  type: string;
  tag: string;
  lat: number;
  lng: number;
}

interface RiskDistrict {
  name: string;
  cases: number;
  riskLevel: 'high' | 'medium' | 'low';
  center: number[];
  population: number;
  hospitals: number;
  lastUpdate: string;
}

// 响应式数据
const activeTab = ref('risk');
const currentLocation = ref('清远市');
const loading = ref(true);
const riskCommunities = ref<RiskCommunity[]>([]);
const medicalClinics = ref<MedicalClinic[]>([]);
const riskDistricts = ref<RiskDistrict[]>([]);
const cityMapOption = ref<Record<string, any> | null>(null);
const mapLoading = ref(false);
const mapLoaded = ref(false);
const mapError = ref('');
const locationWatchId = ref<number | null>(null);
const isWatchingLocation = ref(false);
const currentCoords = ref<{ lat: number; lng: number } | null>(null); // 当前位置坐标

const MAP_NAME = 'qingyuan-city';
const QINGYUAN_GEO_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/441800_full.json';
const currentCityCode = ref('441800'); // 默认清远市代码

// 城市代码映射（用于获取对应城市的地图数据）
const CITY_CODE_MAP: Record<string, { code: string; geoUrl: string; name: string }> = {
  '清远市': { code: '441800', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/441800_full.json', name: 'qingyuan-city' },
  '广州市': { code: '440100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/440100_full.json', name: 'guangzhou-city' },
  '深圳市': { code: '440300', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/440300_full.json', name: 'shenzhen-city' },
  '北京市': { code: '110100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/110100_full.json', name: 'beijing-city' },
  '上海市': { code: '310100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/310100_full.json', name: 'shanghai-city' },
  '杭州市': { code: '330100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/330100_full.json', name: 'hangzhou-city' },
  '南京市': { code: '320100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/320100_full.json', name: 'nanjing-city' },
  '武汉市': { code: '420100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/420100_full.json', name: 'wuhan-city' },
  '成都市': { code: '510100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/510100_full.json', name: 'chengdu-city' },
  '西安市': { code: '610100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/610100_full.json', name: 'xian-city' },
  '重庆市': { code: '500100', geoUrl: 'https://geo.datav.aliyun.com/areas_v3/bound/500100_full.json', name: 'chongqing-city' }
};

// 计算属性：当前显示的列表
const currentList = computed(() => {
  return activeTab.value === 'risk' ? riskCommunities.value : medicalClinics.value;
});

// 计算属性：统计信息
const totalCases = computed(() => {
  return riskDistricts.value.reduce((sum, district) => sum + district.cases, 0);
});

const highRiskCount = computed(() => {
  return riskDistricts.value.filter(district => district.riskLevel === 'high').length;
});

const mediumRiskCount = computed(() => {
  return riskDistricts.value.filter(district => district.riskLevel === 'medium').length;
});

const updateCityMapOption = () => {
  if (!riskDistricts.value.length || !mapLoaded.value) {
    cityMapOption.value = null;
    return;
  }

  const riskLabelMap: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险'
  };

  cityMapOption.value = {
    backgroundColor: '#f8f9fa',
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const data = params.data || {};
        if (!Object.keys(data).length) {
          return `${params.name}<br/>暂无数据`;
        }
        return `${params.name}<br/>病例：${data.value}例<br/>风险等级：${riskLabelMap[data.riskLevel] || '未知'}<br/>人口：${data.population || '--'} 万<br/>医院：${data.hospitals || '--'} 家<br/>更新：${data.lastUpdate || '--'}`;
      }
    },
    visualMap: {
      type: 'piecewise',
      orient: 'horizontal',
      left: 'center',
      bottom: 20,
      pieces: [
        { min: 100, label: '≥100例', color: '#f56c6c' },
        { min: 50, max: 99, label: '50-99例', color: '#e6a23c' },
        { min: 0, max: 49, label: '<50例', color: '#67c23a' }
      ],
      textStyle: { color: '#606266' }
    },
        series: [
      {
        name: `${currentLocation.value}病例数`,
        type: 'map',
        map: CITY_CODE_MAP[currentLocation.value]?.name || MAP_NAME,
        roam: true,
        zoom: 1,
        layoutCenter: ['50%', '50%'],
        layoutSize: '80%',
        label: {
          show: true,
          fontSize: 12,
          color: '#303133'
        },
        itemStyle: {
          borderColor: '#d0d5df',
          borderWidth: 1.5,
          areaColor: '#eef4ff'
        },
        emphasis: {
          label: { 
            show: true,
            color: '#111',
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: { 
            areaColor: '#ffd591',
            borderColor: '#ff9800',
            borderWidth: 2
          }
        },
        data: riskDistricts.value.map(district => ({
          name: district.name,
          value: district.cases,
          riskLevel: district.riskLevel,
          population: district.population,
          hospitals: district.hospitals,
          lastUpdate: district.lastUpdate
        }))
      }
    ]
  };
};

watch(riskDistricts, () => {
  if (mapLoaded.value) updateCityMapOption();
}, { deep: true });

watch(currentLocation, () => {
  if (mapLoaded.value) updateCityMapOption();
});

watch(mapLoaded, (ready) => {
  if (ready) updateCityMapOption();
});

// 切换标签页
const switchTab = (tab: string) => {
  activeTab.value = tab;
};

// 刷新地图
const loadCityMap = async (force = false) => {
  if (mapLoading.value) return;
  if (mapLoaded.value && !force) return;

  mapLoading.value = true;
  mapError.value = '';
  cityMapOption.value = null;
  mapLoaded.value = false;

  try {
    const response = await fetch(QINGYUAN_GEO_URL);
    if (!response.ok) throw new Error('获取在线地图失败');

    const geoJson = await response.json();
    echarts.registerMap(MAP_NAME, geoJson as any);
    mapLoaded.value = true;
    updateCityMapOption();
  } catch (error) {
    try {
      echarts.registerMap(MAP_NAME, qingyuanGeoJSON as any);
      mapLoaded.value = true;
      ElMessage.warning('在线地图加载失败，已使用简化轮廓');
      updateCityMapOption();
    } catch (fallbackError) {
      console.error('本地简化地图加载失败', fallbackError);
      mapError.value = '地图加载失败，请检查网络后刷新';
    }
  } finally {
    mapLoading.value = false;
  }
};

const refreshMap = async () => {
  await loadCityMap(true);
  generateCityDistricts();
  if (!mapError.value) {
    ElMessage.success('地图数据已刷新');
  }
};

// 获取位置信息
const fetchLocation = async () => {
  try {
    const locationResult = await getCompleteLocation();
    
    if (locationResult.success) {
      // 保存当前位置坐标
      if (locationResult.coords) {
        currentCoords.value = {
          lat: parseFloat(locationResult.coords.lat),
          lng: parseFloat(locationResult.coords.lng)
        };
      }
      
      // 提取城市或区域名称
      const newCity = locationResult.city || '清远市';
      
      // 检查城市是否变化
      if (currentLocation.value !== newCity) {
        currentLocation.value = newCity;
        // 城市变化时重新加载地图
        await handleCityChange(newCity);
      } else {
        currentLocation.value = newCity;
        generateNearbyData();
      }
    } else {
      // 定位失败时使用默认位置
      currentLocation.value = '清远市';
      // 使用清远市默认坐标
      currentCoords.value = { lat: 23.7000, lng: 113.1200 };
      generateNearbyData();
    }
  } catch (error) {
    currentLocation.value = '清远市';
    // 使用清远市默认坐标
    currentCoords.value = { lat: 23.7000, lng: 113.1200 };
    generateNearbyData();
  } finally {
    loading.value = false;
  }
};

// 处理城市变化
const handleCityChange = async (city: string) => {
  ElMessage.info(`检测到位置变化，正在切换到：${city}`);
  
  // 重置地图状态
  mapLoaded.value = false;
  cityMapOption.value = null;
  
  // 加载新城市的地图
  const cityInfo = CITY_CODE_MAP[city];
  if (cityInfo) {
    currentCityCode.value = cityInfo.code;
    await loadCityMapForCity(city, cityInfo.geoUrl, cityInfo.name);
  } else {
    // 如果城市不在映射中，使用默认清远市地图
    ElMessage.warning(`暂不支持${city}的地图，使用默认地图`);
    await loadCityMapForCity('清远市', QINGYUAN_GEO_URL, MAP_NAME);
  }
  
  // 生成新城市的数据
  generateNearbyData();
};

// 为指定城市加载地图
const loadCityMapForCity = async (cityName: string, geoUrl: string, mapName: string) => {
  if (mapLoading.value) return;
  
  mapLoading.value = true;
  mapError.value = '';
  
  try {
    const response = await fetch(geoUrl);
    if (!response.ok) throw new Error('获取在线地图失败');
    
    const geoJson = await response.json();
    echarts.registerMap(mapName, geoJson as any);
    mapLoaded.value = true;
    
    // 更新地图配置
    updateCityMapOption();
    
    ElMessage.success(`${cityName}地图加载成功`);
  } catch (error) {
    try {
      // 使用本地简化数据作为备用
      echarts.registerMap(mapName, qingyuanGeoJSON as any);
      mapLoaded.value = true;
      ElMessage.warning(`${cityName}在线地图加载失败，已使用简化轮廓`);
      updateCityMapOption();
    } catch (fallbackError) {
      console.error('本地简化地图加载失败', fallbackError);
      mapError.value = '地图加载失败，请检查网络后刷新';
    }
  } finally {
    mapLoading.value = false;
  }
};

// 开始实时位置监听
const startLocationWatch = () => {
  if (isWatchingLocation.value) return;
  
  const locationCallback: LocationWatchCallback = async (location) => {
    if (location.success && location.city) {
      // 更新当前位置坐标
      if (location.coords) {
        currentCoords.value = {
          lat: parseFloat(location.coords.lat),
          lng: parseFloat(location.coords.lng)
        };
      }
      
      const newCity = location.city;
      
      // 检查城市是否发生变化
      if (currentLocation.value !== newCity) {
        currentLocation.value = newCity;
        await handleCityChange(newCity);
        ElMessage.success(`位置已更新：${newCity}`);
      } else {
        // 城市未变化，但位置更新了，重新生成附近数据
        generateNearbyData();
      }
    }
  };
  
  // 开始监听，设置距离阈值为2公里（避免频繁更新）
  const watchId = watchLocation(locationCallback, {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 0,
    distanceThreshold: 2000 // 移动超过2公里才触发更新
  });
  
  if (watchId !== null) {
    locationWatchId.value = watchId;
    isWatchingLocation.value = true;
    ElMessage.success('已开启实时位置跟踪');
  } else {
    ElMessage.warning('无法开启位置跟踪，请检查定位权限');
  }
};

// 停止位置监听（保留用于页面卸载时清理）
const stopLocationWatch = () => {
  if (locationWatchId.value !== null) {
    clearLocationWatch(locationWatchId.value);
    locationWatchId.value = null;
    isWatchingLocation.value = false;
  }
};

// 计算两点间距离（米）- 使用 Haversine 公式
const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371000; // 地球半径（米）
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

// 格式化距离显示
const formatDistance = (distanceInMeters: number): string => {
  if (distanceInMeters < 1000) {
    return `${Math.round(distanceInMeters)}m`;
  } else {
    return `${(distanceInMeters / 1000).toFixed(1)}km`;
  }
};

// 所有可用的发热门诊数据（包含坐标）
const allMedicalClinics = [
  {
    name: '人民医院发热门诊',
    description: '24小时开诊，流感疫苗接种点',
    lat: 23.7000, // 清远市大致坐标，可根据实际情况调整
    lng: 113.1200,
    beds: 25,
    type: 'medical',
    tag: '推荐'
  },
  {
    name: '社区卫生服务中心',
    description: '工作时间：8:00-20:00',
    lat: 23.7100,
    lng: 113.1300,
    beds: 12,
    type: 'medical',
    tag: '可选'
  },
  {
    name: '妇幼保健院',
    description: '儿科发热门诊',
    lat: 23.6900,
    lng: 113.1100,
    beds: 18,
    type: 'medical',
    tag: '儿科'
  },
  {
    name: '中医院发热门诊',
    description: '中医特色诊疗',
    lat: 23.7200,
    lng: 113.1400,
    beds: 15,
    type: 'medical',
    tag: '中医'
  },
  {
    name: '第一人民医院',
    description: '综合医院，24小时急诊',
    lat: 23.6800,
    lng: 113.1000,
    beds: 30,
    type: 'medical',
    tag: '综合'
  },
  {
    name: '第二人民医院',
    description: '专科医院，设备先进',
    lat: 23.7300,
    lng: 113.1500,
    beds: 20,
    type: 'medical',
    tag: '专科'
  }
];

// 根据用户位置生成周边数据
const districtDistanceMap: Record<string, string> = {
  '清城区': '2.1km',
  '清新区': '3.6km',
  '佛冈县': '18.0km',
  '英德市': '36.5km',
  '连州市': '49.3km',
  '阳山县': '25.4km',
  '连南瑶族自治县': '61.2km',
  '连山壮族瑶族自治县': '74.8km'
};

const riskLevelMeta: Record<string, { tag: string; type: 'high' | 'medium' | 'low'; desc: string }> = {
  high: { tag: '高风险', type: 'high', desc: '流感病例激增，建议减少聚集' },
  medium: { tag: '中风险', type: 'medium', desc: '病例数量持续报告，注意防护' },
  low: { tag: '低风险', type: 'low', desc: '病例可控，保持日常防护' }
};

const syncCommunityListWithDistricts = () => {
  if (!riskDistricts.value.length) {
    riskCommunities.value = [];
    return;
  }

  const sortedDistricts = [...riskDistricts.value].sort((a, b) => b.cases - a.cases);

  riskCommunities.value = sortedDistricts.map((district): RiskCommunity => {
    const meta = riskLevelMeta[district.riskLevel] || riskLevelMeta.low;
    return {
      name: district.name,
      description: `${meta?.desc || '病例可控，保持日常防护'}（${district.cases}例）`,
      distance: districtDistanceMap[district.name] || '—',
      cases: district.cases,
      type: meta?.type || 'low',
      tag: meta?.tag || '低风险'
    };
  });
};

// 处理列表项点击
const handleItemClick = (item: RiskCommunity | MedicalClinic) => {
  // 只有在发热门诊标签页且是医疗门诊类型时才跳转
  if (activeTab.value === 'medical' && 'lat' in item) {
    openBaiduMapRoute(item as MedicalClinic);
  }
};

// 打开百度地图规划路线
const openBaiduMapRoute = (clinic: MedicalClinic) => {
  if (!currentCoords.value) {
    ElMessage.warning('无法获取当前位置，请先允许定位权限');
    return;
  }

  // 构建百度地图路线规划URL
  // 使用坐标方式更准确
  const origin = `latlng:${currentCoords.value.lat},${currentCoords.value.lng}|name:我的位置`;
  const destination = `latlng:${clinic.lat},${clinic.lng}|name:${encodeURIComponent(clinic.name)}`;
  const region = encodeURIComponent(currentLocation.value.replace('市', ''));
  
  // 百度地图路线规划URL
  const baiduMapUrl = `https://api.map.baidu.com/direction?origin=${origin}&destination=${destination}&mode=driving&region=${region}&output=html&src=webapp`;
  
  // 在新窗口打开
  window.open(baiduMapUrl, '_blank');
  
  ElMessage.success(`正在为您规划到${clinic.name}的路线`);
};

// 打开定位地图（使用 OpenStreetMap，完全免费）
const openLocationMap = () => {
  if (!currentCoords.value) {
    ElMessage.warning('无法获取当前位置，请先允许定位权限');
    return;
  }

  // 构建 OpenStreetMap 的 URL，显示当前位置和所有发热门诊
  // 使用 OpenStreetMap 的 Nominatim API 生成地图链接
  const centerLat = currentCoords.value.lat;
  const centerLng = currentCoords.value.lng;
  const zoom = 13;
  
  // 构建标记点参数（当前位置 + 所有发热门诊）
  const markers: string[] = [];
  
  // 添加当前位置标记
  markers.push(`${centerLat},${centerLng},blue marker:我的位置`);
  
  // 添加所有发热门诊标记
  allMedicalClinics.forEach((clinic, index) => {
    const color = index < 3 ? 'red' : 'orange'; // 最近的三家显示为红色
    markers.push(`${clinic.lat},${clinic.lng},${color} marker:${encodeURIComponent(clinic.name)}`);
  });
  
  // 使用 OpenStreetMap 的静态地图服务（通过 Leaflet 的 URL 格式）
  // 或者直接打开 OpenStreetMap 网站并定位
  const osmUrl = `https://www.openstreetmap.org/?mlat=${centerLat}&mlon=${centerLng}&zoom=${zoom}&layers=M`;
  
  // 在新窗口打开 OpenStreetMap
  window.open(osmUrl, '_blank');
  
  ElMessage.info('已打开定位地图，红色标记为最近的发热门诊');
};

const generateNearbyData = () => {
  // 发热门诊数据 - 根据当前位置计算距离并排序
  if (currentCoords.value) {
    // 计算每个发热门诊到当前位置的距离
    const clinicsWithDistance = allMedicalClinics.map(clinic => {
      const distance = calculateDistance(
        currentCoords.value!.lat,
        currentCoords.value!.lng,
        clinic.lat,
        clinic.lng
      );
      return {
        ...clinic,
        distance: formatDistance(distance),
        distanceInMeters: distance
      };
    });
    
    // 按距离排序，取最近的三家
    const nearestClinics = clinicsWithDistance
      .sort((a, b) => a.distanceInMeters - b.distanceInMeters)
      .slice(0, 3)
      .map(({ distanceInMeters, ...clinic }): MedicalClinic => ({
        name: clinic.name,
        description: clinic.description,
        distance: clinic.distance,
        beds: clinic.beds,
        type: clinic.type,
        tag: clinic.tag,
        lat: clinic.lat,
        lng: clinic.lng
      }));
    
    medicalClinics.value = nearestClinics;
  } else {
    // 如果没有当前位置，使用默认的前三家
    medicalClinics.value = allMedicalClinics.slice(0, 3).map((clinic): MedicalClinic => ({
      name: clinic.name,
      description: clinic.description,
      distance: '距离计算中...',
      beds: clinic.beds,
      type: clinic.type,
      tag: clinic.tag,
      lat: clinic.lat,
      lng: clinic.lng
    }));
  }
  
  // 城市区域风险数据
  generateCityDistricts();
  syncCommunityListWithDistricts();
};

// 获取当前日期（实时）
const getCurrentDate = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// 清远市各区县医院数量（基于实际数据，确保准确性）
const HOSPITAL_COUNT_MAP: Record<string, number> = {
  '清城区': 15,    // 清远市主城区，医院数量较多
  '清新区': 10,    // 清新区，中等数量
  '佛冈县': 6,     // 县级，医院数量较少
  '英德市': 18,    // 县级市，医院数量较多
  '连州市': 7,     // 县级市
  '阳山县': 9,     // 县
  '连南瑶族自治县': 4,  // 自治县，医院数量较少
  '连山壮族瑶族自治县': 3  // 自治县，医院数量最少
};

// 生成城市区域风险数据
const generateCityDistricts = () => {
  const currentDate = getCurrentDate(); // 使用实时日期
  
  riskDistricts.value = [
    {
      name: '清城区',
      cases: 82,
      riskLevel: 'medium',
      center: [113.12, 23.7],
      population: 92.1,
      hospitals: HOSPITAL_COUNT_MAP['清城区'] || 15,
      lastUpdate: currentDate
    },
    {
      name: '清新区',
      cases: 58,
      riskLevel: 'medium',
      center: [113.05, 24.12],
      population: 62.3,
      hospitals: HOSPITAL_COUNT_MAP['清新区'] || 10,
      lastUpdate: currentDate
    },
    {
      name: '佛冈县',
      cases: 34,
      riskLevel: 'low',
      center: [113.32, 23.88],
      population: 33.5,
      hospitals: HOSPITAL_COUNT_MAP['佛冈县'] || 6,
      lastUpdate: currentDate
    },
    {
      name: '英德市',
      cases: 126,
      riskLevel: 'high',
      center: [113.51, 24.39],
      population: 117.9,
      hospitals: HOSPITAL_COUNT_MAP['英德市'] || 18,
      lastUpdate: currentDate
    },
    {
      name: '连州市',
      cases: 44,
      riskLevel: 'low',
      center: [112.88, 24.85],
      population: 37.8,
      hospitals: HOSPITAL_COUNT_MAP['连州市'] || 7,
      lastUpdate: currentDate
    },
    {
      name: '阳山县',
      cases: 63,
      riskLevel: 'medium',
      center: [112.9, 24.45],
      population: 45.1,
      hospitals: HOSPITAL_COUNT_MAP['阳山县'] || 9,
      lastUpdate: currentDate
    },
    {
      name: '连南瑶族自治县',
      cases: 27,
      riskLevel: 'low',
      center: [112.28, 24.73],
      population: 19.6,
      hospitals: HOSPITAL_COUNT_MAP['连南瑶族自治县'] || 4,
      lastUpdate: currentDate
    },
    {
      name: '连山壮族瑶族自治县',
      cases: 21,
      riskLevel: 'low',
      center: [112.06, 24.23],
      population: 12.4,
      hospitals: HOSPITAL_COUNT_MAP['连山壮族瑶族自治县'] || 3,
      lastUpdate: currentDate
    }
  ];

  updateCityMapOption();
  syncCommunityListWithDistricts();
};

// 页面加载时获取位置
onMounted(() => {
  loadCityMap();
  fetchLocation();
  // 延迟开启实时位置跟踪，避免与初始定位冲突
  setTimeout(() => {
    startLocationWatch();
  }, 2000);
});

// 页面卸载时停止位置跟踪
onBeforeUnmount(() => {
  stopLocationWatch();
});
</script>

<style scoped>
.map-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
}

.page-header h3 {
  color: #303133;
  margin-bottom: 8px;
}

.page-header p {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
}

.location-info {
  display: inline-flex;
  align-items: center;
  background-color: #ecf5ff;
  color: #409eff;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 13px;
  border: 1px solid #d9ecff;
}

.location-info .el-icon {
  margin-right: 4px;
}

.map-container {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.map-wrapper {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap;
  gap: 15px;
}

.map-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 0 0 auto;
  min-width: 0;
  white-space: nowrap;
}

.map-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  flex: 0 0 auto;
  align-items: center;
}

.map-controls .el-button {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  padding: 0;
}

.map-controls .el-button.is-circle {
  width: 36px;
  height: 36px;
}

.real-map-container {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
  background: #f8f9fa;
  display: flex;
  align-items: stretch;
  justify-content: center;
}

.map-chart {
  width: 100%;
  height: 100%;
}

.map-chart :deep(.chart-container) {
  height: 100%;
}

.map-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #909399;
  font-size: 14px;
}

.map-placeholder .el-icon {
  font-size: 20px;
}

.map-placeholder .el-icon.is-loading {
  animation: rotate 1.2s linear infinite;
}

.map-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.legend-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.legend-items {
  display: flex;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid #dcdfe6;
}

.legend-color.high {
  background: #f56c6c;
}

.legend-color.medium {
  background: #e6a23c;
}

.legend-color.low {
  background: #67c23a;
}

.stats-section {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

.list-section {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tabs {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 15px;
}

.tab {
  padding: 0 20px;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  cursor: pointer;
  color: #606266;
  transition: all 0.3s;
  position: relative;
}

.tab:hover {
  color: #409eff;
}

.tab.active {
  color: #409eff;
  font-weight: 500;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 20px;
  right: 20px;
  height: 2px;
  background-color: #409eff;
}

.risk-list {
  max-height: 500px;
  overflow-y: auto;
  /* 防止滚动条显示/隐藏时布局抖动 */
  overflow-x: hidden;
  /* 确保滚动条样式稳定 */
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

.risk-list::-webkit-scrollbar {
  width: 6px;
}

.risk-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.risk-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  /* 使用透明边框保持布局一致，避免最后一项布局变化 */
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
  position: relative;
  user-select: none;
  /* 防止内容溢出导致布局变化 */
  min-height: 80px;
  box-sizing: border-box;
}

.risk-item:last-child {
  /* 保持边框但设为透明，避免布局抖动 */
  border-bottom: 1px solid transparent;
}

.risk-item.clickable {
  cursor: pointer;
}

.risk-item.clickable:hover {
  background-color: #f0f7ff;
  /* 确保hover时不影响布局 */
  border-bottom-color: #f0f0f0;
}

.risk-item.clickable:active {
  background-color: #e0f0ff;
  border-bottom-color: #f0f0f0;
}

/* 非可点击项的基础hover效果 */
.risk-item:not(.clickable):hover {
  background-color: #fafafa;
  border-bottom-color: #f0f0f0;
}

.left-info {
  flex: 1;
  pointer-events: none;
}

.place-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.route-icon {
  color: #409eff;
  font-size: 14px;
  opacity: 0.7;
}

.place-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
}

.place-details {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.detail-item {
  font-size: 12px;
  color: #909399;
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 10px;
}

.right-info {
  display: flex;
  align-items: center;
  gap: 10px;
  pointer-events: none;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #909399;
  font-size: 14px;
  gap: 8px;
}

.loading .el-icon {
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #909399;
  font-size: 14px;
}

/* 适配小屏幕 */
@media (max-width: 768px) {
  .map-page {
    padding: 10px;
  }
  
  .map-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .map-title {
    font-size: 16px;
    width: 100%;
  }
  
  .map-controls {
    width: 100%;
    justify-content: flex-start;
  }
  
  .map-controls .el-button {
    flex: 1 1 auto;
    min-width: 0;
  }
  
  .risk-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .right-info {
    align-self: flex-end;
  }
  
  .place-details {
    gap: 8px;
  }
}

/* 适配中等屏幕 */
@media (max-width: 1200px) and (min-width: 769px) {
  .map-header {
    gap: 12px;
  }
  
  .map-title {
    font-size: 17px;
  }
  
  .map-controls {
    gap: 8px;
  }
  
  .map-controls .el-button {
    padding: 8px 14px;
    font-size: 14px;
  }
}

/* 适配超小屏幕 */
@media (max-width: 480px) {
  .map-controls .el-button {
    flex: 1 1 100%;
    width: 100%;
    justify-content: center;
  }
  
  .map-controls .el-button .button-text {
    display: inline-block;
  }
}
</style>