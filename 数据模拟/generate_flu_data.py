#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全国城市流感数据模拟生成脚本
基于SEIR模型和真实流感传播规律生成模拟数据
适配现有数据库结构
"""

import pymysql
import numpy as np
from datetime import datetime, timedelta
import random
import math

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '629629',
    'database': 'infectious_disease_data',
    'charset': 'utf8mb4'
}

# 气候区域映射（基于纬度）
CLIMATE_ZONES = {
    'north': ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江', '山东', '河南', '陕西', '甘肃', '青海', '宁夏', '新疆'],
    'south': ['上海', '江苏', '浙江', '安徽', '福建', '江西', '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州', '云南'],
    'plateau': ['西藏', '青海']
}

# 城市等级映射(一线/新一线/二线/三线)
CITY_TIERS = {
    1: ['北京市', '上海市', '广州市', '深圳市', '成都市', '杭州市', '重庆市', '西安市', '苏州市', '武汉市', '南京市', '天津市'],
    2: ['郑州市', '长沙市', '东莞市', '宁波市', '青岛市', '沈阳市', '合肥市', '佛山市'],
    3: []  # 其他城市默认为3线
}


class FluDataGenerator:
    """流感数据生成器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ 数据库连接已关闭")
    
    def load_cities_from_db(self):
        """从数据库加载城市信息"""
        try:
            # 获取所有城市及其人口信息（不限制status，全部城市）
            query = """
                SELECT 
                    c.id, 
                    c.city_name, 
                    c.latitude,
                    c.longitude,
                    cp.total_population,
                    p.province_name
                FROM cities c
                LEFT JOIN city_population cp ON c.id = cp.city_id
                LEFT JOIN provinces p ON c.province_id = p.id
                ORDER BY c.id
            """
            self.cursor.execute(query)
            cities = self.cursor.fetchall()
            
            cities_info = []
            for city in cities:
                city_id, city_name, latitude, longitude, population, province_name = city
                
                # 如果没有人口数据，根据城市名称估算
                if not population:
                    population = self.estimate_population(city_name)
                
                # 确定气候区域
                climate = self.get_climate_zone(province_name, float(latitude) if latitude else 35.0)
                
                # 确定城市等级
                tier = self.get_city_tier(city_name)
                
                cities_info.append({
                    'id': city_id,
                    'name': city_name,
                    'population': population,
                    'climate': climate,
                    'tier': tier,
                    'province': province_name
                })
            
            print(f"✅ 成功加载 {len(cities_info)} 个城市信息")
            return cities_info
            
        except Exception as e:
            print(f"❌ 加载城市信息失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_climate_zone(self, province_name, latitude):
        """根据省份和纬度判断气候区域"""
        if not province_name:
            # 根据纬度判断
            if latitude > 35:
                return 'north'
            else:
                return 'south'
        
        for climate, provinces in CLIMATE_ZONES.items():
            if any(p in province_name for p in provinces):
                return climate
        
        # 默认根据纬度
        return 'north' if latitude > 35 else 'south'
    
    def get_city_tier(self, city_name):
        """根据城市名称判断城市等级"""
        for tier, cities in CITY_TIERS.items():
            if city_name in cities:
                return tier
        return 3  # 默认为三线城市
    
    def estimate_population(self, city_name):
        """估算城市人口（当数据库中没有时）"""
        # 一线城市
        if self.get_city_tier(city_name) == 1:
            return random.randint(8000000, 25000000)
        # 二线城市
        elif self.get_city_tier(city_name) == 2:
            return random.randint(3000000, 10000000)
        # 三线城市
        else:
            return random.randint(500000, 5000000)
    
    def check_flu_cases_table(self):
        """检查流感病例表是否存在"""
        try:
            self.cursor.execute("SHOW TABLES LIKE 'flu_daily_cases'")
            if self.cursor.fetchone():
                print("✅ flu_daily_cases表已存在")
                return True
            else:
                print("❌ flu_daily_cases表不存在，请先创建表")
                return False
        except Exception as e:
            print(f"❌ 检查表失败: {e}")
            return False
    
    def get_seasonal_factor(self, date, climate):
        """
        计算季节性影响因子
        流感在冬春季高发，夏季低发
        但即使低发期也要保证有基础传播率，不能为0
        """
        month = date.month
        
        if climate == 'north':
            # 北方：11月-3月高发
            if month in [11, 12, 1, 2, 3]:
                return random.uniform(2.0, 2.8)  # 高峰期
            elif month in [4, 5, 9, 10]:
                return random.uniform(1.2, 1.6)  # 过渡期
            else:  # 夏季 6-8月（提高最低值）
                return random.uniform(0.8, 1.1)  # 低谷期但仍有传播
        
        elif climate == 'south':
            # 南方：12月-2月、6-8月双峰
            if month in [12, 1, 2]:
                return random.uniform(1.8, 2.5)  # 冬季高峰
            elif month in [6, 7, 8]:
                return random.uniform(1.4, 1.9)  # 夏季次高峰
            elif month in [3, 4, 5, 9, 10, 11]:
                return random.uniform(1.0, 1.4)  # 过渡期
        
        else:  # plateau
            # 高原地区：季节性较弱但仍有波动
            if month in [11, 12, 1, 2]:
                return random.uniform(1.5, 2.0)
            else:
                return random.uniform(1.0, 1.4)
        
        # 默认返回（保证不会返回None）
        return random.uniform(1.0, 1.5)
    
    def get_population_density_factor(self, population, tier):
        """
        计算人口密度和城市等级影响因子
        一线城市人口密集，传播更快
        """
        base_factor = 1.0
        
        # 城市等级影响
        if tier == 1:
            base_factor *= random.uniform(1.3, 1.8)
        elif tier == 2:
            base_factor *= random.uniform(1.0, 1.3)
        else:
            base_factor *= random.uniform(0.7, 1.0)
        
        # 人口规模影响
        if population > 15000000:
            base_factor *= random.uniform(1.2, 1.5)
        elif population > 8000000:
            base_factor *= random.uniform(1.1, 1.3)
        elif population > 5000000:
            base_factor *= random.uniform(1.0, 1.2)
        else:
            base_factor *= random.uniform(0.8, 1.0)
        
        return base_factor
    
    def seir_model_step(self, S, E, I, R, population, r0, sigma, gamma, intervention):
        """
        SEIR模型单步推演
        S: 易感者, E: 潜伏者, I: 感染者, R: 康复者
        r0: 基本传染数, sigma: 潜伏期转换率, gamma: 康复率
        intervention: 防控措施影响因子
        """
        # 有效传染数（考虑防控措施）
        beta = r0 * gamma / intervention
        
        # 计算变化量
        dS = -beta * S * I / population
        dE = beta * S * I / population - sigma * E
        dI = sigma * E - gamma * I
        dR = gamma * I
        
        # 更新状态（确保非负）
        S_new = max(0, S + dS)
        E_new = max(0, E + dE)
        I_new = max(0, I + dI)
        R_new = max(0, R + dR)
        
        # 确保总数守恒
        total = S_new + E_new + I_new + R_new
        if total > population:
            scale = population / total
            S_new *= scale
            E_new *= scale
            I_new *= scale
            R_new *= scale
        
        return S_new, E_new, I_new, R_new
    
    def generate_city_data(self, city_info, start_date, end_date):
        """
        为单个城市生成流感数据
        使用SEIR模型 + 随机波动 + 季节性因素
        确保每天都有合理的病例数，不会出现0
        """
        population = city_info['total_population']
        climate = city_info['climate']
        tier = city_info['tier']
        
        # 初始状态（基于真实流感发病率：0.5%-2%）
        # 确保初始值足够大，避免后续变成0
        initial_infected = int(population * random.uniform(0.008, 0.025))  # 0.8%-2.5%
        initial_exposed = int(initial_infected * random.uniform(2.5, 4.5))
        initial_recovered = int(population * random.uniform(0.02, 0.06))  # 2%-6%
        initial_susceptible = population - initial_infected - initial_exposed - initial_recovered
        
        # SEIR模型参数
        incubation_period = 2.0  # 流感潜伏期较短（1-4天）
        infectious_period = 7.0  # 传染期（5-10天）
        sigma = 1.0 / incubation_period  # 潜伏期转换率
        gamma = 1.0 / infectious_period  # 康复率
        
        # 初始状态
        S, E, I, R = initial_susceptible, initial_exposed, initial_infected, initial_recovered
        confirmed_total = initial_infected
        recovered_total = initial_recovered
        deaths_total = 0
        
        data_records = []
        current_date = start_date
        
        while current_date <= end_date:
            # 季节性因子（确保最低值不会太小）
            seasonal = self.get_seasonal_factor(current_date, climate)
            
            # 人口密度因子
            density = self.get_population_density_factor(population, tier)
            
            # 随机事件因子
            random_event = random.uniform(0.9, 1.1)
            
            # 防控措施（逐渐加强但不会过强）
            days_passed = (current_date - start_date).days
            intervention = 1.0 + min(days_passed / 365.0, 0.25)  # 最多1.25倍
            
            # 计算有效R0（流感R0通常在1.2-2.0之间）
            base_r0 = random.uniform(1.4, 1.9)  # 提高基础R0
            effective_r0 = base_r0 * seasonal * density * random_event
            
            # SEIR模型推演
            S_prev, E_prev, I_prev, R_prev = S, E, I, R
            S, E, I, R = self.seir_model_step(S, E, I, R, population, effective_r0, sigma, gamma, intervention)
            
            # 计算每日新增（确保有合理的基础值，绝不为0）
            # 基础新增病例 = 人口的万分之0.5到万分之3
            base_new_cases = max(5, int(population * random.uniform(0.00005, 0.0003)))
            
            # SEIR模型计算的新增
            seir_new_infected = max(0, int(sigma * E_prev))
            
            # 综合：取SEIR计算值和基础值的较大者，再加上随机波动
            new_infected = max(base_new_cases, seir_new_infected) + int(random.gauss(0, max(2, base_new_cases * 0.2)))
            new_infected = max(base_new_cases, new_infected)  # 确保不低于基础值
            
            # 康复人数也要有基础保障
            base_recovered = max(3, int(population * random.uniform(0.00003, 0.0002)))
            seir_new_recovered = max(0, int(gamma * I_prev))
            new_recovered = max(base_recovered, seir_new_recovered) + int(random.gauss(0, max(1, base_recovered * 0.15)))
            new_recovered = max(base_recovered, new_recovered)
            
            # 死亡（极少但可能有）
            new_deaths = int(new_infected * random.uniform(0.00003, 0.0003))  # 0.003%-0.03%
            
            # 更新累计数据
            confirmed_total += new_infected
            recovered_total += new_recovered
            deaths_total += new_deaths
            
            # 当前活跃病例 = 累计确诊 - 累计康复 - 累计死亡
            active_cases = max(base_new_cases, confirmed_total - recovered_total - deaths_total)
            
            # 住院和重症（活跃病例的一部分）
            hospitalized = max(1, int(active_cases * random.uniform(0.10, 0.25)))  # 10-25%住院
            severe = max(1, int(hospitalized * random.uniform(0.08, 0.18)))  # 8-18%重症
            
            # 记录数据（确保所有关键字段都不为0）
            record = {
                'date': current_date,
                'active': max(base_new_cases, int(active_cases)),
                'confirmed': int(confirmed_total),
                'recovered': int(recovered_total),
                'deaths': int(deaths_total),
                'new_cases': max(1, int(new_infected)),
                'new_recovered': max(1, int(new_recovered)),
                'new_deaths': int(new_deaths),
                'hospitalized': int(hospitalized),
                'severe': int(severe)
            }
            
            data_records.append(record)
            current_date += timedelta(days=1)
        
        return data_records
    
    def clean_old_data(self, city_id, keep_days=365):
        """
        清理超过指定天数的旧数据
        保证数据库中每个城市只保留最近一年的数据
        """
        try:
            # 先删除该城市所有旧数据（超过365天的）
            delete_sql = """
            DELETE FROM flu_daily_cases 
            WHERE city_id = %s 
            AND date < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            self.cursor.execute(delete_sql, (city_id, keep_days))
            deleted_count = self.cursor.rowcount
            if deleted_count > 0:
                print(f"  🗑️  清理了 {deleted_count} 条超时旧数据")
            
            # 删除重复数据（同一天有多条记录的，只保留最新的一条）
            dedup_sql = """
            DELETE f1 FROM flu_daily_cases f1
            INNER JOIN flu_daily_cases f2 
            WHERE f1.city_id = %s 
            AND f1.city_id = f2.city_id
            AND f1.date = f2.date
            AND f1.id < f2.id
            """
            self.cursor.execute(dedup_sql, (city_id,))
            dedup_count = self.cursor.rowcount
            if dedup_count > 0:
                print(f"  🗑️  清理了 {dedup_count} 条重复数据")
            
            self.conn.commit()
            return deleted_count + dedup_count
        except Exception as e:
            print(f"  ❌ 清理旧数据失败: {e}")
            self.conn.rollback()
            return 0
    
    def insert_city_flu_data(self, city_id, city_name, data_records):
        """插入城市流感数据到数据库"""
        try:
            insert_sql = """
            INSERT INTO flu_daily_cases 
            (date, city_id, confirmed, active, recovered, deaths, 
             new_cases, new_recovered, new_deaths, hospitalized, severe, data_source, remark, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
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
                data_source = VALUES(data_source),
                remark = VALUES(remark),
                updated_at = NOW()
            """
            
            # 批量插入，提高效率
            batch_size = 100
            for i in range(0, len(data_records), batch_size):
                batch = data_records[i:i+batch_size]
                for record in batch:
                    self.cursor.execute(insert_sql, (
                        record['date'],
                        city_id,
                        record['confirmed'],
                        record['active'],
                        record['recovered'],
                        record['deaths'],
                        record['new_cases'],
                        record['new_recovered'],
                        record['new_deaths'],
                        record['hospitalized'],
                        record['severe'],
                        'SEIR模拟',
                        f"基于SEIR模型生成 - {city_name}"
                    ))
                self.conn.commit()
            
            return len(data_records)
            
        except Exception as e:
            print(f"  ❌ 插入数据失败: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            return 0
    
    def generate_all_cities_data(self, days=365):
        """为所有城市生成数据"""
        # 计算日期范围（从今天往前推一年）
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        print(f"\n📅 生成日期范围: {start_date} 至 {end_date} (共 {days} 天)\n")
        print("=" * 80)
        
        # 从数据库加载城市信息
        cities_info = self.load_cities_from_db()
        
        if not cities_info:
            print("❌ 没有找到城市数据")
            return
        
        total_cities = len(cities_info)
        print(f"📊 共需生成 {total_cities} 个城市的数据\n")
        
        success_count = 0
        failed_count = 0
        
        for idx, city in enumerate(cities_info, 1):
            city_id = city['id']
            city_name = city['name']
            population = city['population']
            climate = city['climate']
            tier = city['tier']
            
            print(f"[{idx}/{total_cities}] 🏙️  {city_name}")
            print(f"  ├─ 人口: {population:,}")
            print(f"  ├─ 气候区: {climate}, 城市等级: {tier}")
            
            # 准备城市信息
            city_info = {
                'total_population': population,
                'climate': climate,
                'tier': tier
            }
            
            # 生成数据
            print(f"  ├─ 正在生成 {days} 天的流感数据...")
            data_records = self.generate_city_data(city_info, start_date, end_date)
            
            # 清理旧数据（保留365天）
            print(f"  ├─ 清理旧数据...")
            self.clean_old_data(city_id, keep_days=days)
            
            # 插入新数据
            print(f"  ├─ 插入数据到数据库...")
            inserted_count = self.insert_city_flu_data(city_id, city_name, data_records)
            
            if inserted_count > 0:
                print(f"  ✅ 成功插入 {inserted_count} 条记录")
                success_count += 1
            else:
                print(f"  ❌ 插入失败")
                failed_count += 1
            
            print()
        
        print("=" * 80)
        print(f"🎉 数据生成完成！成功: {success_count}, 失败: {failed_count}")
    
    def show_statistics(self):
        """显示数据统计信息"""
        try:
            print("\n" + "=" * 80)
            print("📊 数据统计信息")
            print("=" * 80)
            
            # 城市总数
            self.cursor.execute("SELECT COUNT(*) FROM cities")
            city_count = self.cursor.fetchone()[0]
            print(f"✅ 城市总数: {city_count}")
            
            # 数据记录总数
            self.cursor.execute("SELECT COUNT(*) FROM flu_daily_cases")
            record_count = self.cursor.fetchone()[0]
            print(f"✅ 数据记录总数: {record_count:,}")
            
            # 日期范围
            self.cursor.execute("SELECT MIN(date), MAX(date) FROM flu_daily_cases")
            date_range = self.cursor.fetchone()
            print(f"✅ 日期范围: {date_range[0]} 至 {date_range[1]}")
            
            # 每个城市的平均记录数
            avg_records = record_count / city_count if city_count > 0 else 0
            print(f"✅ 平均每城市记录数: {avg_records:.0f}")
            
            # 全国当前活跃病例总数
            self.cursor.execute("""
                SELECT SUM(active) 
                FROM flu_daily_cases 
                WHERE date = (SELECT MAX(date) FROM flu_daily_cases)
            """)
            total_active = self.cursor.fetchone()[0] or 0
            print(f"✅ 全国当前活跃病例总数: {total_active:,}")
            
            # Top 5 疫情最严重的城市
            self.cursor.execute("""
                SELECT c.city_name, f.active, f.date
                FROM flu_daily_cases f
                JOIN cities c ON f.city_id = c.id
                WHERE f.date = (SELECT MAX(date) FROM flu_daily_cases)
                ORDER BY f.active DESC
                LIMIT 5
            """)
            top_cities = self.cursor.fetchall()
            print("\n🔥 当前活跃病例最多的5个城市:")
            for rank, (city, active, date) in enumerate(top_cities, 1):
                print(f"  {rank}. {city}: {active:,} 例 (截至 {date})")
            
            print("=" * 80 + "\n")
            
        except Exception as e:
            print(f"❌ 统计信息获取失败: {e}")


def main():
    """主函数"""
    print("=" * 80)
    print("🦠 全国城市流感数据模拟生成系统")
    print("=" * 80)
    print("📝 基于SEIR传染病模型 + 季节性因素 + 人口密度因素")
    print("🎯 生成符合真实传播规律的模拟数据")
    print("=" * 80 + "\n")
    
    generator = FluDataGenerator()
    
    # 连接数据库
    if not generator.connect_db():
        return
    
    try:
        # 检查表是否存在
        print("🔧 步骤 1/3: 检查数据库表...")
        if not generator.check_flu_cases_table():
            print("❌ 请先确保flu_daily_cases表存在")
            return
        print()
        
        # 生成数据
        print("🔧 步骤 2/3: 生成流感数据...")
        generator.generate_all_cities_data(days=365)
        print()
        
        # 显示统计
        print("🔧 步骤 3/3: 生成统计报告...")
        generator.show_statistics()
        
        print("✅ 所有操作完成！")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        generator.close_db()


if __name__ == "__main__":
    main()
