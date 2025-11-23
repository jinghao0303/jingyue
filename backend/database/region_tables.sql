-- ============================================
-- 地区表结构（省-市-区县三级）
-- 用途：存储完整的地区层级关系，支持多表查询
-- ============================================

USE Infectious_disease_data;

-- ============================================
-- 1. 省份表
-- ============================================
CREATE TABLE IF NOT EXISTS `provinces` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '省份ID',
    `province_code` VARCHAR(10) NOT NULL UNIQUE COMMENT '省份代码（如：44）',
    `province_name` VARCHAR(50) NOT NULL UNIQUE COMMENT '省份名称（如：广东省）',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_province_code` (`province_code`),
    INDEX `idx_province_name` (`province_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='省份表';

-- ============================================
-- 2. 城市表
-- ============================================
CREATE TABLE IF NOT EXISTS `cities` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '城市ID',
    `city_code` VARCHAR(10) NOT NULL UNIQUE COMMENT '城市代码（如：4418）',
    `city_name` VARCHAR(50) NOT NULL COMMENT '城市名称（如：清远市）',
    `province_id` INT NOT NULL COMMENT '所属省份ID',
    `latitude` DECIMAL(10, 6) COMMENT '纬度',
    `longitude` DECIMAL(10, 6) COMMENT '经度',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_city_code` (`city_code`),
    INDEX `idx_city_name` (`city_name`),
    INDEX `idx_province_id` (`province_id`),
    FOREIGN KEY (`province_id`) REFERENCES `provinces`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='城市表';

-- ============================================
-- 3. 区县表（可选，用于更细粒度的数据）
-- ============================================
CREATE TABLE IF NOT EXISTS `districts` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '区县ID',
    `district_code` VARCHAR(10) NOT NULL UNIQUE COMMENT '区县代码',
    `district_name` VARCHAR(50) NOT NULL COMMENT '区县名称（如：清城区）',
    `city_id` INT NOT NULL COMMENT '所属城市ID',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_district_code` (`district_code`),
    INDEX `idx_district_name` (`district_name`),
    INDEX `idx_city_id` (`city_id`),
    FOREIGN KEY (`city_id`) REFERENCES `cities`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='区县表';

-- ============================================
-- 4. 城市人口配置表（关联到cities表）
-- ============================================
CREATE TABLE IF NOT EXISTS `city_population` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `city_id` INT NOT NULL UNIQUE COMMENT '城市ID（关联cities表）',
    `total_population` INT NOT NULL DEFAULT 5000000 COMMENT '总人口数（用于SEIR模型）',
    `population_year` INT COMMENT '人口数据年份',
    `data_source` VARCHAR(100) COMMENT '数据来源',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_city_id` (`city_id`),
    FOREIGN KEY (`city_id`) REFERENCES `cities`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='城市人口配置表';

-- ============================================
-- 初始化省份数据
-- ============================================
INSERT INTO `provinces` (`province_code`, `province_name`) VALUES
('11', '北京市'),
('12', '天津市'),
('13', '河北省'),
('14', '山西省'),
('15', '内蒙古自治区'),
('21', '辽宁省'),
('22', '吉林省'),
('23', '黑龙江省'),
('31', '上海市'),
('32', '江苏省'),
('33', '浙江省'),
('34', '安徽省'),
('35', '福建省'),
('36', '江西省'),
('37', '山东省'),
('41', '河南省'),
('42', '湖北省'),
('43', '湖南省'),
('44', '广东省'),
('45', '广西壮族自治区'),
('46', '海南省'),
('50', '重庆市'),
('51', '四川省'),
('52', '贵州省'),
('53', '云南省'),
('54', '西藏自治区'),
('61', '陕西省'),
('62', '甘肃省'),
('63', '青海省'),
('64', '宁夏回族自治区'),
('65', '新疆维吾尔自治区')
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 初始化城市数据（示例：广东省部分城市）
-- ============================================
INSERT INTO `cities` (`city_code`, `city_name`, `province_id`, `latitude`, `longitude`) 
SELECT 
    '4401', '广州市', p.id, 23.1291, 113.2644 FROM provinces p WHERE p.province_code = '44'
UNION ALL SELECT '4403', '深圳市', p.id, 22.5431, 114.0579 FROM provinces p WHERE p.province_code = '44'
UNION ALL SELECT '4418', '清远市', p.id, 23.7000, 113.0500 FROM provinces p WHERE p.province_code = '44'
UNION ALL SELECT '1101', '北京市', p.id, 39.9042, 116.4074 FROM provinces p WHERE p.province_code = '11'
UNION ALL SELECT '3101', '上海市', p.id, 31.2304, 121.4737 FROM provinces p WHERE p.province_code = '31'
UNION ALL SELECT '3301', '杭州市', p.id, 30.2741, 120.1551 FROM provinces p WHERE p.province_code = '33'
UNION ALL SELECT '3201', '南京市', p.id, 32.0603, 118.7969 FROM provinces p WHERE p.province_code = '32'
UNION ALL SELECT '4201', '武汉市', p.id, 30.5928, 114.3055 FROM provinces p WHERE p.province_code = '42'
UNION ALL SELECT '5101', '成都市', p.id, 30.5728, 104.0668 FROM provinces p WHERE p.province_code = '51'
UNION ALL SELECT '6101', '西安市', p.id, 34.3416, 108.9398 FROM provinces p WHERE p.province_code = '61'
UNION ALL SELECT '5001', '重庆市', p.id, 29.5630, 106.5516 FROM provinces p WHERE p.province_code = '50'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 初始化城市人口数据
-- ============================================
INSERT INTO `city_population` (`city_id`, `total_population`, `population_year`, `data_source`)
SELECT 
    c.id, 
    CASE c.city_code
        WHEN '4418' THEN 4000000  -- 清远市
        WHEN '4401' THEN 15000000 -- 广州市
        WHEN '4403' THEN 13000000 -- 深圳市
        WHEN '1101' THEN 21000000 -- 北京市
        WHEN '3101' THEN 24000000 -- 上海市
        WHEN '3301' THEN 10000000 -- 杭州市
        WHEN '3201' THEN 8500000  -- 南京市
        WHEN '4201' THEN 12000000 -- 武汉市
        WHEN '5101' THEN 16000000 -- 成都市
        WHEN '6101' THEN 12000000 -- 西安市
        WHEN '5001' THEN 31000000 -- 重庆市
        ELSE 5000000
    END,
    2023,
    '统计年鉴'
FROM cities c
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

