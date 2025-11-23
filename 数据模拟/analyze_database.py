#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库深度分析
"""

import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '629629',
    'database': 'infectious_disease_data',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 80)
print("🔍 关键信息分析")
print("=" * 80)

# 1. 查看城市总数和人口信息来源
print("\n1️⃣ 城市数据分析")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM cities WHERE status = 1")
active_cities = cursor.fetchone()[0]
print(f"激活的城市数: {active_cities}")

cursor.execute("SELECT COUNT(*) FROM cities")
total_cities = cursor.fetchone()[0]
print(f"总城市数: {total_cities}")

# 2. 检查是否有人口数据表
print("\n2️⃣ 检查人口数据表")
print("-" * 80)
cursor.execute("DESCRIBE city_population")
print("city_population 表结构:")
for row in cursor.fetchall():
    print(f"  {row[0]:<20} {row[1]:<20}")

cursor.execute("SELECT * FROM city_population LIMIT 5")
print("\ncity_population 样例数据:")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 80)
for row in cursor.fetchall():
    print(" | ".join(str(x) for x in row))

# 3. 检查省份数据
print("\n3️⃣ 省份数据")
print("-" * 80)
cursor.execute("SELECT id, province_name FROM provinces LIMIT 10")
print("省份列表 (前10条):")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, 省份: {row[1]}")

# 4. 检查现有流感数据的城市分布
print("\n4️⃣ flu_daily_cases 数据分布")
print("-" * 80)
cursor.execute("""
    SELECT c.city_name, COUNT(*) as count, MIN(f.date) as start_date, MAX(f.date) as end_date
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    GROUP BY c.city_name
    ORDER BY count DESC
    LIMIT 10
""")
print(f"{'城市':<15} {'记录数':<10} {'开始日期':<15} {'结束日期':<15}")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:<15} {row[1]:<10} {str(row[2]):<15} {str(row[3]):<15}")

# 5. 检查哪些城市有数据，哪些没有
print("\n5️⃣ 数据覆盖情况")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(DISTINCT c.id) as cities_with_data
    FROM cities c
    JOIN flu_daily_cases f ON c.id = f.city_id
""")
cities_with_data = cursor.fetchone()[0]
print(f"有流感数据的城市数: {cities_with_data}")
print(f"没有流感数据的城市数: {total_cities - cities_with_data}")

# 6. 查看没有数据的城市（前20个）
print("\n6️⃣ 没有流感数据的城市 (前20个)")
print("-" * 80)
cursor.execute("""
    SELECT c.id, c.city_name, c.province_id
    FROM cities c
    LEFT JOIN flu_daily_cases f ON c.id = f.city_id
    WHERE f.id IS NULL
    LIMIT 20
""")
no_data_cities = cursor.fetchall()
if no_data_cities:
    print(f"{'城市ID':<10} {'城市名称':<20} {'省份ID':<10}")
    print("-" * 50)
    for row in no_data_cities:
        print(f"{row[0]:<10} {row[1]:<20} {row[2]:<10}")
else:
    print("✅ 所有城市都有数据")

# 7. 检查日期范围和数据完整性
print("\n7️⃣ 数据时间范围分析")
print("-" * 80)
cursor.execute("SELECT MIN(date), MAX(date) FROM flu_daily_cases")
min_date, max_date = cursor.fetchone()
print(f"最早日期: {min_date}")
print(f"最晚日期: {max_date}")

if min_date and max_date:
    days_diff = (max_date - min_date).days + 1
    print(f"时间跨度: {days_diff} 天")
    
    cursor.execute("SELECT COUNT(DISTINCT date) FROM flu_daily_cases")
    unique_dates = cursor.fetchone()[0]
    print(f"实际有数据的天数: {unique_dates}")
    print(f"缺失天数: {days_diff - unique_dates}")

# 8. 检查数据一致性问题示例
print("\n8️⃣ 数据一致性问题示例")
print("-" * 80)
cursor.execute("""
    SELECT c.city_name, f.date, f.active, f.confirmed, f.recovered, f.deaths,
           (f.confirmed - f.recovered - f.deaths) as calculated_active
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    WHERE f.active != (f.confirmed - f.recovered - f.deaths)
    LIMIT 5
""")
print(f"{'城市':<12} {'日期':<12} {'active':<8} {'confirmed':<10} {'recovered':<10} {'deaths':<8} {'计算值':<8}")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:<12} {str(row[1]):<12} {row[2]:<8} {row[3]:<10} {row[4]:<10} {row[5]:<8} {row[6]:<8}")

# 9. 检查是否存在city_population与cities的关联
print("\n9️⃣ city_population 与 cities 关联检查")
print("-" * 80)
cursor.execute("""
    SELECT cp.*, c.city_name 
    FROM city_population cp
    JOIN cities c ON cp.city_id = c.id
    LIMIT 5
""")
print("关联样例数据:")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 80)
for row in cursor.fetchall():
    print(" | ".join(str(x) for x in row))

# 10. 统计每个城市的人口数据
print("\n🔟 城市人口统计 (前10个)")
print("-" * 80)
cursor.execute("""
    SELECT c.city_name, cp.total_population, cp.population_year
    FROM city_population cp
    JOIN cities c ON cp.city_id = c.id
    ORDER BY cp.total_population DESC
    LIMIT 10
""")
print(f"{'城市':<15} {'人口':<15} {'年份':<10}")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]:<15} {row[1]:>13,}  {row[2]:<10}")

print("\n" + "=" * 80)
print("✅ 分析完成")
print("=" * 80)

cursor.close()
conn.close()
