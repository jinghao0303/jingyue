// src/api/index.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 1. 创建 axios 实例
const DEFAULT_DEV_BASE_URL = 'http://127.0.0.1:5010'
const runtimeBaseURL =
  (import.meta.env?.VITE_API_BASE_URL as string | undefined)?.trim() ||
  ((typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
    ? DEFAULT_DEV_BASE_URL
    : `${window.location.origin}`)

const request = axios.create({
  baseURL: runtimeBaseURL,
  timeout: 10000 // 请求超时时间
})

// 2. 请求拦截器：每次请求头自动带上 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      // 关键点：Bearer 后面必须有一个空格
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 3. 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => {
    // 过滤掉广告相关的响应打印（如果有浏览器扩展在打印）
    // 直接返回后端的数据 data 部分
    return response.data
  },
  (error) => {
    // 获取错误状态码
    const status = error.response?.status
    const msg = error.response?.data?.msg || '请求失败，请检查网络'

    // --- 核心修复：处理 Token 失效或格式错误 ---
    if (status === 401 || status === 422) {
      // 401: Token 过期
      // 422: Token 格式不对 (例如缺少 Bearer 前缀)
      ElMessage.error('登录状态已失效，请重新登录')
      
      // 1. 清除本地脏数据
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      
      // 2. 延迟跳转回登录页 (避免瞬间刷新太快看不清提示)
      setTimeout(() => {
        window.location.href = '/login'
      }, 1000)
      
    } else if (status === 403) {
      // 403: 权限不足 (例如普通管理员想操作超级管理员的功能)
      ElMessage.warning('权限不足：只有超级管理员可执行此操作')
    } else {
      // 其他错误 (500, 404 等)
      ElMessage.error(msg)
    }
    
    return Promise.reject(error)
  }
)

// ================= 接口定义区 =================

// 1. 认证模块
export const loginAPI = (data: any) => request.post('/api/auth/login', data)
export const registerAPI = (data: any) => request.post('/api/auth/register', data)
export const getCurrentUserAPI = () => request.get('/api/auth/me')
export const updateUserInfoAPI = (data: any) => request.put('/api/auth/me', data)

// 2. 预测模块 (后台 Dashboard 用)
export const predictAPI = (data: any) => request.post('/api/predict/run', data)

// 3. 管理员模块 (仅 username='admin' 可用)
export const getUserListAPI = () => request.get('/api/admin/users')

// [新增] 批准为研究员
export const approveUserAPI = (userId: number) => request.post('/api/admin/approve', { user_id: userId })

// 提升权限
export const promoteUserAPI = (userId: number) => request.post('/api/admin/promote', { user_id: userId })

// [新增] 移除权限
export const demoteUserAPI = (userId: number) => request.post('/api/admin/demote', { user_id: userId })

// 4. 公众大屏模块 (前台用，无需 Token 或由后端放行)
export const getPublicStatsAPI = () => request.get('/api/public/stats')

// 5. 公开预测接口 (前台用，无需登录)
export const getPublicPredictAPI = (data: any) => request.post('/api/public/predict', data)

// 6. 模型配置管理 (管理员用)
export const getAdminModelConfigAPI = () => request.get('/api/admin/model/config')
export const updateAdminModelConfigAPI = (data: any) => request.post('/api/admin/model/config', data)

// 7. 获取默认模型配置 (公众端用，无需登录)
export const getDefaultModelConfigAPI = () => request.get('/api/public/model/config')

// 8. 训练数据监控 (管理员用)
export const getTrainingDataStatsAPI = () => request.get('/api/admin/data/stats')
export const getProvincesListAPI = () => request.get('/api/admin/data/provinces')
export const getCitiesListAPI = (provinceId?: number, params?: any) => {
  const requestParams: any = { ...params };
  if (provinceId) {
    requestParams.province_id = provinceId;
  }
  return request.get('/api/admin/data/cities', { params: requestParams });
}
export const getHistoricalDataAPI = (cityName: string, days: number = 60) => 
  request.get('/api/admin/data/historical', { params: { city_name: cityName, days } })
export const getDailyDataListAPI = (params: any) => 
  request.get('/api/admin/data/daily', { params })

// 9. LSTM模型训练 (管理员用)
export const trainLstmModelAPI = (data: any) => request.post('/api/predict/train/lstm', data)

export default request