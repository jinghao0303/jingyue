<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="8" v-for="item in resources" :key="item.name">
        <el-card shadow="always" :body-style="{ padding: '20px' }">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-size: 14px; color: #909399;">{{ item.name }}</div>
              <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">{{ item.used }} / {{ item.total }}</div>
            </div>
            <el-progress type="dashboard" :percentage="item.percentage" :color="item.color" width="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 这里可以加一个表格，显示各医院具体剩余床位 -->
    <el-card header="各定点医院床位余量" style="margin-top: 20px;">
      <el-table :data="hospitalData" stripe>
        <el-table-column prop="name" label="医院名称" />
        <el-table-column prop="icu_free" label="ICU 空余" />
        <el-table-column prop="status" label="负荷状态">
           <template #default="{ row }">
             <el-tag :type="row.status === '正常' ? 'success' : 'danger'">{{ row.status }}</el-tag>
           </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
const resources = [
  { name: 'ICU 重症床位', used: 450, total: 500, percentage: 90, color: '#F56C6C' },
  { name: '呼吸机储备', used: 120, total: 300, percentage: 40, color: '#409EFF' },
  { name: '医护人员在岗', used: 2800, total: 3000, percentage: 93, color: '#E6A23C' },
];

const hospitalData = [
  { name: '市第一人民医院', icu_free: 2, status: '告急' },
  { name: '中心医院', icu_free: 15, status: '正常' },
];
</script>