#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空所有流感数据，重新开始
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
print("🗑️  清空所有流感数据")
print("=" * 80)

# 1. 统计当前数据量
cursor.execute("SELECT COUNT(*) FROM flu_daily_cases")
total = cursor.fetchone()[0]
print(f"\n当前数据库中共有 {total:,} 条记录")

# 2. 确认清空
print("\n⚠️  警告：此操作将删除 flu_daily_cases 表中的所有数据！")
print("请在5秒内按 Ctrl+C 取消，否则将继续...\n")

import time
for i in range(5, 0, -1):
    print(f"倒计时: {i} 秒...")
    time.sleep(1)

print("\n开始清空数据...")

# 3. 删除所有数据
cursor.execute("DELETE FROM flu_daily_cases")
deleted = cursor.rowcount
conn.commit()

print(f"✅ 成功删除 {deleted:,} 条记录")

# 4. 验证
cursor.execute("SELECT COUNT(*) FROM flu_daily_cases")
remaining = cursor.fetchone()[0]
print(f"✅ 数据库中剩余 {remaining} 条记录")

# 5. 重置自增ID（可选）
try:
    cursor.execute("ALTER TABLE flu_daily_cases AUTO_INCREMENT = 1")
    conn.commit()
    print("✅ 已重置自增ID")
except Exception as e:
    print(f"⚠️  重置自增ID失败: {e}")

print("\n" + "=" * 80)
print("✅ 清空完成！现在可以运行 generate_flu_data.py 重新生成数据")
print("=" * 80)

cursor.close()
conn.close()
