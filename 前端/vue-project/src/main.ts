import { createApp } from 'vue'
import App from './App.vue'

// 1. 引入 Element Plus 及其样式
import ElementPlus from 'element-plus' 
import 'element-plus/dist/index.css'
// 如果需要中文包（推荐），解开下面这两行注释
// import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 引入你刚刚创建的路由配置
import router from './router'

// 过滤掉广告相关的响应打印（来自浏览器扩展或用户脚本）
const originalLog = console.log
console.log = (...args: any[]) => {
  const message = args[0]?.toString() || ''
  // 过滤掉包含广告 URL 或特定格式的打印
  if (message.includes('cdn.lyck6.cn') || 
      (message.includes('timestamp') && message.includes('code') && message.includes('result'))) {
    return // 忽略广告相关的打印
  }
  originalLog.apply(console, args)
}

const app = createApp(App)

// 2. 注册插件（关键步骤！）
app.use(ElementPlus)
// 如果启用中文包，改为: app.use(ElementPlus, { locale: zhCn })

// 挂载路由
app.use(router)

app.mount('#app')