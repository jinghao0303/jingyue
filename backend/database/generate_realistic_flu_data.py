#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成真实的流感每日病例模拟数据
特点：
1. 模拟真实的流感传播模式（有周期性波动、季节性趋势）
2. 数据之间有逻辑关系（活跃病例 = 累计确诊 - 累计康复 - 累计死亡）
3. 每个城市有不同的基础参数，模拟不同城市的特点
4. 包含随机波动，但保持合理的趋势
"""

import pymysql
from datetime import date, timedelta
import random
import math
from config import Config

# 从配置获取数据库连接信息
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '629629',
    'database': 'Infectious_disease_data',
    'charset': 'utf8mb4'
}

# 每个城市的基础参数（模拟不同城市的特点）
CITY_BASE_PARAMS = {
    '北京市': {
        'base_confirmed': 1200,  # 基础累计确诊
        'base_active': 350,      # 基础活跃病例
        'base_recovered': 800,   # 基础累计康复
        'population_factor': 1.5,  # 人口因子（大城市）
        'transmission_rate': 1.2,  # 传播率
    },
    '上海市': {
        'base_confirmed': 1100,
        'base_active': 320,
        'base_recovered': 750,
        'population_factor': 1.4,
        'transmission_rate': 1.15,
    },
    '广州市': {
        'base_confirmed': 850,
        'base_active': 280,
        'base_recovered': 550,
        'population_factor': 1.3,
        'transmission_rate': 1.25,
    },
    '深圳市': {
        'base_confirmed': 900,
        'base_active': 300,
        'base_recovered': 580,
        'population_factor': 1.35,
        'transmission_rate': 1.3,
    },
    '清远市': {
        'base_confirmed': 100,
        'base_active': 80,
        'base_recovered': 20,
        'population_factor': 0.8,
        'transmission_rate': 1.1,
    },
    '重庆市': {
        'base_confirmed': 950,
        'base_active': 290,
        'base_recovered': 640,
        'population_factor': 1.25,
        'transmission_rate': 1.2,
    },
    '成都市': {
        'base_confirmed': 780,
        'base_active': 260,
        'base_recovered': 500,
        'population_factor': 1.2,
        'transmission_rate': 1.18,
    },
    '西安市': {
        'base_confirmed': 720,
        'base_active': 240,
        'base_recovered': 460,
        'population_factor': 1.15,
        'transmission_rate': 1.15,
    },
}


def get_city_list(conn, include_all=False):
    """
    获取城市列表
    :param include_all: 如果为True，获取所有城市（包括禁用的）；如果为False，只获取启用的
    """
    cursor = conn.cursor()
    if include_all:
        cursor.execute("SELECT id, city_name, status FROM cities ORDER BY city_name")
    else:
        cursor.execute("SELECT id, city_name, status FROM cities WHERE status = 1 ORDER BY city_name")
    cities = cursor.fetchall()
    
    # 统计信息
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as enabled FROM cities")
    stats = cursor.fetchone()
    cursor.close()
    
    return cities, stats


def generate_seasonal_factor(day_index):
    """
    生成季节性因子
    模拟流感的季节性特征：秋冬季节更容易传播
    """
    # 假设从10月1日开始，10-12月是高峰期
    month = (day_index // 30) % 12 + 10  # 10月开始
    if month in [10, 11, 12, 1, 2]:  # 秋冬季节
        return 1.0 + random.uniform(0.1, 0.3)
    else:  # 春夏季节
        return 0.7 + random.uniform(0, 0.2)


def generate_weekly_pattern(day_index):
    """
    生成周期性波动（每周模式）
    模拟周末效应：周末可能检测较少，工作日检测较多
    """
    day_of_week = day_index % 7
    if day_of_week in [5, 6]:  # 周末
        return 0.85 + random.uniform(-0.1, 0.1)
    else:  # 工作日
        return 1.0 + random.uniform(-0.15, 0.15)


def generate_realistic_new_cases(base_new_cases, day_index, seasonal_factor, weekly_factor, transmission_rate):
    """
    生成真实的新增病例数
    考虑季节性、周期性、传播率等因素
    """
    # 基础新增病例
    new_cases = base_new_cases
    
    # 应用季节性因子
    new_cases *= seasonal_factor
    
    # 应用周期性因子
    new_cases *= weekly_factor
    
    # 应用传播率
    new_cases *= transmission_rate
    
    # 添加随机波动（±20%）
    new_cases *= (1 + random.uniform(-0.2, 0.2))
    
    # 确保不为负数
    new_cases = max(1, int(new_cases))
    
    return new_cases


def generate_realistic_recovered(new_cases, day_index, base_recovery_rate=0.15):
    """
    生成真实的新增康复数
    康复人数通常与新增病例相关，但有延迟
    """
    # 基础康复率（每天约15%的活跃病例会康复）
    recovery_rate = base_recovery_rate
    
    # 添加一些波动
    recovery_rate *= (1 + random.uniform(-0.1, 0.1))
    
    # 新增康复数 = 新增病例数 * 康复率 * 一个系数（考虑历史累积）
    new_recovered = int(new_cases * recovery_rate * random.uniform(0.8, 1.2))
    
    # 确保不为负数，且不超过新增病例
    new_recovered = max(0, min(new_recovered, new_cases))
    
    return new_recovered


def generate_realistic_deaths(new_cases, day_index):
    """
    生成真实的死亡数（流感死亡率很低）
    """
    # 流感死亡率约0.01%-0.1%
    death_rate = random.uniform(0.0001, 0.001)
    
    # 死亡数 = 新增病例 * 死亡率
    new_deaths = int(new_cases * death_rate)
    
    # 大多数情况下为0，偶尔有1-2例
    if random.random() < 0.95:  # 95%的概率为0
        return 0
    else:
        return min(new_deaths, 2)  # 最多2例


def generate_city_data(conn, city_id, city_name, start_date, end_date):
    """
    为单个城市生成从start_date到end_date的所有数据
    """
    cursor = conn.cursor()
    
    # 获取城市基础参数（如果没有则使用默认值，根据城市名称估算）
    if city_name in CITY_BASE_PARAMS:
        params = CITY_BASE_PARAMS[city_name]
    else:
        # 根据城市名称估算参数（大城市通常数据更多）
        if '市' in city_name:
            # 中等城市
            base_value = random.randint(150, 400)
        else:
            # 小城市
            base_value = random.randint(80, 200)
        
        params = {
            'base_confirmed': base_value * 1.5,
            'base_active': base_value,
            'base_recovered': base_value * 0.3,
            'population_factor': random.uniform(0.8, 1.2),
            'transmission_rate': random.uniform(1.05, 1.25),
        }
    
    # 初始化累计数据
    confirmed = params['base_confirmed']
    recovered = params['base_recovered']
    deaths = 0  # 从0开始累计
    active = params['base_active']
    
    # 计算日期范围
    current_date = start_date
    day_index = 0
    data_list = []
    
    while current_date <= end_date:
        # 生成季节性因子
        seasonal_factor = generate_seasonal_factor(day_index)
        
        # 生成周期性因子
        weekly_factor = generate_weekly_pattern(day_index)
        
        # 生成新增病例（基础值根据城市规模调整）
        base_new_cases = 15 * params['population_factor']
        new_cases = generate_realistic_new_cases(
            base_new_cases, 
            day_index, 
            seasonal_factor, 
            weekly_factor,
            params['transmission_rate']
        )
        
        # 生成新增康复
        new_recovered = generate_realistic_recovered(new_cases, day_index)
        
        # 生成新增死亡
        new_deaths = generate_realistic_deaths(new_cases, day_index)
        
        # 更新累计数据
        confirmed += new_cases
        recovered += new_recovered
        deaths += new_deaths
        
        # 计算活跃病例（活跃 = 累计确诊 - 累计康复 - 累计死亡）
        active = max(0, confirmed - recovered - deaths)
        
        # 生成住院人数（约为活跃病例的30-50%）
        hospitalized = int(active * random.uniform(0.3, 0.5))
        
        # 生成重症病例（约为活跃病例的5-10%）
        severe = int(active * random.uniform(0.05, 0.1))
        
        # 准备插入数据
        data_list.append((
            current_date,
            city_id,
            confirmed,
            active,
            recovered,
            deaths,
            new_cases,
            new_recovered,
            new_deaths,
            hospitalized,
            severe,
            '模拟数据'
        ))
        
        # 移动到下一天
        current_date += timedelta(days=1)
        day_index += 1
    
    # 批量插入数据
    insert_sql = """
    INSERT INTO flu_daily_cases 
    (date, city_id, confirmed, active, recovered, deaths, 
     new_cases, new_recovered, new_deaths, hospitalized, severe, data_source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        confirmed = VALUES(confirmed),
        active = VALUES(active),
        recovered = VALUES(recovered),
        deaths = VALUES(deaths),
        new_cases = VALUES(new_cases),
        new_recovered = VALUES(new_recovered),
        new_deaths = VALUES(new_deaths),
        hospitalized = VALUES(hospitalized),
        severe = VALUES(severe),
        updated_at = CURRENT_TIMESTAMP
    """
    
    cursor.executemany(insert_sql, data_list)
    conn.commit()
    cursor.close()
    
    print(f"✓ {city_name}: 已生成 {len(data_list)} 条数据 ({start_date} 至 {end_date})")


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成真实的流感每日病例数据")
    print("=" * 60)
    
    # 连接数据库
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return
    
    try:
        # 获取所有城市（包括禁用的，因为可能只是暂时禁用）
        cities, stats = get_city_list(conn, include_all=True)
        total_cities, enabled_cities = stats
        
        if not cities:
            print("✗ 数据库中没有任何城市数据，请先导入城市数据")
            print("   可以执行: mysql -u root -p < backend/database/region_tables.sql")
            return
        
        print(f"✓ 数据库中共有 {total_cities} 个城市（其中 {enabled_cities} 个启用）")
        print(f"✓ 将为所有 {len(cities)} 个城市生成数据\n")
        
        # 设置日期范围（从2024-10-01到今天）
        start_date = date(2024, 10, 1)
        end_date = date.today()
        
        print(f"✓ 日期范围: {start_date} 至 {end_date}")
        print(f"✓ 共 { (end_date - start_date).days + 1 } 天\n")
        
        # 为每个城市生成数据
        for city_info in cities:
            if len(city_info) == 3:
                city_id, city_name, city_status = city_info
            else:
                city_id, city_name = city_info
                city_status = 1
            
            try:
                status_text = "（启用）" if city_status == 1 else "（禁用）"
                generate_city_data(conn, city_id, city_name, start_date, end_date)
            except Exception as e:
                print(f"✗ {city_name}: 生成数据失败 - {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 60)
        print("数据生成完成！")
        print("=" * 60)
        
        # 验证数据
        cursor = conn.cursor()
        
        # 显示城市总数统计
        cursor.execute("SELECT COUNT(*) FROM cities")
        total_cities_in_db = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cities WHERE status = 1")
        enabled_cities_in_db = cursor.fetchone()[0]
        
        print(f"\n城市统计:")
        print(f"  数据库中共有城市: {total_cities_in_db} 个")
        print(f"  其中启用状态: {enabled_cities_in_db} 个")
        print(f"  已生成数据的城市: {len(cities)} 个")
        
        cursor.execute("""
            SELECT 
                c.city_name,
                COUNT(*) as record_count,
                MIN(fdc.date) as start_date,
                MAX(fdc.date) as end_date,
                AVG(fdc.active) as avg_active,
                MAX(fdc.active) as max_active
            FROM flu_daily_cases fdc
            JOIN cities c ON fdc.city_id = c.id
            GROUP BY c.id, c.city_name
            ORDER BY c.city_name
        """)
        
        results = cursor.fetchall()
        print("\n数据统计:")
        print("-" * 70)
        print(f"{'城市':<15} {'记录数':<10} {'开始日期':<12} {'结束日期':<12} {'平均活跃':<12} {'最大活跃':<10}")
        print("-" * 70)
        for row in results:
            city_name, count, start, end, avg_active, max_active = row
            print(f"{city_name:<15} {count:<10} {str(start):<12} {str(end):<12} {avg_active:<12.1f} {max_active:<10}")
        
        if total_cities_in_db > len(cities):
            print(f"\n⚠️  注意：数据库中有 {total_cities_in_db} 个城市，但只生成了 {len(cities)} 个城市的数据")
            print("   如果需要为所有城市生成数据，请确保所有城市的 status = 1")
            print("   或者修改脚本，为所有城市（包括禁用的）生成数据")
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 生成数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n✓ 数据库连接已关闭")


if __name__ == '__main__':
    main()

