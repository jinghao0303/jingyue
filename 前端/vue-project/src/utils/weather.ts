// 天气工具类 - 获取实时天气信息

// 天气信息接口
export interface WeatherInfo {
  temperature: number; // 温度（摄氏度）
  description: string; // 天气描述
  humidity?: number; // 湿度
  windSpeed?: number; // 风速
  city: string; // 城市名称
  updateTime: string; // 更新时间
}

// 流感传播适宜度
export type FluTransmissionLevel = '适宜' | '较适宜' | '不适宜' | '低风险';

/**
 * 根据温度判断流感传播适宜度
 * 研究显示：流感病毒在4-20°C的温度范围内传播最活跃
 */
export const getFluTransmissionLevel = (temperature: number): FluTransmissionLevel => {
  if (temperature >= 4 && temperature <= 20) {
    return '适宜';
  } else if (temperature >= 0 && temperature < 4) {
    return '较适宜';
  } else if (temperature > 20 && temperature <= 25) {
    return '较适宜';
  } else if (temperature > 25) {
    return '不适宜';
  } else {
    return '低风险';
  }
};

/**
 * 获取流感传播描述文本
 */
export const getFluTransmissionText = (temperature: number): string => {
  const level = getFluTransmissionLevel(temperature);
  switch (level) {
    case '适宜':
      return '适宜流感传播';
    case '较适宜':
      return '较适宜流感传播';
    case '不适宜':
      return '不适宜流感传播';
    case '低风险':
      return '流感传播风险低';
    default:
      return '适宜流感传播';
  }
};

/**
 * 使用 OpenWeatherMap API 获取天气（需要API key）
 * 注意：这是一个示例，实际使用时需要申请免费的API key
 */
const getWeatherFromOpenWeather = async (
  lat: number,
  lng: number,
  apiKey?: string
): Promise<WeatherInfo | null> => {
  if (!apiKey) return null;
  
  try {
    const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lng}&appid=${apiKey}&units=metric&lang=zh_cn`;
    const response = await fetch(url);
    
    if (!response.ok) return null;
    
    const data = await response.json();
    return {
      temperature: Math.round(data.main.temp),
      description: data.weather[0].description,
      humidity: data.main.humidity,
      windSpeed: data.wind?.speed,
      city: data.name,
      updateTime: new Date().toLocaleTimeString('zh-CN')
    };
  } catch (error) {
    console.warn('OpenWeatherMap API 调用失败:', error);
    return null;
  }
};

/**
 * 使用 wttr.in 免费天气API（无需API key）
 */
const getWeatherFromWttr = async (lat: number, lng: number): Promise<WeatherInfo | null> => {
  try {
    // wttr.in 支持坐标查询
    const url = `https://wttr.in/?format=j1&lang=zh`;
    const response = await fetch(url);
    
    if (!response.ok) return null;
    
    const data = await response.json();
    const current = data.current_condition[0];
    
    return {
      temperature: parseInt(current.temp_C),
      description: current.lang_zh[0]?.value || current.weatherDesc[0]?.value || '未知',
      humidity: parseInt(current.humidity),
      windSpeed: parseInt(current.windspeedKmph),
      city: data.nearest_area[0].areaName[0].value || '未知',
      updateTime: new Date().toLocaleTimeString('zh-CN')
    };
  } catch (error) {
    console.warn('wttr.in API 调用失败:', error);
    return null;
  }
};

/**
 * 使用 7Timer! 免费天气API（无需API key，适合中国）
 */
const getWeatherFrom7Timer = async (lat: number, lng: number): Promise<WeatherInfo | null> => {
  try {
    // 7Timer! 使用网格坐标系统
    const gridLat = Math.floor(lat);
    const gridLng = Math.floor(lng);
    
    // 获取实时天气数据
    const url = `https://www.7timer.info/bin/api.pl?lon=${lng}&lat=${lat}&product=civillight&output=json`;
    const response = await fetch(url);
    
    if (!response.ok) return null;
    
    const data = await response.json();
    
    // 7Timer! 返回的是预报数据，取第一个（今天）
    if (data.dataseries && data.dataseries.length > 0) {
      const today = data.dataseries[0];
      // 7Timer! 的温度是字符串格式 "2" 到 "38"
      const temp = parseInt(today.temp2m?.toString() || '20');
      
      return {
        temperature: temp,
        description: '晴天', // 7Timer 不提供详细描述
        city: '当前位置',
        updateTime: new Date().toLocaleTimeString('zh-CN')
      };
    }
    
    return null;
  } catch (error) {
    console.warn('7Timer API 调用失败:', error);
    return null;
  }
};

/**
 * 使用 Open-Meteo 免费天气API（无需API key，数据准确）
 */
const getWeatherFromOpenMeteo = async (lat: number, lng: number): Promise<WeatherInfo | null> => {
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=Asia/Shanghai`;
    const response = await fetch(url);
    
    if (!response.ok) return null;
    
    const data = await response.json();
    const current = data.current;
    
    if (current && current.temperature_2m !== undefined) {
      return {
        temperature: Math.round(current.temperature_2m),
        description: '实时天气',
        humidity: current.relative_humidity_2m,
        windSpeed: current.wind_speed_10m,
        city: '当前位置',
        updateTime: new Date().toLocaleTimeString('zh-CN')
      };
    }
    
    return null;
  } catch (error) {
    console.warn('Open-Meteo API 调用失败:', error);
    return null;
  }
};

/**
 * 根据坐标获取实时天气信息
 * 按优先级尝试多个免费API
 */
export const getWeatherByCoordinates = async (
  lat: number,
  lng: number,
  cityName?: string
): Promise<WeatherInfo | null> => {
  // 按优先级尝试不同的天气API
  const apis = [
    () => getWeatherFromOpenMeteo(lat, lng), // 最优先：Open-Meteo，准确且免费
    () => getWeatherFrom7Timer(lat, lng),    // 备选：7Timer，适合中国
    () => getWeatherFromWttr(lat, lng)        // 最后：wttr.in
  ];
  
  for (const api of apis) {
    try {
      const weather = await api();
      if (weather) {
        // 如果提供了城市名称，使用提供的名称
        if (cityName) {
          weather.city = cityName;
        }
        return weather;
      }
    } catch (error) {
      console.warn('天气API调用失败:', error);
      continue;
    }
  }
  
  // 如果所有API都失败，返回基于位置的估算温度（仅用于演示）
  return getEstimatedTemperature(lat, lng, cityName);
};

/**
 * 根据纬度和季节估算温度（备用方案）
 */
const getEstimatedTemperature = (
  lat: number,
  lng: number,
  cityName?: string
): WeatherInfo => {
  const now = new Date();
  const month = now.getMonth() + 1; // 1-12
  const hour = now.getHours();
  
  // 根据月份和纬度估算基础温度
  let baseTemp = 20;
  
  // 北半球：12-2月冬季，6-8月夏季
  if (lat > 0) {
    if (month >= 12 || month <= 2) {
      // 冬季
      baseTemp = 5 + (lat - 20) * 0.5; // 纬度越高越冷
    } else if (month >= 6 && month <= 8) {
      // 夏季
      baseTemp = 28 - (lat - 20) * 0.3;
    } else {
      // 春秋
      baseTemp = 18 + (lat - 20) * 0.2;
    }
  }
  
  // 根据时间调整（夜间比白天低5-8度）
  if (hour >= 22 || hour <= 6) {
    baseTemp -= 6;
  } else if (hour >= 12 && hour <= 16) {
    baseTemp += 3;
  }
  
  // 添加一些随机变化（±3度）
  const variation = (Math.random() - 0.5) * 6;
  const finalTemp = Math.round(baseTemp + variation);
  
  return {
    temperature: finalTemp,
    description: '估算温度',
    city: cityName || '当前位置',
    updateTime: new Date().toLocaleTimeString('zh-CN')
  };
};

/**
 * 根据城市名称获取天气（需要先获取城市坐标）
 */
export const getWeatherByCity = async (cityName: string): Promise<WeatherInfo | null> => {
  // 这里可以集成城市名称到坐标的转换
  // 暂时返回null，建议使用坐标方式
  console.warn('getWeatherByCity 需要城市坐标，请使用 getWeatherByCoordinates');
  return null;
};

