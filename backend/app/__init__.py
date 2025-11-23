# file: app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 允许跨域
    CORS(app, supports_credentials=True)

    db.init_app(app)
    jwt.init_app(app)

    # === 👇 复制这一段代码进去 👇 ===
    from flask import jsonify

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """
        当 Token 格式对，但验证失败时触发 (比如签名不对)
        """
        print("\n🔥 [JWT 错误调试] 验证失败原因:", error_string)
        return jsonify({"msg": error_string}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """
        当 Token 丢失时触发
        """
        print("\n🔥 [JWT 错误调试] Token 丢失原因:", error_string)
        return jsonify({"msg": "Request does not contain an access token"}), 401

    # === 👆 复制结束 👆 ===

    # --- 注册蓝图 ---

    # 1. 认证模块
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # 2. 预测模块 (新增)
    from app.routes.predict import predict_bp
    app.register_blueprint(predict_bp, url_prefix='/api/predict')

    # 3. 公众数据模块 (新增)
    from app.routes.public import public_bp
    app.register_blueprint(public_bp, url_prefix='/api/public')

    # 打印路由方便调试
    with app.app_context():
        # 自动创建数据库表 (如果没有的话) - 方便开发
        db.create_all()
        print("System ready. Mapping routes...")

    return app