-- ============================================
-- 生成流感每日病例模拟数据
-- 用途：清除现有数据并生成从2024-10-01到现在的每日数据
-- 日期：自动计算到今天
-- ============================================

USE Infectious_disease_data;

-- ============================================
-- 第一步：清除所有现有数据
-- 使用 TRUNCATE 而不是 DELETE，避免安全更新模式限制，且速度更快
-- ============================================
TRUNCATE TABLE `flu_daily_cases`;

-- ============================================
-- 第二步：创建临时日期表（从2024-10-01到今天）
-- ============================================
DROP TEMPORARY TABLE IF EXISTS temp_dates;
CREATE TEMPORARY TABLE temp_dates (
    n INT,
    date_val DATE,
    PRIMARY KEY (n)
);

-- 生成日期序列（从2024-10-01到今天，最多500天）
INSERT INTO temp_dates (n, date_val)
SELECT 
    numbers.n,
    DATE_ADD('2024-10-01', INTERVAL numbers.n DAY) as date_val
FROM (
    SELECT 
        (@row_number := @row_number + 1) - 1 as n
    FROM 
        (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1,
        (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t2,
        (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) t3,
        (SELECT @row_number := 0) r
) numbers
WHERE DATE_ADD('2024-10-01', INTERVAL numbers.n DAY) <= CURDATE();

-- ============================================
-- 第三步：为每个城市生成数据
-- ============================================
INSERT INTO `flu_daily_cases` (
    `date`, 
    `city_id`, 
    `confirmed`, 
    `active`, 
    `recovered`, 
    `deaths`, 
    `new_cases`, 
    `new_recovered`, 
    `new_deaths`, 
    `hospitalized`, 
    `severe`, 
    `data_source`
)
SELECT 
    td.date_val as date,
    c.id as city_id,
    -- confirmed: 从100开始，每天递增1，加上一些波动（符合示例：100, 101, 102, 103...）
    CAST(100 + td.n + (td.n % 7) * 0.1 AS UNSIGNED) as confirmed,
    -- active: 从80开始，有波动，模拟活跃病例的变化（符合示例：80, 82, 89, 90...）
    CAST(80 + td.n * 0.5 + 
        (CASE WHEN td.n % 7 < 3 THEN 5 ELSE -3 END) +
        (CASE WHEN td.n % 14 < 7 THEN 8 ELSE -5 END) +
        (td.n % 10 - 5) AS UNSIGNED) as active,
    -- recovered: 从20开始，缓慢增长（符合示例：20, 20, 21, 21...）
    CAST(20 + FLOOR(td.n * 0.3) + (CASE WHEN td.n % 5 = 0 THEN 1 ELSE 0 END) AS UNSIGNED) as recovered,
    -- deaths: 保持为0（流感死亡率很低）
    0 as deaths,
    -- new_cases: 每日新增病例，有波动（符合示例：13, 14, 15, 16...）
    CAST(13 + (td.n % 7) + 
        (CASE WHEN td.n % 14 < 7 THEN 2 ELSE -1 END) AS UNSIGNED) as new_cases,
    -- new_recovered: 每日新增康复，有波动（符合示例：5, 6, 7, 5...）
    CAST(5 + (td.n % 4) + 
        (CASE WHEN td.n % 7 < 4 THEN 1 ELSE -1 END) AS UNSIGNED) as new_recovered,
    -- new_deaths: 保持为0
    0 as new_deaths,
    -- hospitalized: 住院人数，缓慢增长（符合示例：15, 15, 16, 16...）
    CAST(15 + FLOOR(td.n * 0.1) + (CASE WHEN td.n % 5 = 0 THEN 1 ELSE 0 END) AS UNSIGNED) as hospitalized,
    -- severe: 重症病例，有波动（符合示例：2, 3, 4, 2...）
    CAST(2 + (td.n % 5) + 
        (CASE WHEN td.n % 10 < 5 THEN 1 ELSE -1 END) AS UNSIGNED) as severe,
    '模拟数据' as data_source
FROM 
    cities c
CROSS JOIN
    temp_dates td
WHERE 
    c.status = 1
ORDER BY c.id, td.date_val;

-- 清理临时表
DROP TEMPORARY TABLE IF EXISTS temp_dates;

-- ============================================
-- 第三步：验证数据
-- ============================================
SELECT 
    c.city_name as '城市',
    COUNT(*) as '记录数',
    MIN(fdc.date) as '开始日期',
    MAX(fdc.date) as '结束日期',
    ROUND(AVG(fdc.active), 2) as '平均活跃病例',
    MAX(fdc.active) as '最大活跃病例',
    MIN(fdc.active) as '最小活跃病例',
    ROUND(AVG(fdc.new_cases), 2) as '平均新增病例',
    SUM(fdc.confirmed) as '累计确诊总数'
FROM flu_daily_cases fdc
JOIN cities c ON fdc.city_id = c.id
GROUP BY c.id, c.city_name
ORDER BY c.city_name;

-- ============================================
-- 第四步：显示数据示例（前10条）
-- ============================================
SELECT 
    fdc.id,
    fdc.date,
    fdc.city_id,
    c.city_name,
    fdc.confirmed,
    fdc.active,
    fdc.recovered,
    fdc.deaths,
    fdc.new_cases,
    fdc.new_recovered,
    fdc.new_deaths,
    fdc.hospitalized,
    fdc.severe,
    fdc.data_source
FROM flu_daily_cases fdc
JOIN cities c ON fdc.city_id = c.id
ORDER BY fdc.date, c.city_name
LIMIT 20;

