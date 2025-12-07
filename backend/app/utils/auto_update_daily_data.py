# file: app/utils/auto_update_daily_data.py
"""
自动更新每日流感数据脚本
在服务器启动时运行，确保最近一年的数据连续可用
缺失的数据会自动补齐，超过一年的历史会自动清理
"""
from app import db, create_app
from app.models import FluDailyCase, City
from datetime import date, timedelta
from types import SimpleNamespace
import random


def calculate_growth_trend(recent_cases):
    """
    根据最近的数据计算增长趋势
    返回：平均日增长率、平均新增病例数
    """
    if len(recent_cases) < 2:
        return 0.0035, 17  # 默认增长率 0.35%，新增 17 例
    
    # 计算平均日增长率
    growth_rates = []
    daily_changes = []
    
    for i in range(1, len(recent_cases)):
        prev_active = recent_cases[i-1].active or 0
        curr_active = recent_cases[i].active or 0
        
        if prev_active > 0:
            growth_rate = (curr_active - prev_active) / prev_active
            growth_rates.append(growth_rate)
            daily_changes.append(curr_active - prev_active)
    
    if growth_rates:
        avg_growth_rate = sum(growth_rates) / len(growth_rates)
        avg_daily_change = sum(daily_changes) / len(daily_changes)
    else:
        avg_growth_rate = 0.0035
        avg_daily_change = 17
    
    return avg_growth_rate, avg_daily_change


def generate_today_data(city, latest_case):
    """
    根据最新数据生成今天的数据
    """
    if not latest_case:
        # 如果没有历史数据，使用默认值
        return {
            'confirmed': 4308,
            'active': 4308,
            'recovered': 0,
            'deaths': 0,
            'new_cases': 0,
            'new_recovered': 0,
            'new_deaths': 0,
            'hospitalized': 0,
            'severe': 0
        }
    
    # 获取最近7天的数据用于计算趋势
    recent_cases = FluDailyCase.query.filter(
        FluDailyCase.city_id == city.id,
        FluDailyCase.date <= latest_case.date
    ).order_by(FluDailyCase.date.desc()).limit(7).all()
    
    # 反转列表，使其按日期正序
    recent_cases = list(reversed(recent_cases))
    
    # 计算增长趋势
    avg_growth_rate, avg_daily_change = calculate_growth_trend(recent_cases)
    
    # 添加一些随机波动（±20%）
    random_factor = 1 + (random.random() - 0.5) * 0.4  # -20% 到 +20%
    daily_change = int(avg_daily_change * random_factor)
    
    # 确保变化量不为负（如果增长率很小，可能为负）
    if avg_growth_rate < 0.001:  # 增长率小于 0.1%
        daily_change = max(0, daily_change)  # 至少为0
    else:
        daily_change = max(1, daily_change)  # 至少为1
    
    # 计算今天的活跃病例数
    latest_active = latest_case.active or 0
    today_active = max(0, int(latest_active + daily_change))
    
    # 计算累计确诊数（基于活跃病例的增长）
    latest_confirmed = latest_case.confirmed or 0
    today_confirmed = latest_confirmed + daily_change
    
    # 计算康复数（假设每天有一定比例的活跃病例康复）
    recovery_rate = 0.14  # 每天约 14% 的活跃病例康复（7天传染期）
    new_recovered = max(0, int(latest_active * recovery_rate))
    latest_recovered = latest_case.recovered or 0
    today_recovered = latest_recovered + new_recovered
    
    # 死亡数（假设死亡率很低）
    death_rate = 0.0001  # 0.01% 的死亡率
    new_deaths = max(0, int(latest_active * death_rate))
    latest_deaths = latest_case.deaths or 0
    today_deaths = latest_deaths + new_deaths
    
    # 住院人数（假设活跃病例的 30% 需要住院）
    today_hospitalized = max(0, int(today_active * 0.3))
    
    # 重症病例（假设住院病例的 5% 是重症）
    today_severe = max(0, int(today_hospitalized * 0.05))
    
    return {
        'confirmed': today_confirmed,
        'active': today_active,
        'recovered': today_recovered,
        'deaths': today_deaths,
        'new_cases': daily_change,
        'new_recovered': new_recovered,
        'new_deaths': new_deaths,
        'hospitalized': today_hospitalized,
        'severe': today_severe
    }


RETENTION_DAYS = 365


def clone_case(case):
    """简化历史数据对象，用于在删除旧数据后继续生成新数据"""
    if not case:
        return None
    return SimpleNamespace(
        date=case.date,
        confirmed=case.confirmed,
        active=case.active,
        recovered=case.recovered,
        deaths=case.deaths
    )


def update_today_data_for_all_cities():
    """
    为所有有数据的城市补齐最近一年的每日数据，并自动清理过期记录
    """
    today = date.today()
    start_date = today - timedelta(days=RETENTION_DAYS)
    created_count = 0
    cleaned_count = 0
    
    # 获取所有有历史数据的城市
    cities_with_data = db.session.query(City).join(FluDailyCase).distinct().all()
    
    if not cities_with_data:
        print("⚠️ 没有找到有历史数据的城市，跳过自动更新")
        return
    
    print(f"📊 正在确保 {len(cities_with_data)} 个城市最近 {RETENTION_DAYS} 天的数据完整...")
    
    for city in cities_with_data:
        try:
            # 记录保留区间之前最后一条数据，用作生成起点
            baseline_case = FluDailyCase.query.filter(
                FluDailyCase.city_id == city.id,
                FluDailyCase.date < start_date
            ).order_by(FluDailyCase.date.desc()).first()
            baseline_snapshot = clone_case(baseline_case)
            
            # 清理超过保留期的数据
            cleaned = FluDailyCase.query.filter(
                FluDailyCase.city_id == city.id,
                FluDailyCase.date < start_date
            ).delete(synchronize_session=False)
            cleaned_count += cleaned
            
            # 获取保留区间内已有的数据
            existing_cases = FluDailyCase.query.filter(
                FluDailyCase.city_id == city.id,
                FluDailyCase.date >= start_date,
                FluDailyCase.date <= today
            ).order_by(FluDailyCase.date.asc()).all()
            cases_by_date = {case.date: case for case in existing_cases}
            
            latest_case = baseline_snapshot
            city_created = 0
            
            current_date = start_date
            while current_date <= today:
                existing_case = cases_by_date.get(current_date)
                if existing_case:
                    latest_case = existing_case
                else:
                    today_data = generate_today_data(city, latest_case)
                    new_case = FluDailyCase(
                        date=current_date,
                        city_id=city.id,
                        confirmed=today_data['confirmed'],
                        active=today_data['active'],
                        recovered=today_data['recovered'],
                        deaths=today_data['deaths'],
                        new_cases=today_data['new_cases'],
                        new_recovered=today_data['new_recovered'],
                        new_deaths=today_data['new_deaths'],
                        hospitalized=today_data['hospitalized'],
                        severe=today_data['severe'],
                        data_source='auto_generated',
                        remark='系统自动生成（基于历史数据趋势）'
                    )
                    db.session.add(new_case)
                    db.session.flush()
                    latest_case = new_case
                    created_count += 1
                    city_created += 1
                current_date += timedelta(days=1)
            
            if city_created > 0:
                print(f"  ✅ 城市 '{city.city_name}': 补充 {city_created} 天数据")
            else:
                print(f"  ➖ 城市 '{city.city_name}': 数据已覆盖最近 {RETENTION_DAYS} 天")
            
            if cleaned > 0:
                print(f"     🧹 已清理 {cleaned} 条早于 {start_date} 的数据")
            
        except Exception as e:
            print(f"  ❌ 城市 '{city.city_name}' 更新失败: {e}")
            db.session.rollback()
            continue
    
    # 提交所有更改
    try:
        db.session.commit()
        print(f"\n✅ 自动更新完成: 补齐 {created_count} 条数据, 清理 {cleaned_count} 条过期记录")
    except Exception as e:
        print(f"\n❌ 提交数据失败: {e}")
        db.session.rollback()


def run_auto_update():
    """
    运行自动更新（在应用上下文中）
    """
    app = create_app()
    with app.app_context():
        try:
            update_today_data_for_all_cities()
        except Exception as e:
            print(f"❌ 自动更新数据时发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    # 可以直接运行此脚本进行测试
    run_auto_update()

