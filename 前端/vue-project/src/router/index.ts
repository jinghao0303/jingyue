import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 1. 根路径重定向到登录
  {
    path: '/',
    redirect: '/login'
  },
  
  // 2. 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  },
  
  // 3. 后台管理端 (PC端 - AdminLayout)
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'), // 确保你创建了 src/layouts/AdminLayout.vue
    meta: { requiresAuth: true }, // 整个 admin 目录下都需要登录
    children: [
      { 
        path: 'dashboard', 
        name: 'Dashboard',
        component: () => import('../views/admin/DashboardView.vue'), 
        meta: { title: '疫情态势总览' } 
      },
      { 
        path: 'map', 
        name: 'MapAnalysis',
        component: () => import('../views/admin/MapAnalysis.vue'), 
        meta: { title: '区域风险地图' } 
      },
      { 
        path: 'data', 
        name: 'DataManage',
        component: () => import('../views/admin/DataManage.vue'), 
        meta: { title: '病例数据管理' } 
      },
      { 
        path: 'simulation', 
        name: 'Simulation',
        component: () => import('../views/admin/Simulation.vue'), 
        meta: { title: '多场景推演' } 
      },
      { 
        path: 'resources', 
        name: 'Resources',
        component: () => import('../views/admin/Resources.vue'), 
        meta: { title: '医疗资源监控' }
      },
      { 
        path: 'model-config', 
        name: 'ModelConfig',
        component: () => import('../views/admin/ModelConfig.vue'), 
        meta: { title: '模型配置管理' }
      },
      { 
        path: 'data-monitor', 
        name: 'DataMonitor',
        component: () => import('../views/admin/DataMonitor.vue'), 
        meta: { title: '训练数据监控' }
      },
    ]
  },
  
  // 4. 公众展示端 (移动端 - PublicLayout)
  {
    path: '/public',
    component: () => import('../layouts/PublicLayout.vue'), // 确保你创建了 src/layouts/PublicLayout.vue
    redirect: '/public/home', // 默认进首页
    children: [
      { 
        path: 'home', 
        name: 'PublicHome', 
        component: () => import('../views/public/Home.vue'),
        meta: { title: '城市防疫' }
      },
      { 
        path: 'map', 
        name: 'PublicMap', 
        component: () => import('../views/public/RiskMap.vue'), 
        meta: { title: '身边风险' }
      },
      { 
        path: 'guide', 
        name: 'PublicGuide', 
        component: () => import('../views/public/Guide.vue'), 
        meta: { title: '防护指南' }
      },
      { 
        path: 'profile', 
        name: 'PublicProfile', 
        component: () => import('../views/public/Profile.vue'), 
        meta: { title: '账号管理', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫：检查权限
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 检查当前路由或其父路由是否需要验证
  if (to.matched.some(record => record.meta.requiresAuth) && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router