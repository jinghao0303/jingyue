<template>
  <div>
    <el-card>
      <div class="filter-bar" style="margin-bottom: 20px; display: flex; gap: 10px;">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        <el-button type="primary" icon="Search">查询</el-button>
        <el-button type="success" icon="Plus" @click="dialogVisible = true">录入新数据</el-button>
      </div>

      <el-table :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="180" sortable />
        <el-table-column prop="confirmed" label="新增确诊" sortable />
        <el-table-column prop="asymptomatic" label="无症状感染" />
        <el-table-column prop="cured" label="治愈出院" />
        <el-table-column label="操作" width="150">
          <template #default>
            <el-button link type="primary" size="small">编辑</el-button>
            <el-button link type="danger" size="small">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination style="margin-top: 20px;" background layout="prev, pager, next" :total="100" />
    </el-card>

    <!-- 录入弹窗 (简化版) -->
    <el-dialog v-model="dialogVisible" title="录入每日疫情数据" width="500px">
      <el-form label-width="100px">
        <el-form-item label="日期"><el-date-picker type="date" style="width: 100%" /></el-form-item>
        <el-form-item label="确诊人数"><el-input-number :min="0" /></el-form-item>
        <el-form-item label="无症状"><el-input-number :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="dialogVisible = false">提交数据库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const dateRange = ref('');
const dialogVisible = ref(false);
// 模拟表格数据
const tableData = [
  { date: '2023-11-20', confirmed: 125, asymptomatic: 45, cured: 89 },
  { date: '2023-11-19', confirmed: 110, asymptomatic: 30, cured: 70 },
  { date: '2023-11-18', confirmed: 98, asymptomatic: 20, cured: 55 },
];
</script>