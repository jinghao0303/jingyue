from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os
import base64
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


# --- 注册接口 ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'msg': '账号和密码不能为空'}), 400

    # 检查账号是否存在
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': '该账号已存在'}), 400

    # 密码哈希加密 (安全关键步骤！)
    hashed_password = generate_password_hash(password)

    # ==========================================
    # 核心修改：强制设置 role='public'
    # 这样任何人注册后，默认都只是普通客户，进不去后台
    # ==========================================
    new_user = User(
        username=username,
        password=hashed_password,
        role='public'  # <--- 关键修改在这里
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg': '注册成功', 'code': 200}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'注册失败: {str(e)}'}), 500


# --- 登录接口 ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    # 验证逻辑
    password_valid = False
    if user:
        # 1. 优先尝试哈希验证 (新注册用户)
        if check_password_hash(user.password, password):
            password_valid = True
        # 2. 兼容旧明文密码 (仅针对你手动插入数据库的那个 admin)
        elif user.password == password:
            password_valid = True

    if not password_valid:
        return jsonify({'msg': '账号或密码错误', 'code': 401}), 401

    # 生成 JWT Token
    # 注意：这里必须用 str() 转换 user_id，否则会报 Subject must be a string
    access_token = create_access_token(identity=str(user.user_id))

    return jsonify({
        'msg': '登录成功',
        'code': 200,
        'token': access_token,
        # 返回给前端的信息，包含 role，前端据此判断跳转去后台还是前台
        'userInfo': user.to_dict()
    }), 200


# --- 获取当前用户信息 ---
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前登录用户的信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404
        
        return jsonify({
            'code': 200,
            'data': user.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# --- 更新用户信息 ---
@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """更新当前登录用户的信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404
        
        data = request.get_json() or {}
        
        # 账号名称不可修改，只允许修改真实姓名
        
        # 更新真实姓名（如果提供）
        if 'real_name' in data:
            user.real_name = data['real_name'] if data['real_name'] else None
        
        # 更新头像（如果提供，base64格式）
        if 'avatar' in data and data['avatar']:
            # 这里简单处理，实际项目中应该保存到文件系统或OSS
            # 暂时只保存base64字符串的前1000个字符作为示例
            avatar_data = data['avatar']
            if avatar_data.startswith('data:image'):
                # 提取base64部分
                avatar_data = avatar_data.split(',')[1] if ',' in avatar_data else avatar_data
            # 如果User模型有avatar字段，可以保存
            # user.avatar = avatar_data[:1000]  # 限制长度
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '更新成功',
            'data': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500