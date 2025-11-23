-- ============================================
-- 广东省流感模拟数据导入脚本（最终版）
-- 用途：为LSTM模型训练提供历史数据
-- 数据范围：2024-10-01 至 2025-01-31（123天）
-- 覆盖城市：清远市、广州市、深圳市
-- 使用方法：直接执行此文件即可
-- ============================================

USE Infectious_disease_data;

-- ============================================
-- 插入清远市数据
-- ============================================
INSERT INTO `flu_daily_cases` (`date`, `city_id`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`, `new_deaths`, `hospitalized`, `severe`, `data_source`)
SELECT 
    DATE_ADD('2024-10-01', INTERVAL n DAY) as date,
    (SELECT id FROM cities WHERE city_name = '清远市' LIMIT 1) as city_id,
    100 + n * 1 + (n * n / 100) as confirmed,
    80 + n * 0.8 + 
    (CASE WHEN n % 7 < 2 THEN -5 ELSE 0 END) +
    (CASE WHEN n % 14 < 7 THEN 10 ELSE -5 END) +
    (n % 10 - 5) as active,
    20 + n * 0.4 as recovered,
    0 as deaths,
    10 + (n % 7) + (CASE WHEN n % 14 < 7 THEN 3 ELSE -2 END) as new_cases,
    5 + (n % 3) as new_recovered,
    0 as new_deaths,
    15 + n * 0.3 as hospitalized,
    2 + (n % 3) as severe,
    '模拟数据' as data_source
FROM (
    SELECT 
        (@n := @n + 1) as n
    FROM 
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t2,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2) t3,
    (SELECT @n := -1) r
    LIMIT 123
) numbers
ON DUPLICATE KEY UPDATE 
    `active` = VALUES(`active`),
    `confirmed` = VALUES(`confirmed`),
    `recovered` = VALUES(`recovered`),
    `new_cases` = VALUES(`new_cases`),
    `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 插入广州市数据
-- ============================================
INSERT INTO `flu_daily_cases` (`date`, `city_id`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`, `new_deaths`, `hospitalized`, `severe`, `data_source`)
SELECT 
    DATE_ADD('2024-10-01', INTERVAL n DAY) as date,
    (SELECT id FROM cities WHERE city_name = '广州市' LIMIT 1) as city_id,
    500 + n * 3 + (n * n / 50) as confirmed,
    400 + n * 2.8 + 
    (CASE WHEN n % 7 < 2 THEN -15 ELSE 0 END) +
    (CASE WHEN n % 14 < 7 THEN 25 ELSE -10 END) +
    (n % 15 - 7) as active,
    100 + n * 0.7 as recovered,
    0 as deaths,
    35 + (n % 8) + (CASE WHEN n % 14 < 7 THEN 8 ELSE -5 END) as new_cases,
    20 + (n % 4) as new_recovered,
    0 as new_deaths,
    60 + n * 1.2 as hospitalized,
    8 + (n % 4) as severe,
    '模拟数据' as data_source
FROM (
    SELECT 
        (@n := @n + 1) as n
    FROM 
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t2,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2) t3,
    (SELECT @n := -1) r
    LIMIT 123
) numbers
ON DUPLICATE KEY UPDATE 
    `active` = VALUES(`active`),
    `confirmed` = VALUES(`confirmed`),
    `recovered` = VALUES(`recovered`),
    `new_cases` = VALUES(`new_cases`),
    `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 插入深圳市数据
-- ============================================
INSERT INTO `flu_daily_cases` (`date`, `city_id`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`, `new_deaths`, `hospitalized`, `severe`, `data_source`)
SELECT 
    DATE_ADD('2024-10-01', INTERVAL n DAY) as date,
    (SELECT id FROM cities WHERE city_name = '深圳市' LIMIT 1) as city_id,
    450 + n * 2.8 + (n * n / 55) as confirmed,
    360 + n * 2.5 + 
    (CASE WHEN n % 7 < 2 THEN -12 ELSE 0 END) +
    (CASE WHEN n % 14 < 7 THEN 22 ELSE -8 END) +
    (n % 12 - 6) as active,
    90 + n * 0.6 as recovered,
    0 as deaths,
    32 + (n % 7) + (CASE WHEN n % 14 < 7 THEN 7 ELSE -4 END) as new_cases,
    18 + (n % 3) as new_recovered,
    0 as new_deaths,
    55 + n * 1.1 as hospitalized,
    7 + (n % 3) as severe,
    '模拟数据' as data_source
FROM (
    SELECT 
        (@n := @n + 1) as n
    FROM 
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t2,
    (SELECT 0 UNION SELECT 1 UNION SELECT 2) t3,
    (SELECT @n := -1) r
    LIMIT 123
) numbers
ON DUPLICATE KEY UPDATE 
    `active` = VALUES(`active`),
    `confirmed` = VALUES(`confirmed`),
    `recovered` = VALUES(`recovered`),
    `new_cases` = VALUES(`new_cases`),
    `updated_at` = CURRENT_TIMESTAMP;

-- ============================================
-- 验证数据
-- ============================================
SELECT 
    c.city_name as '城市',
    COUNT(*) as '记录数',
    MIN(fdc.date) as '开始日期',
    MAX(fdc.date) as '结束日期',
    ROUND(AVG(fdc.active), 2) as '平均活跃病例',
    MAX(fdc.active) as '最大活跃病例',
    MIN(fdc.active) as '最小活跃病例',
    ROUND(AVG(fdc.new_cases), 2) as '平均新增病例'
FROM flu_daily_cases fdc
JOIN cities c ON fdc.city_id = c.id
WHERE c.city_name IN ('清远市', '广州市', '深圳市')
  AND fdc.date >= '2024-10-01'
  AND fdc.date <= '2025-01-31'
  AND fdc.data_source = '模拟数据'
GROUP BY c.city_name
ORDER BY c.city_name;
