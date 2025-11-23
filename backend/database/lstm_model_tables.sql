-- ============================================
-- LSTM 模型训练记录表
-- 用途：记录LSTM模型的训练历史、参数和性能指标
-- 数据库：Infectious_disease_data
-- ============================================

USE Infectious_disease_data;

-- ============================================
-- LSTM模型训练记录表
-- 用途：存储LSTM模型的训练信息，便于管理和追踪
-- ============================================
CREATE TABLE IF NOT EXISTS `flu_lstm_models` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `city_id` INT NOT NULL COMMENT '城市ID（关联cities表）',
    `model_name` VARCHAR(200) NOT NULL COMMENT '模型文件名（如：lstm_model_清远市_20250101.h5）',
    `model_path` VARCHAR(500) NOT NULL COMMENT '模型文件路径',
    `scaler_path` VARCHAR(500) COMMENT 'Scaler文件路径',
    `training_date` DATE NOT NULL COMMENT '训练日期',
    `epochs` INT NOT NULL COMMENT '训练轮数',
    `batch_size` INT NOT NULL COMMENT '批次大小',
    `validation_split` DECIMAL(3, 2) NOT NULL COMMENT '验证集比例',
    `historical_days` INT NOT NULL COMMENT '使用的历史数据天数',
    `data_points` INT NOT NULL COMMENT '实际使用的数据点数量',
    `final_loss` DECIMAL(10, 6) COMMENT '最终训练损失',
    `final_val_loss` DECIMAL(10, 6) COMMENT '最终验证损失',
    `final_mae` DECIMAL(10, 2) COMMENT '最终平均绝对误差',
    `final_val_mae` DECIMAL(10, 2) COMMENT '最终验证平均绝对误差',
    `sequence_length` INT DEFAULT 14 COMMENT '输入序列长度（默认14天）',
    `model_size` BIGINT COMMENT '模型文件大小（字节）',
    `training_time` INT COMMENT '训练耗时（秒）',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-有效，0-已删除',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否当前激活模型：1-是，0-否（同一城市可能有多个版本）',
    `user_id` BIGINT COMMENT '训练模型的用户ID',
    `remark` TEXT COMMENT '备注信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_city_id` (`city_id`),
    INDEX `idx_training_date` (`training_date`),
    INDEX `idx_is_active` (`is_active`, `city_id`),
    INDEX `idx_user_id` (`user_id`),
    FOREIGN KEY (`city_id`) REFERENCES `cities`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LSTM模型训练记录表';

-- ============================================
-- 注意：
-- 1. 模型文件本身保存在文件系统中（backend/models/目录）
-- 2. 此表只记录模型的元数据和训练信息
-- 3. 同一城市可以有多个模型版本，通过 is_active 字段标记当前使用的版本
-- 4. 预测结果仍然保存在 flu_seir_predictions 表中（algorithm='lstm'）
-- ============================================

