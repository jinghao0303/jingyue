<template>
  <div class="login-container">
    <div class="brand-section">
      <div class="brand-bg-overlay"></div>
      <div class="brand-content">
        <div class="logo">
          <el-icon :size="36"><TrendCharts /></el-icon>
          <span>IDPS System</span>
        </div>
        <h2 class="brand-title">传染病态势<br />感知与预测系统</h2>
        <p class="brand-desc">
          Infectious Disease Prediction System<br/><br/>
          基于多源异构数据与 AI 算法，提供精准的疫情趋势预测、风险评估与辅助决策支持，构筑智慧公卫防线。
        </p>
      </div>
    </div>

    <div class="form-section">
      <div class="form-wrapper">
        <div class="welcome-text">
          <h3>{{ isLogin ? '系统登录' : '创建账户' }}</h3>
          <p class="sub-text">
            {{ isLogin ? '请输入您的专家账号以访问数据大屏' : '填写以下信息注册新的研究员账号' }}
          </p>
        </div>

        <transition name="fade" mode="out-in">
          
          <el-form
            v-if="isLogin"
            key="login"
            ref="loginFormRef"
            :model="loginForm"
            :rules="rules"
            size="large"
            class="custom-form"
          >
            <el-form-item prop="username">
              <div class="input-label">账号 / 工号</div>
              <el-input
                v-model="loginForm.username"
                placeholder="请输入工号"
                :prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <div class="input-label">密码</div>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
                @keyup.enter="handleLogin(loginFormRef)"
              />
            </el-form-item>

            <div class="form-actions">
              <el-checkbox v-model="loginForm.rememberMe" label="记住我" />
              <el-link type="primary" :underline="false">忘记密码?</el-link>
            </div>

            <el-button
              type="primary"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin(loginFormRef)"
            >
              立即登录
            </el-button>
          </el-form>

          <el-form
            v-else
            key="register"
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            size="large"
            class="custom-form"
          >
            <el-form-item prop="username">
              <div class="input-label">设置账号</div>
              <el-input
                v-model="registerForm.username"
                placeholder="请设置登录账号"
                :prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <div class="input-label">设置密码</div>
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="8位以上数字与字母组合"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <div class="input-label">确认密码</div>
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
              />
            </el-form-item>

            <el-button
              type="success"
              class="submit-btn register-btn-color"
              :loading="loading"
              @click="handleRegister(registerFormRef)"
            >
              注册账户
            </el-button>
          </el-form>
        </transition>

        <div class="switch-mode-box">
          <span class="text-gray">
            {{ isLogin ? '还没有账号？' : '已有账号？' }}
          </span>
          <el-link 
            type="primary" 
            :underline="false" 
            @click="toggleMode" 
            class="switch-link"
          >
            {{ isLogin ? '立即注册' : '返回登录' }}
          </el-link>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue' // <-- 缺少这一行
// 引入新的图标
import { User, Lock, TrendCharts } from '@element-plus/icons-vue' // <-- 缺少图标的引入
import { ElMessage, type FormInstance, type FormRules } from 'element-plus' // <-- 缺少 ElMessage, FormInstance 等类型定义

// 引入刚才定义的接口
import { loginAPI, registerAPI } from '../api/index'
import { useRouter } from 'vue-router' 

// --- 状态管理 (缺失的核心部分) ---
const isLogin = ref(true) // 控制登录/注册切换
const loading = ref(false)

// 表单引用
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// Router 实例 (如果已安装 vue-router，这一行是必须的)
const router = useRouter() 

// --- 数据模型 (缺失的核心部分) ---
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// --- 验证规则 (缺失的核心部分) ---
const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
})

// 注册专用验证：确认密码一致性
const validatePass2 = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const registerRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validatePass2, trigger: 'blur' }]
})


// 切换模式时重置表单
const toggleMode = () => {
  isLogin.value = !isLogin.value
  // 简单的延迟清理，防止动画卡顿
  setTimeout(() => {
    loginFormRef.value?.resetFields()
    registerFormRef.value?.resetFields()
  }, 200)
}

// --- 登录逻辑 (你提供的代码) ---
const handleLogin = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        const res: any = await loginAPI(loginForm)
        
        if (!res.token) {
            ElMessage.error('登录异常：后端未返回 Token')
            return
        }

        ElMessage.success('登录成功，正在进入系统...')
        
        // 1. 保存 Token (确保这里和后端返回的字段名一致)
        localStorage.setItem('token', res.token)
        localStorage.setItem('userInfo', JSON.stringify(res.userInfo))

        // 2. 跳转
        // 如果是 admin 或 researcher，跳到 /admin/dashboard
        if (res.userInfo.role === 'admin' || res.userInfo.role === 'researcher') {
            router.push('/admin/dashboard') 
        } else {
            // 其他人跳到 /public/home
            router.push('/public/home')
        }

      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

// --- 注册逻辑 (你提供的代码) ---
const handleRegister = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
     if (valid) {
      try {
        loading.value = true

        // 发送真实注册请求
        await registerAPI({
          username: registerForm.username,
          password: registerForm.password
          // confirmPassword 不需要发给后端，后端只存 password
        })

        ElMessage.success('注册成功！请登录')
        toggleMode() // 切回登录页

      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }

    }
  })
}
</script>
<style scoped>
/* --- 布局框架 --- */
.login-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
  background: #fff;
}

/* --- 左侧：医疗/科技风格 --- */
.brand-section {
  flex: 1;
  /* 改为深青/蓝绿色调，符合医疗与数据大屏的科技感 */
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px;
  color: white;
  overflow: hidden;
}

/* 科技感背景装饰：模拟数据网格或波浪 */
.brand-bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
    radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: 0 0, 20px 20px;
  opacity: 0.3;
  z-index: 0;
}

/* 光效球 */
.brand-bg-overlay::after {
  content: '';
  position: absolute;
  bottom: -100px;
  left: -100px;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(0, 255, 170, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 6s infinite alternate;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(1.2); opacity: 0.8; }
}

.brand-content {
  position: relative;
  z-index: 2;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 40px;
  color: #4ade80; /* 医疗绿/荧光绿，突出科技感 */
  letter-spacing: 1px;
}

.brand-title {
  font-size: 56px;
  line-height: 1.1;
  font-weight: 800;
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.brand-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.75);
  max-width: 480px;
  line-height: 1.8;
}

/* --- 右侧表单区 --- */
.form-section {
  flex: 1; /* 增加宽度占比，或保持 1:1 */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #ffffff;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.welcome-text {
  margin-bottom: 32px;
}

.welcome-text h3 {
  font-size: 30px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 8px;
}

.sub-text {
  color: #909399;
  font-size: 14px;
}

/* 表单样式 */
.input-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.custom-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e5e7eb inset;
  padding: 12px;
  border-radius: 8px;
  background-color: #f9fafb;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #0f766e inset !important; /* 聚焦变为深青色 */
  background-color: #fff;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  margin-top: 10px;
  background-color: #0f766e; /* 按钮颜色与品牌色呼应 */
  border: none;
}

.submit-btn:hover {
  background-color: #115e59;
}

.register-btn-color {
  background-color: #059669; /* 注册按钮用绿色区分 */
}
.register-btn-color:hover {
  background-color: #047857;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

/* 底部切换 */
.switch-mode-box {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
}
.text-gray {
  color: #6b7280;
}
.switch-link {
  font-weight: 600;
  margin-left: 4px;
  vertical-align: baseline;
  color: #0f766e;
}

/* --- 过渡动画 (Fade) --- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

@media (max-width: 900px) {
  .brand-section {
    display: none;
  }
}
</style>