#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断数据生成问题
"""

import pymysql
from datetime import datetime, timedelta

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
print("🔍 诊断报告")
print("=" * 80)

# 1. 检查哪个城市的数据正在被查询
print("\n1️⃣ 检查前端查询的城市")
print("-" * 80)
cursor.execute("""
    SELECT city_name, id 
    FROM cities 
    WHERE city_name LIKE '%' 
    LIMIT 10
""")
print("前10个城市:")
for row in cursor.fetchall():
    print(f"  {row[0]} (ID: {row[1]})")

# 2. 检查某个特定城市的最近数据
print("\n2️⃣ 检查北京市的最近7天数据")
print("-" * 80)
cursor.execute("""
    SELECT f.date, f.active, f.confirmed, f.new_cases
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    WHERE c.city_name = '北京市'
    ORDER BY f.date DESC
    LIMIT 10
""")
print(f"{'日期':<15} {'active':<10} {'confirmed':<12} {'new_cases':<10}")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{str(row[0]):<15} {row[1]:<10} {row[2]:<12} {row[3]:<10}")

# 3. 检查数据库中各城市的数据量
print("\n3️⃣ 各城市最新数据日期")
print("-" * 80)
cursor.execute("""
    SELECT c.city_name, MAX(f.date) as latest_date, COUNT(*) as record_count
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    GROUP BY c.city_name
    ORDER BY latest_date DESC
    LIMIT 10
""")
print(f"{'城市':<20} {'最新日期':<15} {'记录数':<10}")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]:<20} {str(row[1]):<15} {row[2]:<10}")

# 4. 检查11月20-23日的数据
print("\n4️⃣ 检查11月20-26日北京市的数据")
print("-" * 80)
cursor.execute("""
    SELECT f.date, f.active, f.confirmed, f.recovered, f.deaths, f.new_cases
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    WHERE c.city_name = '北京市'
    AND f.date BETWEEN '2025-11-20' AND '2025-11-26'
    ORDER BY f.date
""")
results = cursor.fetchall()
if results:
    print(f"{'日期':<15} {'active':<10} {'confirmed':<12} {'recovered':<12} {'deaths':<10} {'new_cases':<10}")
    print("-" * 80)
    for row in results:
        print(f"{str(row[0]):<15} {row[1]:<10} {row[2]:<12} {row[3]:<12} {row[4]:<10} {row[5]:<10}")
else:
    print("⚠️ 11月20-26日没有数据！")

# 5. 检查所有城市的status
print("\n5️⃣ 城市状态分布")
print("-" * 80)
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM cities
    GROUP BY status
""")
print("status分布:")
for row in cursor.fetchall():
    status = row[0] if row[0] is not None else 'NULL'
    print(f"  status={status}: {row[1]}个城市")

# 6. 检查是否所有城市都有数据
print("\n6️⃣ 有无数据的城市统计")
print("-" * 80)
cursor.execute("""
    SELECT 
        (SELECT COUNT(*) FROM cities WHERE status = 1) as active_cities,
        (SELECT COUNT(*) FROM cities) as total_cities,
        (SELECT COUNT(DISTINCT city_id) FROM flu_daily_cases) as cities_with_data
""")
row = cursor.fetchone()
print(f"激活城市数 (status=1): {row[0]}")
print(f"总城市数: {row[1]}")
print(f"有流感数据的城市数: {row[2]}")

if row[2] < row[1]:
    print(f"\n⚠️ 警告：有 {row[1] - row[2]} 个城市没有流感数据！")
    
    cursor.execute("""
        SELECT c.id, c.city_name, c.status
        FROM cities c
        LEFT JOIN flu_daily_cases f ON c.id = f.city_id
        WHERE f.id IS NULL
        LIMIT 20
    """)
    print("\n没有数据的城市（前20个）:")
    for row in cursor.fetchall():
        print(f"  ID:{row[0]}, 城市:{row[1]}, status:{row[2]}")

print("\n" + "=" * 80)
print("✅ 诊断完成")
print("=" * 80)

cursor.close()
conn.close()
