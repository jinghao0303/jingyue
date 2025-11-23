#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库数据查看脚本
"""

import pymysql
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '629629',
    'database': 'infectious_disease_data',
    'charset': 'utf8mb4'
}


def connect_db():
    """连接数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功\n")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


def check_tables(conn):
    """检查数据库中的表"""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("=" * 80)
    print("📋 数据库表列表")
    print("=" * 80)
    if tables:
        for idx, table in enumerate(tables, 1):
            print(f"{idx}. {table[0]}")
    else:
        print("❌ 数据库中没有表")
    print()
    cursor.close()
    return [table[0] for table in tables]


def check_cities(conn):
    """查看城市表数据"""
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🏙️  城市表 (cities) 数据")
    print("=" * 80)
    
    try:
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'cities'")
        if not cursor.fetchone():
            print("❌ cities 表不存在")
            cursor.close()
            return
        
        # 统计城市数量
        cursor.execute("SELECT COUNT(*) FROM cities")
        count = cursor.fetchone()[0]
        print(f"📊 总城市数: {count}\n")
        
        if count == 0:
            print("❌ cities 表为空")
            cursor.close()
            return
        
        # 显示所有城市
        cursor.execute("""
            SELECT id, city_name, total_population, gdp_per_capita, climate_zone, city_tier 
            FROM cities 
            ORDER BY id
        """)
        cities = cursor.fetchall()
        
        print(f"{'ID':<5} {'城市名称':<15} {'人口':<12} {'人均GDP':<10} {'气候':<10} {'等级':<5}")
        print("-" * 80)
        for city in cities:
            city_id, name, pop, gdp, climate, tier = city
            print(f"{city_id:<5} {name:<15} {pop:>10,}  {gdp or 0:>8,}  {climate or 'N/A':<10} {tier or 'N/A':<5}")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        cursor.close()
    
    print()


def check_flu_data(conn):
    """查看流感数据表"""
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🦠 流感数据表 (flu_daily_cases) 统计")
    print("=" * 80)
    
    try:
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'flu_daily_cases'")
        if not cursor.fetchone():
            print("❌ flu_daily_cases 表不存在")
            cursor.close()
            return
        
        # 统计总记录数
        cursor.execute("SELECT COUNT(*) FROM flu_daily_cases")
        total_records = cursor.fetchone()[0]
        print(f"📊 总记录数: {total_records:,}\n")
        
        if total_records == 0:
            print("❌ flu_daily_cases 表为空")
            cursor.close()
            return
        
        # 日期范围
        cursor.execute("SELECT MIN(date), MAX(date) FROM flu_daily_cases")
        min_date, max_date = cursor.fetchone()
        print(f"📅 日期范围: {min_date} 至 {max_date}")
        
        # 计算天数
        if min_date and max_date:
            days = (max_date - min_date).days + 1
            print(f"📅 数据天数: {days} 天\n")
        
        # 每个城市的数据量
        cursor.execute("""
            SELECT c.city_name, COUNT(*) as record_count
            FROM flu_daily_cases f
            JOIN cities c ON f.city_id = c.id
            GROUP BY c.city_name
            ORDER BY record_count DESC
            LIMIT 10
        """)
        city_records = cursor.fetchall()
        
        if city_records:
            print("📊 各城市数据记录数 (Top 10):")
            print(f"{'城市名称':<20} {'记录数':<10}")
            print("-" * 35)
            for city_name, count in city_records:
                print(f"{city_name:<20} {count:>8,}")
            print()
        
        # 全国当前活跃病例统计
        cursor.execute("""
            SELECT SUM(active), SUM(confirmed), SUM(recovered), SUM(deaths)
            FROM flu_daily_cases 
            WHERE date = (SELECT MAX(date) FROM flu_daily_cases)
        """)
        stats = cursor.fetchone()
        if stats and stats[0] is not None:
            active, confirmed, recovered, deaths = stats
            print(f"🔥 最新数据统计 (截至 {max_date}):")
            print(f"   ├─ 全国活跃病例: {active:,}")
            print(f"   ├─ 累计确诊: {confirmed:,}")
            print(f"   ├─ 累计康复: {recovered:,}")
            print(f"   └─ 累计死亡: {deaths:,}\n")
        
        # Top 5 活跃病例最多的城市
        cursor.execute("""
            SELECT c.city_name, f.active, f.new_cases, f.hospitalized, f.severe
            FROM flu_daily_cases f
            JOIN cities c ON f.city_id = c.id
            WHERE f.date = (SELECT MAX(date) FROM flu_daily_cases)
            ORDER BY f.active DESC
            LIMIT 5
        """)
        top_cities = cursor.fetchall()
        
        if top_cities:
            print("🔥 活跃病例最多的5个城市:")
            print(f"{'排名':<5} {'城市':<15} {'活跃':<10} {'新增':<10} {'住院':<10} {'重症':<10}")
            print("-" * 70)
            for rank, (city, active, new_cases, hosp, severe) in enumerate(top_cities, 1):
                print(f"{rank:<5} {city:<15} {active:>8,}  {new_cases or 0:>8,}  {hosp or 0:>8,}  {severe or 0:>8,}")
            print()
        
        # 显示某个城市的最近7天数据示例
        cursor.execute("""
            SELECT c.city_name, f.date, f.active, f.new_cases, f.confirmed, f.recovered
            FROM flu_daily_cases f
            JOIN cities c ON f.city_id = c.id
            WHERE c.id = (SELECT id FROM cities LIMIT 1)
            ORDER BY f.date DESC
            LIMIT 7
        """)
        recent_data = cursor.fetchall()
        
        if recent_data:
            city_name = recent_data[0][0]
            print(f"📈 {city_name} 最近7天数据:")
            print(f"{'日期':<12} {'活跃':<10} {'新增':<10} {'累计确诊':<12} {'累计康复':<12}")
            print("-" * 70)
            for row in recent_data:
                _, date, active, new_cases, confirmed, recovered = row
                print(f"{date}  {active:>8,}  {new_cases or 0:>8,}  {confirmed:>10,}  {recovered:>10,}")
            print()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()


def check_data_quality(conn):
    """检查数据质量"""
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🔍 数据质量检查")
    print("=" * 80)
    
    try:
        # 检查是否有空值
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN active IS NULL THEN 1 ELSE 0 END) as null_active,
                SUM(CASE WHEN confirmed IS NULL THEN 1 ELSE 0 END) as null_confirmed,
                SUM(CASE WHEN recovered IS NULL THEN 1 ELSE 0 END) as null_recovered,
                COUNT(*) as total
            FROM flu_daily_cases
        """)
        null_check = cursor.fetchone()
        
        if null_check:
            null_active, null_confirmed, null_recovered, total = null_check
            print(f"📊 空值检查 (总记录数: {total:,}):")
            print(f"   ├─ active 为空: {null_active:,} ({null_active/total*100:.2f}%)")
            print(f"   ├─ confirmed 为空: {null_confirmed:,} ({null_confirmed/total*100:.2f}%)")
            print(f"   └─ recovered 为空: {null_recovered:,} ({null_recovered/total*100:.2f}%)\n")
        
        # 检查逻辑一致性
        cursor.execute("""
            SELECT COUNT(*) 
            FROM flu_daily_cases 
            WHERE active != (confirmed - recovered - deaths)
            AND active IS NOT NULL 
            AND confirmed IS NOT NULL 
            AND recovered IS NOT NULL 
            AND deaths IS NOT NULL
        """)
        inconsistent = cursor.fetchone()[0]
        
        if inconsistent > 0:
            print(f"⚠️  发现 {inconsistent:,} 条记录的 active 值与 (confirmed - recovered - deaths) 不一致")
        else:
            print(f"✅ 所有记录的 active 值与 (confirmed - recovered - deaths) 一致")
        
        print()
        
    except Exception as e:
        print(f"❌ 数据质量检查失败: {e}")
    finally:
        cursor.close()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 数据库数据查看工具")
    print("=" * 80)
    print(f"📅 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    # 连接数据库
    conn = connect_db()
    if not conn:
        return
    
    try:
        # 检查表
        tables = check_tables(conn)
        
        # 检查城市表
        if 'cities' in tables:
            check_cities(conn)
        
        # 检查流感数据表
        if 'flu_daily_cases' in tables:
            check_flu_data(conn)
            check_data_quality(conn)
        
        print("=" * 80)
        print("✅ 数据库查看完成")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print("✅ 数据库连接已关闭\n")


if __name__ == "__main__":
    main()
