#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成广东省流感模拟数据
用于LSTM模型训练
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Tuple

# 设置随机种子，确保可重复
random.seed(42)

# 广东省主要城市配置
CITIES = [
    {'name': '清远市', 'base_active': 80, 'growth_rate': 0.8, 'amplitude': 30},
    {'name': '广州市', 'base_active': 400, 'growth_rate': 2.8, 'amplitude': 80},
    {'name': '深圳市', 'base_active': 360, 'growth_rate': 2.5, 'amplitude': 70},
]

def generate_city_data(city_config: dict, start_date: datetime, days: int) -> List[Tuple]:
    """
    生成单个城市的数据
    
    :param city_config: 城市配置
    :param start_date: 起始日期
    :param days: 生成天数
    :return: 数据列表 [(date, active, confirmed, recovered, new_cases, ...), ...]
    """
    data = []
    base_active = city_config['base_active']
    growth_rate = city_config['growth_rate']
    amplitude = city_config['amplitude']
    
    confirmed = base_active * 1.25  # 初始累计确诊
    recovered = base_active * 0.25   # 初始康复数
    deaths = 0                       # 初始死亡数
    active = confirmed - recovered - deaths  # 初始活跃病例（通过计算得出）
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # 生成新增病例（有趋势、周期性和随机性，但保持合理范围）
        # 基础新增病例（根据城市规模调整）
        base_new_cases = base_active * 0.15
        
        # 趋势：逐步增长（但增长幅度较小）
        trend_factor = 1.0 + (day * growth_rate * 0.01)
        
        # 周期性：模拟周末效应和季节性（使用更温和的波动）
        # 使用较小的周期，避免大幅波动
        cycle_factor = 1.0 + math.sin(day * 0.15) * 0.2  # 波动范围：0.8-1.2
        
        # 随机波动（较小）
        noise_factor = 1.0 + random.gauss(0, 0.1)  # 波动范围：约0.9-1.1
        
        # 组合计算新增病例
        new_cases = max(1, int(base_new_cases * trend_factor * cycle_factor * noise_factor))
        
        # 累计确诊
        confirmed += new_cases
        
        # 当日新增康复（基于当前活跃病例的一定比例，约10-15%）
        recovery_rate = 0.12 + random.uniform(-0.02, 0.03)  # 10-15%的康复率
        new_recovered = max(0, int(active * recovery_rate + random.gauss(0, 2)))
        # 确保新增康复不超过活跃病例
        new_recovered = min(new_recovered, active)
        recovered += new_recovered
        
        # 死亡数（流感死亡率很低，约0.01%-0.1%）
        death_rate = random.uniform(0.0001, 0.001)
        new_deaths = max(0, int(new_cases * death_rate))
        # 大多数情况下为0，偶尔有1例
        if random.random() < 0.95:
            new_deaths = 0
        else:
            new_deaths = min(new_deaths, 1)
        deaths += new_deaths
        
        # 计算活跃病例（活跃 = 累计确诊 - 累计康复 - 累计死亡）
        active = max(0, confirmed - recovered - deaths)
        
        # 住院人数（活跃病例的一部分）
        hospitalized = max(0, int(active * 0.15 + random.gauss(0, 3)))
        
        # 重症病例（活跃病例的很小一部分）
        severe = max(0, int(active * 0.02 + random.gauss(0, 1)))
        
        data.append((
            current_date.strftime('%Y-%m-%d'),
            active,
            int(confirmed),
            int(recovered),
            int(deaths),
            new_cases,
            new_recovered,
            new_deaths,
            hospitalized,
            severe
        ))
    
    return data

def generate_sql_insert(city_name: str, data: List[Tuple]) -> str:
    """
    生成SQL INSERT语句
    
    :param city_name: 城市名称
    :param data: 数据列表
    :return: SQL语句
    """
    sql_lines = []
    sql_lines.append(f"-- {city_name}流感数据")
    sql_lines.append(f"INSERT INTO `flu_daily_cases` (`date`, `city_id`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`, `new_deaths`, `hospitalized`, `severe`, `data_source`) VALUES")
    
    values = []
    for row in data:
        date_str, active, confirmed, recovered, deaths, new_cases, new_recovered, new_deaths, hospitalized, severe = row
        values.append(
            f"((SELECT id FROM cities WHERE city_name = '{city_name}' LIMIT 1), "
            f"'{date_str}', {confirmed}, {active}, {recovered}, {deaths}, "
            f"{new_cases}, {new_recovered}, {new_deaths}, {hospitalized}, {severe}, '模拟数据')"
        )
    
    # 将值组合成SQL
    for i, value in enumerate(values):
        if i == len(values) - 1:
            sql_lines.append(f"  {value};")
        else:
            sql_lines.append(f"  {value},")
    
    sql_lines.append("")
    sql_lines.append("-- 如果数据已存在，更新数据")
    sql_lines.append(f"INSERT INTO `flu_daily_cases` (`city_id`, `date`, `confirmed`, `active`, `recovered`, `deaths`, `new_cases`, `new_recovered`, `new_deaths`, `hospitalized`, `severe`, `data_source`) VALUES")
    
    for i, value in enumerate(values):
        if i == len(values) - 1:
            sql_lines.append(f"  {value}")
            sql_lines.append("ON DUPLICATE KEY UPDATE")
            sql_lines.append("  `active` = VALUES(`active`),")
            sql_lines.append("  `confirmed` = VALUES(`confirmed`),")
            sql_lines.append("  `recovered` = VALUES(`recovered`),")
            sql_lines.append("  `new_cases` = VALUES(`new_cases`),")
            sql_lines.append("  `updated_at` = CURRENT_TIMESTAMP;")
        else:
            sql_lines.append(f"  {value},")
    
    sql_lines.append("")
    return "\n".join(sql_lines)

def main():
    """主函数"""
    start_date = datetime(2024, 10, 1)
    days = 123  # 2024-10-01 到 2025-01-31
    
    print("-- ============================================")
    print("-- 广东省流感模拟数据导入脚本（Python生成）")
    print("-- 数据范围：2024-10-01 至 2025-01-31（123天）")
    print("-- 生成时间：", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("-- ============================================")
    print()
    print("USE Infectious_disease_data;")
    print()
    
    for city_config in CITIES:
        city_name = city_config['name']
        print(f"-- ============================================")
        print(f"-- {city_name}流感数据")
        print(f"-- ============================================")
        
        data = generate_city_data(city_config, start_date, days)
        sql = generate_sql_insert(city_name, data)
        print(sql)
        print()

if __name__ == '__main__':
    main()

