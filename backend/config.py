# backend/config.py
import os


class Config:
    # 数据库连接 (保持你原来的)
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:629629@localhost:3306/Infectious_disease_data'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === JWT 关键配置 ===
    # 1. 必须设置密钥
    JWT_SECRET_KEY = 'super-secret-key-for-idps-system'

    # 2. 强制只使用 Header，不使用 Cookie (这行最关键)
    JWT_TOKEN_LOCATION = ['headers']

    # 3. 指定 Header 格式
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # 4. 显式关闭 Cookie 保护 (防止 Token 里出现 csrf 字段导致校验失败)
    JWT_COOKIE_CSRF_PROTECT = False

    # 跨域
    CORS_HEADERS = 'Content-Type'