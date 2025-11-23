"""
导入真实流感数据到数据库
支持从Excel/CSV文件导入数据
"""
import pandas as pd
import os
from app import create_app, db
from app.models import City, FluDailyCase
from datetime import datetime

app = create_app()


def import_from_excel(file_path, city_name, data_source='卫健委'):
    """
    从Excel文件导入数据
    
    :param file_path: Excel文件路径
    :param city_name: 城市名称
    :param data_source: 数据来源
    """
    with app.app_context():
        print("=" * 60)
        print("导入真实流感数据")
        print("=" * 60)
        
        # 1. 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 错误：文件不存在: {file_path}")
            return False
        
        # 2. 获取城市ID
        city = City.query.filter_by(city_name=city_name, status=1).first()
        if not city:
            print(f"❌ 错误：未找到城市 '{city_name}'")
            print("   请先运行 import_cities.py 导入城市数据")
            return False
        
        print(f"✅ 找到城市：{city_name} (ID: {city.id})")
        
        # 3. 读取Excel文件
        try:
            # 尝试读取Excel
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                print(f"❌ 错误：不支持的文件格式，请使用 .xlsx, .xls 或 .csv")
                return False
            
            print(f"✅ 成功读取文件，共 {len(df)} 行数据")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            print("   提示：请确保文件格式正确，CSV文件使用UTF-8编码")
            return False
        
        # 4. 数据验证
        required_columns = ['date', 'confirmed', 'active']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ 错误：缺少必需列：{missing_columns}")
            print(f"   文件中的列：{list(df.columns)}")
            print(f"   必需的列：{required_columns}")
            return False
        
        # 5. 数据预处理
        print("\n【数据预处理】")
        
        # 处理日期格式
        date_errors = []
        for index, row in df.iterrows():
            try:
                if isinstance(row['date'], str):
                    # 尝试多种日期格式
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            df.at[index, 'date'] = datetime.strptime(row['date'], fmt).date()
                            break
                        except:
                            continue
                    else:
                        date_errors.append(f"第{index+1}行: {row['date']}")
                elif hasattr(row['date'], 'date'):
                    df.at[index, 'date'] = row['date'].date()
                elif hasattr(row['date'], 'to_pydatetime'):
                    df.at[index, 'date'] = row['date'].to_pydatetime().date()
            except Exception as e:
                date_errors.append(f"第{index+1}行: {row['date']} ({e})")
        
        if date_errors:
            print(f"  ⚠️  日期格式错误（前5个）: {date_errors[:5]}")
            print("   提示：日期格式应为 YYYY-MM-DD，如 2024-10-01")
        
        # 处理数值字段（填充NaN为0，转换为整数）
        numeric_columns = ['confirmed', 'active', 'recovered', 'deaths', 
                          'new_cases', 'new_recovered', 'new_deaths', 
                          'hospitalized', 'severe']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # 6. 导入数据
        print("\n【开始导入数据】")
        success_count = 0
        error_count = 0
        update_count = 0
        insert_count = 0
        
        for index, row in df.iterrows():
            try:
                # 获取日期
                date_obj = row['date']
                if not isinstance(date_obj, type(datetime.now().date())):
                    continue
                
                # 检查数据有效性
                confirmed = int(row.get('confirmed', 0))
                active = int(row.get('active', 0))
                
                if confirmed < 0 or active < 0:
                    error_count += 1
                    print(f"  ⚠️  第 {index+1} 行：数值为负数，跳过")
                    continue
                
                # 如果没有active字段，尝试计算
                if active == 0 and confirmed > 0:
                    recovered = int(row.get('recovered', 0))
                    deaths = int(row.get('deaths', 0))
                    active = max(0, confirmed - recovered - deaths)
                    if active > 0:
                        print(f"  ℹ️  第 {index+1} 行：通过计算得到active={active}")
                
                # 检查是否已存在
                existing = FluDailyCase.query.filter_by(
                    city_id=city.id,
                    date=date_obj
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.confirmed = confirmed
                    existing.active = active
                    existing.recovered = int(row.get('recovered', 0)) if pd.notna(row.get('recovered')) else 0
                    existing.deaths = int(row.get('deaths', 0)) if pd.notna(row.get('deaths')) else 0
                    existing.new_cases = int(row.get('new_cases', 0)) if pd.notna(row.get('new_cases')) else 0
                    existing.new_recovered = int(row.get('new_recovered', 0)) if pd.notna(row.get('new_recovered')) else 0
                    existing.new_deaths = int(row.get('new_deaths', 0)) if pd.notna(row.get('new_deaths')) else 0
                    existing.hospitalized = int(row.get('hospitalized', 0)) if pd.notna(row.get('hospitalized')) else 0
                    existing.severe = int(row.get('severe', 0)) if pd.notna(row.get('severe')) else 0
                    existing.data_source = str(row.get('data_source', data_source)) if pd.notna(row.get('data_source')) else data_source
                    existing.remark = str(row.get('remark', '')) if pd.notna(row.get('remark')) else None
                    update_count += 1
                    success_count += 1
                else:
                    # 创建新记录
                    new_case = FluDailyCase(
                        date=date_obj,
                        city_id=city.id,
                        confirmed=confirmed,
                        active=active,
                        recovered=int(row.get('recovered', 0)) if pd.notna(row.get('recovered')) else 0,
                        deaths=int(row.get('deaths', 0)) if pd.notna(row.get('deaths')) else 0,
                        new_cases=int(row.get('new_cases', 0)) if pd.notna(row.get('new_cases')) else 0,
                        new_recovered=int(row.get('new_recovered', 0)) if pd.notna(row.get('new_recovered')) else 0,
                        new_deaths=int(row.get('new_deaths', 0)) if pd.notna(row.get('new_deaths')) else 0,
                        hospitalized=int(row.get('hospitalized', 0)) if pd.notna(row.get('hospitalized')) else 0,
                        severe=int(row.get('severe', 0)) if pd.notna(row.get('severe')) else 0,
                        data_source=str(row.get('data_source', data_source)) if pd.notna(row.get('data_source')) else data_source,
                        remark=str(row.get('remark', '')) if pd.notna(row.get('remark')) else None
                    )
                    db.session.add(new_case)
                    insert_count += 1
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 只显示前5个错误
                    print(f"  ⚠️  第 {index+1} 行数据导入失败: {e}")
                continue
        
        # 7. 提交事务
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ 导入完成！")
            print(f"  成功：{success_count} 条（新增：{insert_count}，更新：{update_count}）")
            print(f"  失败：{error_count} 条")
            print("=" * 60)
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 提交失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def import_from_csv(file_path, city_name, data_source='卫健委'):
    """从CSV文件导入（调用import_from_excel，支持CSV）"""
    return import_from_excel(file_path, city_name, data_source)


if __name__ == "__main__":
    import sys
    
    # 使用示例
    if len(sys.argv) < 3:
        print("使用方法：")
        print("  python import_real_data.py <文件路径> <城市名称> [数据来源]")
        print("\n示例：")
        print("  python import_real_data.py data/流感数据_清远市.xlsx 清远市 卫健委")
        print("  python import_real_data.py data/流感数据_广州市.csv 广州市")
        sys.exit(1)
    
    file_path = sys.argv[1]
    city_name = sys.argv[2]
    data_source = sys.argv[3] if len(sys.argv) > 3 else '卫健委'
    
    success = import_from_excel(file_path, city_name, data_source)
    
    if success:
        print("\n💡 提示：")
        print("  1. 运行 check_data.py 验证导入的数据")
        print("  2. 运行 test_train_lstm.py 重新训练LSTM模型")
    else:
        print("\n❌ 导入失败，请检查错误信息")

