-- ============================================
-- 为 flu_model_config 表添加 default_algorithm 字段
-- 用途：存储默认预测算法配置
-- ============================================

USE Infectious_disease_data;

-- 添加 default_algorithm 字段（如果不存在）
-- 使用存储过程检查列是否存在，避免重复添加
SET @dbname = DATABASE();
SET @tablename = 'flu_model_config';
SET @columnname = 'default_algorithm';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @dbname
        AND TABLE_NAME = @tablename
        AND COLUMN_NAME = @columnname
    ) > 0,
    'SELECT 1', -- 列已存在，不执行任何操作
    CONCAT('ALTER TABLE `', @tablename, '` ADD COLUMN `', @columnname, '` VARCHAR(20) DEFAULT ''seir'' COMMENT ''默认预测算法：seir/lstm/prophet'' AFTER `intervention_factor`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 更新现有默认配置的算法
-- 使用子查询确保 WHERE 子句包含主键，满足安全更新模式要求
UPDATE `flu_model_config` 
SET `default_algorithm` = 'seir' 
WHERE `id` IN (
    SELECT `id` FROM (
        SELECT `id` FROM `flu_model_config` WHERE `is_default` = 1
    ) AS temp
);

-- 验证
SELECT 
    id,
    config_name,
    default_algorithm,
    is_default
FROM `flu_model_config`
WHERE `is_default` = 1;

