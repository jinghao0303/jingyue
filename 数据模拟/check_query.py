#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查前端查询逻辑
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
print("🔍 检查前端可能的查询方式")
print("=" * 80)

# 1. 检查是否有默认城市或特定city_id
print("\n1️⃣ 检查可能被查询的城市")
print("-" * 80)

# 尝试几种可能的查询方式
test_queries = [
    ("按city_id=1查询", "SELECT * FROM flu_daily_cases WHERE city_id = 1 AND date >= '2025-11-20' ORDER BY date LIMIT 5"),
    ("按城市名查询", "SELECT f.* FROM flu_daily_cases f JOIN cities c ON f.city_id = c.id WHERE c.city_name = '北京市' AND f.date >= '2025-11-20' ORDER BY f.date LIMIT 5"),
    ("查询所有城市最新数据", "SELECT city_id, MAX(date) as latest, COUNT(*) FROM flu_daily_cases WHERE date >= '2025-11-20' GROUP BY city_id LIMIT 10"),
]

for name, query in test_queries:
    print(f"\n{name}:")
    print(f"SQL: {query}")
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            print(f"✅ 返回 {len(results)} 条结果")
            for row in results[:3]:
                print(f"  {row}")
        else:
            print("❌ 没有数据")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

# 2. 检查刚生成的数据
print("\n\n2️⃣ 检查最近生成的数据")
print("-" * 80)
cursor.execute("""
    SELECT city_id, COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
    FROM flu_daily_cases
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    GROUP BY city_id
    ORDER BY city_id
    LIMIT 10
""")
print("最近1小时内生成的数据:")
results = cursor.fetchall()
if results:
    print(f"{'city_id':<10} {'记录数':<10} {'最小日期':<15} {'最大日期':<15}")
    print("-" * 60)
    for row in results:
        print(f"{row[0]:<10} {row[1]:<10} {str(row[2]):<15} {str(row[3]):<15}")
else:
    print("⚠️ 最近1小时没有新生成的数据")

# 3. 检查北京市11月20-26日的详细数据
print("\n\n3️⃣ 北京市11月20-26日的数据（按created_at排序）")
print("-" * 80)
cursor.execute("""
    SELECT date, active, confirmed, new_cases, created_at
    FROM flu_daily_cases
    WHERE city_id = 1
    AND date BETWEEN '2025-11-20' AND '2025-11-26'
    ORDER BY date, created_at DESC
""")
results = cursor.fetchall()
print(f"{'日期':<15} {'active':<10} {'confirmed':<12} {'new_cases':<10} {'创建时间':<20}")
print("-" * 80)
for row in results:
    print(f"{str(row[0]):<15} {row[1]:<10} {row[2]:<12} {row[3]:<10} {str(row[4]):<20}")

# 4. 检查是否有其他city_id的数据
print("\n\n4️⃣ 检查各城市11月23日的数据情况")
print("-" * 80)
cursor.execute("""
    SELECT c.city_name, f.city_id, f.active, f.confirmed, f.new_cases
    FROM flu_daily_cases f
    JOIN cities c ON f.city_id = c.id
    WHERE f.date = '2025-11-23'
    ORDER BY f.city_id
    LIMIT 20
""")
results = cursor.fetchall()
if results:
    print(f"{'城市':<15} {'city_id':<10} {'active':<10} {'confirmed':<12} {'new_cases':<10}")
    print("-" * 70)
    for row in results:
        print(f"{row[0]:<15} {row[1]:<10} {row[2]:<10} {row[3]:<12} {row[4]:<10}")
else:
    print("❌ 11月23日没有任何数据")

print("\n" + "=" * 80)
print("✅ 检查完成")
print("=" * 80)

cursor.close()
conn.close()
