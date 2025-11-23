<template>
  <div class="model-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Setting /></el-icon>
          <span>预测模型配置管理</span>
        </div>
      </template>

      <el-alert
        title="配置说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #default>
          <div style="line-height: 1.8;">
            <p><strong>默认预测模型：</strong>设置前端公众端使用的默认预测算法</p>
            <p><strong>模型选择：</strong></p>
            <ul style="margin: 10px 0; padding-left: 20px;">
              <li><strong>SEIR 动力学模型：</strong>基于数学公式，适合理论分析和参数可解释的场景</li>
              <li><strong>LSTM 深度学习：</strong>需要训练，适合复杂模式学习，需要至少14天历史数据</li>
              <li><strong>Prophet 时序预测：</strong>自动识别季节性，适合有明显季节性的数据，需要至少30天历史数据</li>
            </ul>
            <p><strong>注意：</strong>前端会根据用户位置自动获取对应城市的数据，然后使用这里配置的默认模型进行预测</p>
          </div>
        </template>
      </el-alert>

      <el-form
        :model="configForm"
        label-width="180px"
        :rules="rules"
        ref="configFormRef"
      >
        <el-form-item label="默认预测算法" prop="default_algorithm">
          <el-radio-group v-model="configForm.default_algorithm">
            <el-radio label="seir">
              <div>
                <div style="font-weight: bold;">SEIR 动力学模型</div>
                <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                  基于数学公式，参数可解释，适合理论分析
                </div>
              </div>
            </el-radio>
            <el-radio label="lstm" style="margin-top: 15px;">
              <div>
                <div style="font-weight: bold;">LSTM 深度学习</div>
                <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                  需要训练，适合复杂模式学习（需至少14天数据）
                </div>
              </div>
            </el-radio>
            <el-radio label="prophet" style="margin-top: 15px;">
              <div>
                <div style="font-weight: bold;">Prophet 时序预测</div>
                <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                  自动识别季节性，适合有明显季节性的数据（需至少30天数据）
                </div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider />

        <el-form-item label="SEIR模型参数">
          <el-form-item label="R0 (基本传染数)" style="margin-bottom: 15px;">
            <el-input-number
              v-model="configForm.r0"
              :min="0.5"
              :max="5"
              :step="0.1"
              :precision="2"
              style="width: 200px;"
            />
            <span style="margin-left: 10px; color: #909399; font-size: 12px;">
              流感通常为 1.2-2.0
            </span>
          </el-form-item>

          <el-form-item label="潜伏期 (天)" style="margin-bottom: 15px;">
            <el-input-number
              v-model="configForm.incubation_period"
              :min="1"
              :max="14"
              :step="0.5"
              :precision="1"
              style="width: 200px;"
            />
            <span style="margin-left: 10px; color: #909399; font-size: 12px;">
              流感通常为 3-7 天
            </span>
          </el-form-item>

          <el-form-item label="传染期 (天)" style="margin-bottom: 15px;">
            <el-input-number
              v-model="configForm.infectious_period"
              :min="1"
              :max="20"
              :step="0.5"
              :precision="1"
              style="width: 200px;"
            />
            <span style="margin-left: 10px; color: #909399; font-size: 12px;">
              流感通常为 5-10 天
            </span>
          </el-form-item>

          <el-form-item label="防控措施影响因子" style="margin-bottom: 15px;">
            <el-input-number
              v-model="configForm.intervention_factor"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 200px;"
            />
            <span style="margin-left: 10px; color: #909399; font-size: 12px;">
              1.0=无防控，0.5=中等防控，0.2=严格防控
            </span>
          </el-form-item>

          <el-form-item label="预测天数" style="margin-bottom: 15px;">
            <el-input-number
              v-model="configForm.days"
              :min="1"
              :max="5"
              :step="1"
              style="width: 200px;"
            />
            <span style="margin-left: 10px; color: #909399; font-size: 12px;">
              默认预测未来天数，建议 3-5 天
            </span>
          </el-form-item>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">
            保存配置
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="info-section">
        <h3>当前配置信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="默认算法">
            <el-tag :type="getAlgorithmTagType(configForm.default_algorithm)">
              {{ getAlgorithmName(configForm.default_algorithm) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="R0值">
            {{ configForm.r0 }}
          </el-descriptions-item>
          <el-descriptions-item label="潜伏期">
            {{ configForm.incubation_period }} 天
          </el-descriptions-item>
          <el-descriptions-item label="传染期">
            {{ configForm.infectious_period }} 天
          </el-descriptions-item>
          <el-descriptions-item label="防控措施影响因子">
            {{ configForm.intervention_factor }}
          </el-descriptions-item>
          <el-descriptions-item label="预测天数">
            {{ configForm.days }} 天
          </el-descriptions-item>
          <el-descriptions-item label="最后更新时间">
            {{ lastUpdateTime || '未保存' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Setting } from '@element-plus/icons-vue';
import { getAdminModelConfigAPI, updateAdminModelConfigAPI } from '@/api/index';

const configFormRef = ref();
const saving = ref(false);
const lastUpdateTime = ref('');

const configForm = reactive({
  default_algorithm: 'seir',
  r0: 1.4,
  incubation_period: 5.0,
  infectious_period: 7.0,
  intervention_factor: 1.0,
  days: 3
});

const rules = {
  default_algorithm: [
    { required: true, message: '请选择默认预测算法', trigger: 'change' }
  ]
};

// 获取算法名称
const getAlgorithmName = (algorithm: string) => {
  const names: Record<string, string> = {
    'seir': 'SEIR 动力学模型',
    'lstm': 'LSTM 深度学习',
    'prophet': 'Prophet 时序预测'
  };
  return names[algorithm] || algorithm;
};

// 获取算法标签类型
const getAlgorithmTagType = (algorithm: string) => {
  const types: Record<string, string> = {
    'seir': 'primary',
    'lstm': 'success',
    'prophet': 'warning'
  };
  return types[algorithm] || '';
};

// 加载配置
const loadConfig = async () => {
  try {
    const res: any = await getAdminModelConfigAPI();
    if (res.code === 200 && res.data) {
      configForm.default_algorithm = res.data.default_algorithm || 'seir';
      configForm.r0 = res.data.r0 || 1.4;
      configForm.incubation_period = res.data.incubation_period || 5.0;
      configForm.infectious_period = res.data.infectious_period || 7.0;
      configForm.intervention_factor = res.data.intervention_factor || 1.0;
      configForm.days = res.data.days || 3;
      
      if (res.data.updated_at) {
        lastUpdateTime.value = res.data.updated_at;
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error);
    ElMessage.warning('加载配置失败，使用默认值');
  }
};

// 保存配置
const handleSave = async () => {
  try {
    await configFormRef.value.validate();
    saving.value = true;
    
    const res: any = await updateAdminModelConfigAPI(configForm);
    
    if (res.code === 200) {
      ElMessage.success('配置保存成功！前端将使用新的默认模型进行预测');
      lastUpdateTime.value = new Date().toLocaleString('zh-CN');
    } else {
      ElMessage.error(res.msg || '保存失败');
    }
  } catch (error: any) {
    if (error.fields) {
      ElMessage.warning('请检查表单填写');
    } else {
      console.error('保存配置失败:', error);
      ElMessage.error('保存配置失败');
    }
  } finally {
    saving.value = false;
  }
};

// 重置配置
const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确定要重置为默认配置吗？', '提示', {
      type: 'warning'
    });
    
    configForm.default_algorithm = 'seir';
    configForm.r0 = 1.4;
    configForm.incubation_period = 5.0;
    configForm.infectious_period = 7.0;
    configForm.intervention_factor = 1.0;
    configForm.days = 3;
    
    ElMessage.info('已重置为默认配置，请点击"保存配置"应用更改');
  } catch {
    // 用户取消
  }
};

onMounted(() => {
  loadConfig();
});
</script>

<style scoped>
.model-config-container {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.info-section {
  margin-top: 30px;
}

.info-section h3 {
  margin-bottom: 15px;
  color: #303133;
}
</style>

