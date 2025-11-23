-- ============================================
-- 为 flu_model_config 表添加 days 字段
-- 用途：存储默认预测天数配置
-- ============================================

USE Infectious_disease_data;

-- 添加 days 字段（如果不存在）
-- 使用存储过程检查列是否存在，避免重复添加
SET @dbname = DATABASE();
SET @tablename = 'flu_model_config';
SET @columnname = 'days';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @dbname
        AND TABLE_NAME = @tablename
        AND COLUMN_NAME = @columnname
    ) > 0,
    'SELECT 1', -- 列已存在，不执行任何操作
    CONCAT('ALTER TABLE `', @tablename, '` ADD COLUMN `', @columnname, '` INT DEFAULT 3 COMMENT ''预测天数，默认3天'' AFTER `intervention_factor`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 更新现有默认配置的预测天数
-- 使用子查询确保 WHERE 子句包含主键，满足安全更新模式要求
UPDATE `flu_model_config` 
SET `days` = 3 
WHERE `id` IN (
    SELECT `id` FROM (
        SELECT `id` FROM `flu_model_config` WHERE `is_default` = 1 AND (`days` IS NULL OR `days` = 0)
    ) AS temp
);

-- 验证
SELECT 
    id,
    config_name,
    days,
    is_default
FROM `flu_model_config`
WHERE `is_default` = 1;

