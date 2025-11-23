from app import create_app
from app.utils.auto_update_daily_data import run_auto_update

app = create_app()

if __name__ == '__main__':
    # 启动时自动更新今天的数据
    print("\n" + "="*50)
    print("🔄 正在检查并更新今天的流感数据...")
    print("="*50)
    try:
        run_auto_update()
    except Exception as e:
        print(f"⚠️ 自动更新数据失败（不影响服务器启动）: {e}")
    print("="*50 + "\n")
    
    # 开启 debug 模式，方便修改代码后自动重启
    app.run(debug=True, host='0.0.0.0', port=5010)