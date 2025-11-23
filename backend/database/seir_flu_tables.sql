-- ============================================
-- SEIR 流感预测算法数据库表结构
-- 用途：存储流感疫情历史数据、预测结果和配置信息
-- 数据库：Infectious_disease_data
-- ============================================

USE Infectious_disease_data;

-- ============================================
-- 注意：城市人口配置表已迁移到 region_tables.sql
-- 请先执行 region_tables.sql 创建地区表结构
-- ============================================

-- ============================================
-- 2. 流感历史数据表（每日病例统计）
-- 用途：存储每日流感确诊病例数据，用于模型校准和验证
-- 注意：city_id 关联到 cities 表，支持多表查询
-- ============================================
CREATE TABLE IF NOT EXISTS `flu_daily_cases` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `date` DATE NOT NULL COMMENT '日期',
    `city_id` INT NOT NULL COMMENT '城市ID（关联cities表）',
    `confirmed` INT DEFAULT 0 COMMENT '累计确诊数',
    `active` INT DEFAULT 0 COMMENT '当前活跃病例数（正在患病）',
    `recovered` INT DEFAULT 0 COMMENT '累计康复数',
    `deaths` INT DEFAULT 0 COMMENT '累计死亡数',
    `new_cases` INT DEFAULT 0 COMMENT '当日新增病例',
    `new_recovered` INT DEFAULT 0 COMMENT '当日新增康复',
    `new_deaths` INT DEFAULT 0 COMMENT '当日新增死亡',
    `hospitalized` INT DEFAULT 0 COMMENT '当前住院人数',
    `severe` INT DEFAULT 0 COMMENT '重症病例数',
    `data_source` VARCHAR(100) COMMENT '数据来源（如：CDC、医院上报等）',
    `remark` TEXT COMMENT '备注信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_date_city` (`date`, `city_id`),
    INDEX `idx_date` (`date`),
    INDEX `idx_city_id` (`city_id`),
    INDEX `idx_date_city` (`date`, `city_id`),
    FOREIGN KEY (`city_id`) REFERENCES `cities`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流感每日病例数据表';

-- ============================================
-- 3. SEIR模型预测结果表
-- 用途：存储模型预测的结果，用于历史查询和对比分析
-- 注意：city_id 关联到 cities 表，支持多表查询
-- ============================================
CREATE TABLE IF NOT EXISTS `flu_seir_predictions` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `prediction_date` DATE NOT NULL COMMENT '预测日期（预测的起始日期）',
    `city_id` INT NOT NULL COMMENT '城市ID（关联cities表）',
    `algorithm` VARCHAR(20) NOT NULL DEFAULT 'seir' COMMENT '算法类型：seir/lstm/prophet',
    `r0` DECIMAL(5, 2) NOT NULL COMMENT '基本传染数（R0值）',
    `days` INT NOT NULL COMMENT '预测天数',
    `total_population` INT NOT NULL COMMENT '总人口数',
    `initial_infected` INT NOT NULL COMMENT '初始感染数',
    `initial_exposed` INT DEFAULT NULL COMMENT '初始潜伏者数',
    `initial_recovered` INT DEFAULT 0 COMMENT '初始康复者数',
    `incubation_period` DECIMAL(4, 2) DEFAULT 5.0 COMMENT '潜伏期（天）',
    `infectious_period` DECIMAL(4, 2) DEFAULT 7.0 COMMENT '传染期（天）',
    `intervention_factor` DECIMAL(3, 2) DEFAULT 1.0 COMMENT '防控措施影响因子（0-1，1表示无防控）',
    `peak_infection` INT COMMENT '预测峰值感染数',
    `peak_date` DATE COMMENT '预测峰值日期',
    `risk_level` VARCHAR(10) COMMENT '风险等级：低/中/高',
    `prediction_data` JSON COMMENT '预测详细数据（JSON格式：dates和values数组）',
    `user_id` BIGINT COMMENT '创建预测的用户ID',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-有效，0-已删除',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_prediction_date` (`prediction_date`),
    INDEX `idx_city_id` (`city_id`),
    INDEX `idx_algorithm` (`algorithm`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_created_at` (`created_at`),
    FOREIGN KEY (`city_id`) REFERENCES `cities`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SEIR模型预测结果表';

-- ============================================
-- 4. 流感模型参数配置表
-- 用途：存储不同场景下的模型参数配置（如：不同防控措施）
-- ============================================
CREATE TABLE IF NOT EXISTS `flu_model_config` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `config_name` VARCHAR(100) NOT NULL COMMENT '配置名称（如：无防控措施、轻度防控、严格防控）',
    `config_type` VARCHAR(20) DEFAULT 'scenario' COMMENT '配置类型：scenario-场景，default-默认',
    `r0` DECIMAL(5, 2) NOT NULL COMMENT '基本传染数',
    `incubation_period` DECIMAL(4, 2) DEFAULT 5.0 COMMENT '潜伏期（天）- 流感通常3-7天',
    `infectious_period` DECIMAL(4, 2) DEFAULT 7.0 COMMENT '传染期（天）- 流感通常5-10天',
    `intervention_factor` DECIMAL(3, 2) DEFAULT 1.0 COMMENT '防控措施影响因子',
    `vaccination_rate` DECIMAL(4, 3) DEFAULT 0.0 COMMENT '疫苗接种率（0-1）',
    `mortality_rate` DECIMAL(6, 5) DEFAULT 0.0001 COMMENT '死亡率（流感通常很低，约0.01%-0.1%）',
    `description` TEXT COMMENT '配置说明',
    `is_default` TINYINT DEFAULT 0 COMMENT '是否默认配置：1-是，0-否',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_config_type` (`config_type`),
    INDEX `idx_is_default` (`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流感模型参数配置表';

-- ============================================
-- 5. 预测结果详情表（可选，用于存储每日预测值）
-- 用途：如果预测数据量很大，可以单独存储每日预测值
-- ============================================
CREATE TABLE IF NOT EXISTS `flu_prediction_details` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `prediction_id` BIGINT NOT NULL COMMENT '预测记录ID（关联flu_seir_predictions.id）',
    `predict_date` DATE NOT NULL COMMENT '预测的日期',
    `day_index` INT NOT NULL COMMENT '预测的第几天（从1开始）',
    `susceptible` INT COMMENT '易感者数量（S）',
    `exposed` INT COMMENT '潜伏者数量（E）',
    `infected` INT COMMENT '感染者数量（I）',
    `recovered` INT COMMENT '康复者数量（R）',
    `new_cases` INT COMMENT '当日新增病例',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_prediction_id` (`prediction_id`),
    INDEX `idx_predict_date` (`predict_date`),
    FOREIGN KEY (`prediction_id`) REFERENCES `flu_seir_predictions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预测结果详情表（每日数据）';

-- ============================================
-- 注意：城市配置数据已迁移到 region_tables.sql
-- 请先执行 region_tables.sql 创建地区表和初始化数据
-- ============================================

-- ============================================
-- 初始化数据：插入默认模型配置
-- ============================================
INSERT INTO `flu_model_config` (`config_name`, `config_type`, `r0`, `incubation_period`, `infectious_period`, `intervention_factor`, `description`, `is_default`) VALUES
('默认配置', 'default', 1.4, 5.0, 7.0, 1.0, '流感默认参数：潜伏期5天，传染期7天，R0=1.4', 1),
('无防控措施', 'scenario', 2.0, 5.0, 7.0, 1.0, '无任何防控措施场景，R0较高', 0),
('轻度防控', 'scenario', 1.2, 5.0, 7.0, 0.8, '轻度防控措施（如：部分场所戴口罩）', 0),
('严格防控', 'scenario', 0.8, 5.0, 7.0, 0.5, '严格防控措施（如：封控、大规模检测）', 0)
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 示例：插入模拟历史数据（可选，用于测试）
-- ============================================
-- 注意：以下为示例数据，实际使用时应该从真实数据源导入
-- 使用 city_id 而不是 city_name
/*
INSERT INTO `flu_daily_cases` (`date`, `city_id`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`) 
SELECT '2024-01-01', c.id, 100, 80, 20, 0, 10, 5 FROM cities c WHERE c.city_name = '清远市'
UNION ALL SELECT '2024-01-02', c.id, 115, 90, 25, 0, 15, 5 FROM cities c WHERE c.city_name = '清远市'
UNION ALL SELECT '2024-01-03', c.id, 135, 105, 30, 0, 20, 5 FROM cities c WHERE c.city_name = '清远市';
*/

