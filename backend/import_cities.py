"""
导入城市数据到数据库
"""
from app import create_app, db
from app.models import Province, City, CityPopulation

app = create_app()

with app.app_context():
    print("=" * 60)
    print("导入城市数据")
    print("=" * 60)
    
    # 1. 导入省份数据
    print("\n【步骤1】导入省份数据...")
    provinces_data = [
        ('44', '广东省'),
        ('11', '北京市'),
        ('31', '上海市'),
        ('33', '浙江省'),
        ('32', '江苏省'),
        ('42', '湖北省'),
        ('51', '四川省'),
        ('61', '陕西省'),
        ('50', '重庆市'),
    ]
    
    for code, name in provinces_data:
        province = Province.query.filter_by(province_code=code).first()
        if not province:
            province = Province(province_code=code, province_name=name)
            db.session.add(province)
            print(f"  ✅ 添加省份: {name}")
        else:
            print(f"  ℹ️  省份已存在: {name}")
    
    db.session.commit()
    print("✅ 省份数据导入完成")
    
    # 2. 导入城市数据
    print("\n【步骤2】导入城市数据...")
    cities_data = [
        ('4401', '广州市', '44', 23.1291, 113.2644, 15000000),
        ('4403', '深圳市', '44', 22.5431, 114.0579, 13000000),
        ('4418', '清远市', '44', 23.7000, 113.0500, 4000000),
        ('1101', '北京市', '11', 39.9042, 116.4074, 21000000),
        ('3101', '上海市', '31', 31.2304, 121.4737, 24000000),
        ('3301', '杭州市', '33', 30.2741, 120.1551, 10000000),
        ('3201', '南京市', '32', 32.0603, 118.7969, 8500000),
        ('4201', '武汉市', '42', 30.5928, 114.3055, 12000000),
        ('5101', '成都市', '51', 30.5728, 104.0668, 16000000),
        ('6101', '西安市', '61', 34.3416, 108.9398, 12000000),
        ('5001', '重庆市', '50', 29.5630, 106.5516, 31000000),
    ]
    
    for city_code, city_name, province_code, lat, lng, population in cities_data:
        province = Province.query.filter_by(province_code=province_code).first()
        if not province:
            print(f"  ❌ 错误：找不到省份代码 {province_code}")
            continue
        
        city = City.query.filter_by(city_code=city_code).first()
        if not city:
            city = City(
                city_code=city_code,
                city_name=city_name,
                province_id=province.id,
                latitude=lat,
                longitude=lng,
                status=1  # 确保状态为启用
            )
            db.session.add(city)
            db.session.flush()  # 获取city.id
            print(f"  ✅ 添加城市: {city_name}")
        else:
            # 更新已有城市的状态和坐标
            if city.status != 1:
                city.status = 1
                print(f"  ✅ 更新城市状态: {city_name} (status=1)")
            if city.latitude != lat or city.longitude != lng:
                city.latitude = lat
                city.longitude = lng
                print(f"  ✅ 更新城市坐标: {city_name}")
            if city.city_name != city_name:
                city.city_name = city_name
                print(f"  ✅ 更新城市名称: {city_name}")
            print(f"  ℹ️  城市已存在: {city_name}")
            db.session.flush()
        
        # 3. 导入人口数据
        city_pop = CityPopulation.query.filter_by(city_id=city.id).first()
        if not city_pop:
            city_pop = CityPopulation(
                city_id=city.id,
                total_population=population,
                population_year=2023,
                data_source='统计年鉴'
            )
            db.session.add(city_pop)
            print(f"    ✅ 添加人口数据: {population:,} 人")
        else:
            print(f"    ℹ️  人口数据已存在: {city_pop.total_population:,} 人")
    
    db.session.commit()
    print("\n✅ 城市数据导入完成！")
    
    # 4. 验证数据
    print("\n【验证】检查导入的数据...")
    # 先查看所有城市（包括status=0的）
    all_cities = City.query.all()
    print(f"  数据库中城市总数（包括禁用）: {len(all_cities)}")
    
    # 查看启用的城市
    cities = City.query.filter_by(status=1).all()
    print(f"  启用状态的城市数: {len(cities)}")
    
    if len(all_cities) > 0 and len(cities) == 0:
        print("\n  ⚠️  警告：有城市数据但都是禁用状态！")
        print("  正在将所有城市设置为启用状态...")
        City.query.update({'status': 1})
        db.session.commit()
        cities = City.query.filter_by(status=1).all()
        print(f"  ✅ 已更新，启用状态的城市数: {len(cities)}")
    
    for city in cities:
        pop = CityPopulation.query.filter_by(city_id=city.id).first()
        pop_str = f"{pop.total_population:,}" if pop else "无"
        print(f"    - {city.city_name} (人口: {pop_str}, status={city.status})")
    
    print("\n" + "=" * 60)
    print("✅ 导入完成！现在可以运行训练脚本了。")
    print("=" * 60)

