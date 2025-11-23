// 定位工具类 - 统一管理定位相关功能

// 定位配置
interface LocationConfig {
  timeout: number;
  enableHighAccuracy: boolean;
  maximumAge: number;
}

// 城市信息
interface CityInfo {
  name: string;
  province: string;
  lat: number;
  lng: number;
  threshold: number;
}

// 定位配置
const LOCATION_CONFIG: LocationConfig = {
  timeout: 10000, // 10秒超时
  enableHighAccuracy: true, // 启用高精度
  maximumAge: 5 * 60 * 1000 // 5分钟缓存
};

// 中国主要城市数据库
const CITY_DATABASE: CityInfo[] = [
  { name: '北京市', province: '北京市', lat: 39.9042, lng: 116.4074, threshold: 0.5 },
  { name: '上海市', province: '上海市', lat: 31.2304, lng: 121.4737, threshold: 0.5 },
  { name: '广州市', province: '广东省', lat: 23.1291, lng: 113.2644, threshold: 0.3 },
  { name: '深圳市', province: '广东省', lat: 22.5431, lng: 114.0579, threshold: 0.3 },
  { name: '杭州市', province: '浙江省', lat: 30.2741, lng: 120.1551, threshold: 0.4 },
  { name: '南京市', province: '江苏省', lat: 32.0603, lng: 118.7969, threshold: 0.4 },
  { name: '武汉市', province: '湖北省', lat: 30.5928, lng: 114.3055, threshold: 0.5 },
  { name: '成都市', province: '四川省', lat: 30.5728, lng: 104.0668, threshold: 0.5 },
  { name: '西安市', province: '陕西省', lat: 34.3416, lng: 108.9398, threshold: 0.5 },
  { name: '重庆市', province: '重庆市', lat: 29.5630, lng: 106.5516, threshold: 1.0 }
];

// 免费定位API列表（按优先级排序）
const LOCATION_APIS = [
  {
    name: 'BigDataCloud',
    url: (lat: string, lng: string) => 
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=zh`,
    parser: (data: any) => {
      if (!data.locality) return null;
      return {
        city: data.city || data.locality,
        province: data.principalSubdivision || ''
      };
    }
  },
  {
    name: 'GeocodeXYZ',
    url: (lat: string, lng: string) => 
      `https://geocode.xyz/${lat},${lng}?json=1&auth=your-free-key`,
    parser: (data: any) => {
      if (!data.city) return null;
      return {
        city: data.city,
        province: data.state || data.prov || ''
      };
    }
  },
  {
    name: 'OpenStreetMap',
    url: (lat: string, lng: string) => 
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&accept-language=zh`,
    parser: (data: any) => {
      if (!data.address) return null;
      const address = data.address;
      return {
        city: address.city || address.town || address.county || address.state,
        province: address.state || address.province || ''
      };
    }
  }
];

/**
 * 获取浏览器GPS定位
 */
export const getGPSLocation = (): Promise<{lat: number, lng: number}> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('浏览器不支持定位功能'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
      },
      (error) => {
        let errorMsg = '定位失败';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg = '用户拒绝定位权限';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMsg = '无法获取位置信息';
            break;
          case error.TIMEOUT:
            errorMsg = '定位请求超时';
            break;
        }
        reject(new Error(errorMsg));
      },
      LOCATION_CONFIG
    );
  });
};

/**
 * 通过坐标获取城市信息
 */
export const getCityFromCoordinates = async (lat: number, lng: number): Promise<{city: string, province: string}> => {
  const latStr = lat.toFixed(6);
  const lngStr = lng.toFixed(6);

  // 尝试使用API获取城市信息
  for (const api of LOCATION_APIS) {
    try {
      const response = await fetch(api.url(latStr, lngStr));
      const data = await response.json();
      const result = api.parser(data);
      
      if (result && result.city) {
        return result;
      }
    } catch (error) {
      console.warn(`${api.name} API调用失败:`, error);
    }
  }

  // 如果API都失败，使用本地数据库智能推断
  return smartGeoCheck(lat, lng);
};

/**
 * 智能备用方案：基于中国主要城市经纬度数据库进行智能匹配
 */
const smartGeoCheck = (lat: number, lng: number): {city: string, province: string} => {
  // 计算距离并找到最近的城市
  let nearestCity: CityInfo | null = null;
  let minDistance = Infinity;
  
  for (const city of CITY_DATABASE) {
    const distance = Math.sqrt(Math.pow(lat - city.lat, 2) + Math.pow(lng - city.lng, 2));
    if (distance < minDistance) {
      minDistance = distance;
      nearestCity = city;
    }
  }
  
  // 如果距离在阈值范围内，认为是该城市
  if (nearestCity && minDistance <= nearestCity.threshold) {
    return {
      city: nearestCity.name,
      province: nearestCity.province
    };
  }
  
  // 使用省级区域判断
  if (lat > 21 && lat < 26 && lng > 108 && lng < 118) {
    return { city: '华南地区', province: '华南' };
  } else if (lat > 28 && lat < 35 && lng > 115 && lng < 123) {
    return { city: '华东地区', province: '华东' };
  } else if (lat > 39 && lat < 42 && lng > 115 && lng < 118) {
    return { city: '华北地区', province: '华北' };
  }
  
  return { city: '未知区域', province: '未知' };
};

/**
 * 完整的定位流程
 */
export const getCompleteLocation = async () => {
  try {
    // 1. 获取GPS坐标
    const coords = await getGPSLocation();
    
    // 2. 获取城市信息
    const cityInfo = await getCityFromCoordinates(coords.lat, coords.lng);
    
    return {
      success: true,
      coords: {
        lat: coords.lat.toFixed(6),
        lng: coords.lng.toFixed(6)
      },
      city: cityInfo.city,
      province: cityInfo.province,
      fullAddress: cityInfo.province ? `${cityInfo.province}·${cityInfo.city}` : cityInfo.city
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '定位失败',
      coords: null,
      city: '定位失败',
      province: '',
      fullAddress: '定位失败'
    };
  }
};

/**
 * 实时位置监听回调函数类型
 */
export type LocationWatchCallback = (location: {
  success: boolean;
  coords: { lat: string; lng: string } | null;
  city: string;
  province: string;
  fullAddress: string;
  error?: string;
}) => void;

/**
 * 开始实时位置监听
 * @param callback 位置变化时的回调函数
 * @param options 监听选项
 * @returns 返回 watchId，用于停止监听
 */
export const watchLocation = (
  callback: LocationWatchCallback,
  options?: {
    enableHighAccuracy?: boolean;
    timeout?: number;
    maximumAge?: number;
    distanceThreshold?: number; // 距离阈值（米），超过此距离才触发回调
  }
): number | null => {
  if (!navigator.geolocation) {
    callback({
      success: false,
      error: '浏览器不支持定位功能',
      coords: null,
      city: '定位失败',
      province: '',
      fullAddress: '定位失败'
    });
    return null;
  }

  const config = {
    enableHighAccuracy: options?.enableHighAccuracy ?? true,
    timeout: options?.timeout ?? 10000,
    maximumAge: options?.maximumAge ?? 0 // 实时监听不使用缓存
  };

  const distanceThreshold = options?.distanceThreshold ?? 1000; // 默认1公里
  let lastCoords: { lat: number; lng: number; city: string } | null = null;

  // 计算两点间距离（米）
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

  const watchId = navigator.geolocation.watchPosition(
    async (position) => {
      const newCoords = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };

      // 检查距离是否超过阈值
      if (lastCoords) {
        const distance = calculateDistance(
          lastCoords.lat,
          lastCoords.lng,
          newCoords.lat,
          newCoords.lng
        );
        
        // 如果距离变化不大，不触发回调（避免频繁更新）
        if (distance < distanceThreshold) {
          return;
        }
      }

      try {
        // 获取城市信息
        const cityInfo = await getCityFromCoordinates(newCoords.lat, newCoords.lng);
        const newCity = cityInfo.city;

        // 如果城市发生变化，或者首次定位，触发回调
        if (!lastCoords || lastCoords.city !== newCity) {
          lastCoords = {
            lat: newCoords.lat,
            lng: newCoords.lng,
            city: newCity
          };

          callback({
            success: true,
            coords: {
              lat: newCoords.lat.toFixed(6),
              lng: newCoords.lng.toFixed(6)
            },
            city: cityInfo.city,
            province: cityInfo.province,
            fullAddress: cityInfo.province ? `${cityInfo.province}·${cityInfo.city}` : cityInfo.city
          });
        } else {
          // 城市未变化，但位置有显著移动，更新坐标
          lastCoords = {
            lat: newCoords.lat,
            lng: newCoords.lng,
            city: newCity
          };
        }
      } catch (error) {
        callback({
          success: false,
          error: error instanceof Error ? error.message : '获取城市信息失败',
          coords: {
            lat: newCoords.lat.toFixed(6),
            lng: newCoords.lng.toFixed(6)
          },
          city: '未知',
          province: '',
          fullAddress: '未知'
        });
      }
    },
    (error) => {
      let errorMsg = '定位失败';
      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorMsg = '用户拒绝定位权限';
          break;
        case error.POSITION_UNAVAILABLE:
          errorMsg = '无法获取位置信息';
          break;
        case error.TIMEOUT:
          errorMsg = '定位请求超时';
          break;
      }
      callback({
        success: false,
        error: errorMsg,
        coords: null,
        city: '定位失败',
        province: '',
        fullAddress: '定位失败'
      });
    },
    config
  );

  return watchId;
};

/**
 * 停止位置监听
 * @param watchId 监听ID
 */
export const clearLocationWatch = (watchId: number | null): void => {
  if (watchId !== null && navigator.geolocation) {
    navigator.geolocation.clearWatch(watchId);
  }
};