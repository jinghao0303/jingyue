"""
检查数据库中的城市和历史数据
"""
from app import create_app, db
from app.models import City, FluDailyCase
from sqlalchemy import func
from datetime import date, timedelta

app = create_app()

with app.app_context():
    print("=" * 60)
    print("检查数据库中的城市和历史数据")
    print("=" * 60)
    
    # 1. 查看所有城市
    print("\n【所有城市列表】")
    cities = City.query.filter_by(status=1).all()
    if cities:
        for city in cities:
            print(f"  ID: {city.id}, 名称: {city.city_name}, 省份: {city.province.province_name if city.province else 'N/A'}")
    else:
        print("  ❌ 没有找到任何城市")
    
    # 2. 查看每个城市的历史数据数量
    print("\n【各城市历史数据统计】")
    if cities:
        for city in cities:
            # 统计总数据量
            total_count = FluDailyCase.query.filter_by(city_id=city.id).count()
            
            # 统计有active字段的数据量
            active_count = FluDailyCase.query.filter_by(
                city_id=city.id
            ).filter(FluDailyCase.active.isnot(None)).count()
            
            # 统计最近60天的数据
            end_date = date.today()
            start_date = end_date - timedelta(days=60)
            recent_count = FluDailyCase.query.filter(
                FluDailyCase.city_id == city.id,
                FluDailyCase.date >= start_date,
                FluDailyCase.date <= end_date,
                FluDailyCase.active.isnot(None)
            ).count()
            
            # 获取最早和最晚的日期
            earliest = FluDailyCase.query.filter_by(city_id=city.id).order_by(FluDailyCase.date.asc()).first()
            latest = FluDailyCase.query.filter_by(city_id=city.id).order_by(FluDailyCase.date.desc()).first()
            
            print(f"\n  城市: {city.city_name}")
            print(f"    总数据量: {total_count} 条")
            print(f"    有active字段的数据: {active_count} 条")
            print(f"    最近60天有active的数据: {recent_count} 条")
            if earliest:
                print(f"    最早日期: {earliest.date}")
            if latest:
                print(f"    最晚日期: {latest.date}")
            
            # 显示最近几天的数据示例
            if recent_count > 0:
                recent_data = FluDailyCase.query.filter(
                    FluDailyCase.city_id == city.id,
                    FluDailyCase.date >= start_date,
                    FluDailyCase.date <= end_date,
                    FluDailyCase.active.isnot(None)
                ).order_by(FluDailyCase.date.desc()).limit(5).all()
                
                print(f"    最近5天数据示例:")
                for case in recent_data:
                    print(f"      {case.date}: active={case.active}")
    else:
        print("  ❌ 没有城市数据，无法统计")
    
    # 3. 检查"清远市"是否存在
    print("\n【检查'清远市'】")
    qingyuan = City.query.filter_by(city_name="清远市", status=1).first()
    if qingyuan:
        print(f"  ✅ 找到清远市，ID: {qingyuan.id}")
        
        # 检查数据
        total = FluDailyCase.query.filter_by(city_id=qingyuan.id).count()
        active_total = FluDailyCase.query.filter_by(
            city_id=qingyuan.id
        ).filter(FluDailyCase.active.isnot(None)).count()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=60)
        recent = FluDailyCase.query.filter(
            FluDailyCase.city_id == qingyuan.id,
            FluDailyCase.date >= start_date,
            FluDailyCase.date <= end_date,
            FluDailyCase.active.isnot(None)
        ).count()
        
        print(f"  总数据: {total} 条")
        print(f"  有active的数据: {active_total} 条")
        print(f"  最近60天有active的数据: {recent} 条")
        
        if recent == 0:
            print("\n  ⚠️  警告：清远市最近60天没有active字段的数据！")
            print("  可能的原因：")
            print("    1. 数据导入时active字段为NULL")
            print("    2. 数据日期不在最近60天内")
            print("    3. 需要检查数据导入脚本")
    else:
        print("  ❌ 未找到'清远市'")
        print("  提示：请检查城市名称是否正确，或者使用上面列出的城市名称")
    
    print("\n" + "=" * 60)

