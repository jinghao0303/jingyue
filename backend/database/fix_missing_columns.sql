-- ============================================
-- 快速修复：为 flu_model_config 表添加缺失字段
-- 执行方法：mysql -u root -p Infectious_disease_data < backend/database/fix_missing_columns.sql
-- ============================================

USE Infectious_disease_data;

-- 添加 days 字段（如果不存在）
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
    'SELECT 1',
    CONCAT('ALTER TABLE `', @tablename, '` ADD COLUMN `', @columnname, '` INT DEFAULT 3 COMMENT ''预测天数，默认3天'' AFTER `intervention_factor`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 添加 default_algorithm 字段（如果不存在）
SET @columnname = 'default_algorithm';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @dbname
        AND TABLE_NAME = @tablename
        AND COLUMN_NAME = @columnname
    ) > 0,
    'SELECT 1',
    CONCAT('ALTER TABLE `', @tablename, '` ADD COLUMN `', @columnname, '` VARCHAR(20) DEFAULT ''seir'' COMMENT ''默认预测算法：seir/lstm/prophet'' AFTER `intervention_factor`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 更新现有默认配置
UPDATE `flu_model_config` 
SET `days` = 3, `default_algorithm` = 'seir'
WHERE `is_default` = 1 AND (`days` IS NULL OR `days` = 0 OR `default_algorithm` IS NULL);

-- 验证
SELECT 
    id,
    config_name,
    days,
    default_algorithm,
    is_default
FROM `flu_model_config`
WHERE `is_default` = 1;

