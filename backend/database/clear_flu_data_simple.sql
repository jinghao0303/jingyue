-- ============================================
-- 清空流感模拟数据（简单版）
-- 用途：删除之前插入的模拟数据，重新导入
-- 兼容MySQL安全更新模式
-- ============================================

USE Infectious_disease_data;

-- 方法：先查询ID，再删除（完全兼容安全模式）
DELETE FROM `flu_daily_cases`
WHERE `id` IN (
    SELECT id FROM (
        SELECT fdc.id
        FROM flu_daily_cases fdc
        WHERE fdc.data_source = '模拟数据'
          AND fdc.date >= '2024-10-01'
          AND fdc.date <= '2025-01-31'
    ) AS temp
);

-- 查看删除结果
SELECT 
    COUNT(*) as remaining_simulated_data,
    '如果为0，说明已全部删除' as note
FROM flu_daily_cases fdc
WHERE fdc.data_source = '模拟数据'
  AND fdc.date >= '2024-10-01'
  AND fdc.date <= '2025-01-31';

