<template>
  <div class="profile-page">
    <div class="profile-header">
      <h2>账号管理</h2>
    </div>

    <div class="profile-content">
      <!-- 头像上传 -->
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <span>头像设置</span>
          </div>
        </template>
        <div class="avatar-section">
          <div class="avatar-wrapper">
            <el-avatar 
              :size="100" 
              :src="avatarUrl"
              :icon="UserFilled"
              class="avatar"
            />
            <div class="avatar-overlay" @click="triggerFileInput">
              <el-icon :size="24"><Camera /></el-icon>
              <span>更换头像</span>
            </div>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleAvatarChange"
          />
          <p class="avatar-tip">支持 JPG、PNG 格式，建议尺寸 200x200</p>
        </div>
      </el-card>

      <!-- 基本信息 -->
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <el-form
          ref="formRef"
          :model="userForm"
          :rules="rules"
          label-width="100px"
          label-position="left"
        >
          <el-form-item label="账号名称">
            <span class="readonly-text">{{ userForm.username || '未知' }}</span>
            <span class="readonly-hint">（账号名称不可修改）</span>
          </el-form-item>

          <el-form-item label="真实姓名" prop="real_name">
            <el-input
              v-model="userForm.real_name"
              placeholder="请输入真实姓名（选填）"
              maxlength="20"
            />
          </el-form-item>

          <el-form-item label="账号角色">
            <el-tag :type="getRoleTagType(userForm.role)">
              {{ getRoleName(userForm.role) }}
            </el-tag>
          </el-form-item>

          <el-form-item label="注册时间">
            <span class="readonly-text">{{ userForm.created_at || '未知' }}</span>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSave" :loading="saving">
              保存修改
            </el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 退出登录 -->
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <span>账号操作</span>
          </div>
        </template>
        <div class="logout-section">
          <el-button 
            type="danger" 
            :icon="SwitchButton" 
            @click="handleLogout"
            style="width: 100%;"
          >
            退出登录
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UserFilled, Camera, SwitchButton } from '@element-plus/icons-vue';
import { getCurrentUserAPI, updateUserInfoAPI } from '@/api/index';

const router = useRouter();

const formRef = ref();
const fileInput = ref<HTMLInputElement | null>(null);
const saving = ref(false);
const avatarUrl = ref<string>('');

const userForm = reactive({
  user_id: 0,
  username: '',
  real_name: '',
  role: '',
  created_at: ''
});

const rules = {
  // 账号名称不可修改，不需要验证规则
};

const originalForm = reactive({
  real_name: ''
});

// 获取角色名称
const getRoleName = (role: string) => {
  const roleMap: Record<string, string> = {
    'public': '普通用户',
    'researcher': '研究员',
    'admin': '管理员'
  };
  return roleMap[role] || role;
};

// 获取角色标签类型
const getRoleTagType = (role: string) => {
  const typeMap: Record<string, string> = {
    'public': 'info',
    'researcher': 'success',
    'admin': 'warning'
  };
  return typeMap[role] || 'info';
};

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click();
};

// 处理头像选择
const handleAvatarChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件');
    return;
  }
  
  // 检查文件大小（限制为2MB）
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB');
    return;
  }
  
  // 读取文件并转换为base64
  const reader = new FileReader();
  reader.onload = (e) => {
    const result = e.target?.result as string;
    avatarUrl.value = result;
    // 保存头像到localStorage（临时方案）
    localStorage.setItem('userAvatar', result);
    ElMessage.success('头像已更新，请点击保存修改');
  };
  reader.readAsDataURL(file);
};

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const res: any = await getCurrentUserAPI();
    if (res.code === 200 && res.data) {
      userForm.user_id = res.data.user_id;
      userForm.username = res.data.username || '';
      userForm.real_name = res.data.real_name || '';
      userForm.role = res.data.role || 'public';
      userForm.created_at = res.data.created_at || '';
      
      // 保存原始值用于重置
      originalForm.real_name = res.data.real_name || '';
      
      // 加载头像（从localStorage或使用默认）
      avatarUrl.value = localStorage.getItem('userAvatar') || '';
    }
  } catch (error: any) {
    console.error('加载用户信息失败:', error);
    ElMessage.error('加载用户信息失败: ' + (error.message || '未知错误'));
  }
};

// 保存修改
const handleSave = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;
    
    saving.value = true;
    try {
      const updateData: any = {
        real_name: userForm.real_name || null
      };
      
      // 如果头像已更新，添加到更新数据中
      if (avatarUrl.value && avatarUrl.value !== localStorage.getItem('userAvatar')) {
        updateData.avatar = avatarUrl.value;
      }
      
      const res: any = await updateUserInfoAPI(updateData);
      if (res.code === 200) {
        ElMessage.success('保存成功');
        // 更新localStorage中的用户信息
        const userInfo = localStorage.getItem('userInfo');
        if (userInfo) {
          const user = JSON.parse(userInfo);
          user.real_name = userForm.real_name;
          localStorage.setItem('userInfo', JSON.stringify(user));
        }
        // 保存头像
        if (avatarUrl.value) {
          localStorage.setItem('userAvatar', avatarUrl.value);
        }
        // 更新原始值
        originalForm.real_name = userForm.real_name;
      } else {
        ElMessage.error(res.msg || '保存失败');
      }
    } catch (error: any) {
      console.error('保存用户信息失败:', error);
      ElMessage.error('保存失败: ' + (error.message || '未知错误'));
    } finally {
      saving.value = false;
    }
  });
};

// 重置表单
const handleReset = () => {
  userForm.real_name = originalForm.real_name;
  // 重置头像
  const savedAvatar = localStorage.getItem('userAvatar');
  avatarUrl.value = savedAvatar || '';
  ElMessage.info('已重置为原始值');
};

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    // 清除所有本地存储的数据
    localStorage.removeItem('token');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('userAvatar');
    
    ElMessage.success('已退出登录');
    
    // 跳转到登录页
    router.push('/login');
  }).catch(() => {
    // 用户取消，不做任何操作
  });
};

onMounted(() => {
  loadUserInfo();
});
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
  padding-bottom: 80px;
}

.profile-header {
  margin-bottom: 20px;
}

.profile-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: 15px;
  cursor: pointer;
}

.avatar {
  border: 3px solid #e4e7ed;
  transition: all 0.3s;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.3s;
  cursor: pointer;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay span {
  font-size: 12px;
  margin-top: 5px;
}

.avatar-tip {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.readonly-text {
  color: #606266;
}

.readonly-hint {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.logout-section {
  padding: 20px 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input) {
  max-width: 400px;
}
</style>

