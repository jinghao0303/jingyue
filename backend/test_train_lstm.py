"""
LSTM模型训练测试脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5010"

def register_and_train():
    """注册用户并训练LSTM模型"""
    
    # 0. 注册用户（如果不存在）
    print("=" * 50)
    print("步骤0: 注册用户...")
    register_url = f"{BASE_URL}/api/auth/register"
    
    # 注册信息（可以修改）
    username = "test_user"
    password = "test123456"
    
    register_data = {
        "username": username,
        "password": password
    }
    
    try:
        register_response = requests.post(register_url, json=register_data)
        register_result = register_response.json()
        
        if register_result.get('code') == 200:
            print(f"✅ 注册成功: {username}")
        elif "已存在" in register_result.get('msg', ''):
            print(f"ℹ️  用户已存在: {username}，直接使用")
        else:
            print(f"⚠️  注册失败: {register_result.get('msg')}，尝试登录...")
    except Exception as e:
        print(f"⚠️  注册请求失败: {e}，尝试登录...")
    
    # 1. 登录获取token
    print("\n" + "=" * 50)
    print("步骤1: 登录获取token...")
    login_url = f"{BASE_URL}/api/auth/login"
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        login_result = login_response.json()
        
        if login_result.get('code') != 200:
            print(f"❌ 登录失败: {login_result.get('msg')}")
            print(f"\n提示：")
            print(f"  1. 请检查数据库中是否有用户账号")
            print(f"  2. 或者修改脚本中的 username 和 password 为正确的账号密码")
            return
        
        # 获取token（根据实际返回格式）
        token = login_result.get('token') or login_result.get('data', {}).get('access_token') or login_result.get('data', {}).get('token')
        if not token:
            print("❌ 未获取到token")
            print(f"响应: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
            return
        
        print(f"✅ 登录成功，获取到token")
        
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 2. 训练模型
    print("\n" + "=" * 50)
    print("步骤2: 开始训练LSTM模型...")
    train_url = f"{BASE_URL}/api/predict/train/lstm"
    
    # 训练参数
    train_data = {
        "city_name": "清远市",  # 修改为你要训练的城市名称
        "epochs": 50,           # 训练轮数（可选，默认50）
        "batch_size": 32,       # 批次大小（可选，默认32）
        "validation_split": 0.2, # 验证集比例（可选，默认0.2）
        "historical_days": 60    # 使用多少天历史数据（可选，默认60）
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"训练参数:")
    print(f"  城市: {train_data['city_name']}")
    print(f"  训练轮数: {train_data['epochs']}")
    print(f"  批次大小: {train_data['batch_size']}")
    print(f"  验证集比例: {train_data['validation_split']}")
    print(f"  历史数据天数: {train_data['historical_days']}")
    print("\n开始训练，请耐心等待...")
    
    try:
        train_response = requests.post(train_url, json=train_data, headers=headers)
        train_result = train_response.json()
        
        print("\n" + "=" * 50)
        if train_result.get('code') == 200:
            print("✅ 训练成功！")
            print("\n训练结果:")
            data = train_result.get('data', {})
            print(f"  城市: {data.get('city_name')}")
            print(f"  模型路径: {data.get('model_path')}")
            print(f"  Scaler路径: {data.get('scaler_path')}")
            print(f"  数据点数: {data.get('data_points')}")
            print(f"  训练耗时: {data.get('training_time')}秒")
            
            history = data.get('training_history', {})
            if history:
                print(f"\n训练指标:")
                print(f"  最终损失: {history.get('final_loss')}")
                print(f"  最终验证损失: {history.get('final_val_loss')}")
                print(f"  最终MAE: {history.get('final_mae')}")
                print(f"  最终验证MAE: {history.get('final_val_mae')}")
        else:
            print(f"❌ 训练失败: {train_result.get('msg')}")
            print(f"\n详细错误信息:")
            print(json.dumps(train_result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"❌ 训练请求失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    register_and_train()
