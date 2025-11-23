"""
检查Prophet模型是否可用
"""
import sys

print("=" * 60)
print("检查Prophet模型环境")
print("=" * 60)

# 1. 检查Prophet库
print("\n【1. 检查Prophet库】")
try:
    from prophet import Prophet
    print("✅ Prophet库已安装")
    
    # 检查版本
    try:
        import prophet
        print(f"   版本信息: {prophet.__version__ if hasattr(prophet, '__version__') else '未知'}")
    except:
        pass
except ImportError:
    print("❌ Prophet库未安装")
    print("\n安装方法：")
    print("  pip install prophet")
    print("\n或者使用conda：")
    print("  conda install -c conda-forge prophet")
    sys.exit(1)

# 2. 检查依赖
print("\n【2. 检查依赖库】")
dependencies = ['pandas', 'numpy']
for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep} 已安装")
    except ImportError:
        print(f"❌ {dep} 未安装")

# 3. 测试Prophet模型
print("\n【3. 测试Prophet模型】")
try:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta, date
    
    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    values = 100 + np.random.randn(60).cumsum()  # 模拟数据
    values = np.maximum(values, 0)  # 确保非负
    
    df = pd.DataFrame({
        'ds': dates,
        'y': values
    })
    
    # 创建并训练模型
    model = Prophet()
    model.fit(df)
    print("✅ Prophet模型创建和训练成功")
    
    # 测试预测
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    print(f"✅ Prophet预测成功（预测了{len(forecast)}个数据点）")
    print(f"   最后7天的预测值: {forecast['yhat'].tail(7).values.astype(int).tolist()}")
    
except Exception as e:
    print(f"❌ Prophet模型测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Prophet环境检查完成，一切正常！")
print("=" * 60)

