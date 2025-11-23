#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看表结构
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
print("📋 cities 表结构")
print("=" * 80)
cursor.execute("DESCRIBE cities")
for row in cursor.fetchall():
    print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10}")

print("\n" + "=" * 80)
print("📋 flu_daily_cases 表结构")
print("=" * 80)
cursor.execute("DESCRIBE flu_daily_cases")
for row in cursor.fetchall():
    print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10}")

print("\n" + "=" * 80)
print("📊 cities 表样例数据 (前5条)")
print("=" * 80)
cursor.execute("SELECT * FROM cities LIMIT 5")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 80)
for row in cursor.fetchall():
    print(" | ".join(str(x) for x in row))

cursor.close()
conn.close()
