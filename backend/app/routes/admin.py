# backend/app/routes/admin.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, FluModelConfig, City, FluDailyCase, Province
from app import db
from app.utils.db_service import ModelConfigService, CityService, FluDataService
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)


def check_super_admin():
    """
    核心权限检查：
    只有 username 是 'admin' 的用户才是超级管理员。
    即使 role 字段是 'admin'，如果 username 不对，也不行。
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # 严格判断：必须存在，且账号名必须是 'admin'
    if user and user.username == 'admin':
        return True
    return False


# --- 1. 获取用户列表 ---
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    # 先检查权限
    if not check_super_admin():
        return jsonify({'code': 403, 'msg': '无权操作：只有系统初始超级管理员可查看用户列表'}), 403

    try:
        users = User.query.all()
        # 返回所有用户数据
        return jsonify({
            'code': 200,
            'data': [u.to_dict() for u in users]
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# --- 2. 提升权限 ---
@admin_bp.route('/promote', methods=['POST'])
@jwt_required()
def promote_user():
    # 先检查权限
    if not check_super_admin():
        return jsonify({'code': 403, 'msg': '无权操作：只有超级管理员可授予权限'}), 403

    data = request.get_json()
    target_user_id = data.get('user_id')

    if not target_user_id:
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    try:
        # 修改角色
        target_user.role = 'admin'
        db.session.commit()
        return jsonify({'code': 200, 'msg': f'已将用户 {target_user.username} 升级为管理员'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


# --- 新增：移除管理员权限 (降级) ---
@admin_bp.route('/demote', methods=['POST'])
@jwt_required()
def demote_user():
    # 1. 依然只有超级管理员(admin账号)才能执行
    if not check_super_admin():
        return jsonify({'code': 403, 'msg': '无权操作'}), 403

    data = request.get_json()
    target_user_id = data.get('user_id')

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    # 防止误操作把超级管理员自己降级了 (虽然前端过滤了，后端再防一手)
    if target_user.username == 'admin':
        return jsonify({'code': 400, 'msg': '无法移除超级管理员的权限'}), 400

    try:
        # 核心逻辑：把角色改回 'researcher'
        target_user.role = 'researcher'
        db.session.commit()
        return jsonify({'code': 200, 'msg': f'已移除用户 {target_user.username} 的管理员权限'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


# [新增] 批准为研究员 (Public -> Researcher)
@admin_bp.route('/approve', methods=['POST'])
@jwt_required()
def approve_researcher():
    if not check_super_admin():
        return jsonify({'code': 403, 'msg': '无权操作'}), 403

    data = request.get_json()
    target_user = User.query.get(data.get('user_id'))

    if not target_user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    # 逻辑：大众 -> 研究员
    target_user.role = 'researcher'
    db.session.commit()
    return jsonify({'code': 200, 'msg': f'已批准 {target_user.username} 进入后台工作'})


# --- 模型配置管理 ---
@admin_bp.route('/model/config', methods=['GET'])
@jwt_required()
def get_model_config():
    """获取默认模型配置（包括默认算法）"""
    try:
        config = ModelConfigService.get_default_config()
        if config:
            try:
                config_dict = config.to_dict()
                return jsonify({
                    'code': 200,
                    'data': config_dict
                })
            except Exception as e:
                # 如果 to_dict() 失败，手动构建字典
                import traceback
                print(f"Error in to_dict(): {str(e)}")
                print(traceback.format_exc())
                return jsonify({
                    'code': 200,
                    'data': {
                        'id': config.id if hasattr(config, 'id') else None,
                        'config_name': config.config_name if hasattr(config, 'config_name') else '默认配置',
                        'default_algorithm': getattr(config, 'default_algorithm', None) or 'seir',
                        'r0': float(config.r0) if hasattr(config, 'r0') and config.r0 else 1.4,
                        'incubation_period': float(config.incubation_period) if hasattr(config, 'incubation_period') and config.incubation_period else 5.0,
                        'infectious_period': float(config.infectious_period) if hasattr(config, 'infectious_period') and config.infectious_period else 7.0,
                        'intervention_factor': float(config.intervention_factor) if hasattr(config, 'intervention_factor') and config.intervention_factor else 1.0,
                        'days': int(config.days) if hasattr(config, 'days') and config.days else 3,
                        'updated_at': config.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(config, 'updated_at') and config.updated_at else None
                    }
                })
        else:
            # 如果没有默认配置，返回默认值
            return jsonify({
                'code': 200,
                'data': {
                    'default_algorithm': 'seir',
                    'r0': 1.4,
                    'incubation_period': 5.0,
                    'infectious_period': 7.0,
                    'intervention_factor': 1.0,
                    'days': 3
                }
            })
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error in get_model_config: {error_msg}")
        print(traceback_str)
        return jsonify({'code': 500, 'msg': f'服务器错误: {error_msg}'}), 500


@admin_bp.route('/model/config', methods=['POST'])
@jwt_required()
def update_model_config():
    """更新默认模型配置（包括默认算法）"""
    if not check_super_admin():
        return jsonify({'code': 403, 'msg': '无权操作：只有超级管理员可修改模型配置'}), 403
    
    try:
        data = request.get_json()
        default_algorithm = data.get('default_algorithm', 'seir')
        
        # 验证算法类型
        if default_algorithm not in ['seir', 'lstm', 'prophet']:
            return jsonify({'code': 400, 'msg': '无效的算法类型，必须是 seir、lstm 或 prophet'}), 400
        
        # 获取或创建默认配置
        config = ModelConfigService.get_default_config()
        if not config:
            # 创建默认配置（使用原始SQL，避免字段不存在的问题）
            from sqlalchemy import text
            try:
                # 先尝试正常创建
                config = FluModelConfig(
                    config_name='默认配置',
                    config_type='default',
                    r0=1.4,
                    incubation_period=5.0,
                    infectious_period=7.0,
                    intervention_factor=1.0,
                    days=3,
                    default_algorithm=default_algorithm,
                    is_default=1,
                    description='系统默认模型配置'
                )
                db.session.add(config)
                db.session.commit()
            except Exception as e:
                # 如果字段不存在，使用原始SQL插入
                db.session.rollback()
                db.session.execute(text("""
                    INSERT INTO flu_model_config 
                    (config_name, config_type, r0, incubation_period, infectious_period, 
                     intervention_factor, is_default, status, description)
                    VALUES ('默认配置', 'default', 1.4, 5.0, 7.0, 1.0, 1, 1, '系统默认模型配置')
                """))
                db.session.commit()
                config = ModelConfigService.get_default_config()
            except Exception as e:
                db.session.rollback()
                raise e
        
        if not config:
            return jsonify({'code': 500, 'msg': '无法创建或获取默认配置'}), 500
        
        # 更新配置（包括首次创建后的初次更新）
        try:
            # 先检查字段是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('flu_model_config')]
            
            # 尝试使用ORM更新
            try:
                # 更新 default_algorithm
                if 'default_algorithm' in columns and hasattr(config, 'default_algorithm'):
                    config.default_algorithm = default_algorithm
                elif 'default_algorithm' in columns:
                    # 字段存在但对象没有属性，使用原始SQL
                    from sqlalchemy import text
                    db.session.execute(text("""
                        UPDATE flu_model_config 
                        SET default_algorithm = :algorithm
                        WHERE is_default = 1 AND status = 1
                    """), {'algorithm': default_algorithm})
                
                # 更新其他字段
                if 'r0' in data:
                    config.r0 = float(data['r0'])
                if 'incubation_period' in data:
                    config.incubation_period = float(data['incubation_period'])
                if 'infectious_period' in data:
                    config.infectious_period = float(data['infectious_period'])
                if 'intervention_factor' in data:
                    config.intervention_factor = float(data['intervention_factor'])
                if 'days' in data:
                    if hasattr(config, 'days'):
                        config.days = int(data['days'])
                    elif 'days' in columns:
                        # 字段存在但对象没有属性，使用原始SQL
                        from sqlalchemy import text
                        db.session.execute(text("""
                            UPDATE flu_model_config 
                            SET days = :days
                            WHERE is_default = 1 AND status = 1
                        """), {'days': int(data['days'])})
                
                db.session.commit()
                
            except Exception as orm_e:
                # ORM更新失败，使用原始SQL
                db.session.rollback()
                from sqlalchemy import text
                update_sql = "UPDATE flu_model_config SET"
                params = {}
                updates = []
                
                # 更新 default_algorithm（如果字段存在）
                if 'default_algorithm' in columns:
                    updates.append("default_algorithm = :default_algorithm")
                    params['default_algorithm'] = default_algorithm
                
                # 更新其他字段
                if 'r0' in data:
                    updates.append("r0 = :r0")
                    params['r0'] = float(data['r0'])
                if 'incubation_period' in data and 'incubation_period' in columns:
                    updates.append("incubation_period = :incubation_period")
                    params['incubation_period'] = float(data['incubation_period'])
                if 'infectious_period' in data and 'infectious_period' in columns:
                    updates.append("infectious_period = :infectious_period")
                    params['infectious_period'] = float(data['infectious_period'])
                if 'intervention_factor' in data and 'intervention_factor' in columns:
                    updates.append("intervention_factor = :intervention_factor")
                    params['intervention_factor'] = float(data['intervention_factor'])
                if 'days' in data and 'days' in columns:
                    updates.append("days = :days")
                    params['days'] = int(data['days'])
                
                if updates:
                    update_sql += " " + ", ".join(updates)
                    update_sql += " WHERE is_default = 1 AND status = 1"
                    db.session.execute(text(update_sql), params)
                    db.session.commit()
                
                config = ModelConfigService.get_default_config()
                
        except Exception as e:
            db.session.rollback()
            raise e
        
        # 返回结果
        if hasattr(config, 'to_dict'):
            config_dict = config.to_dict()
        else:
            # 手动构建字典
            config_dict = {
                'default_algorithm': default_algorithm,
                'r0': float(data.get('r0', 1.4)),
                'incubation_period': float(data.get('incubation_period', 5.0)),
                'infectious_period': float(data.get('infectious_period', 7.0)),
                'intervention_factor': float(data.get('intervention_factor', 1.0)),
                'days': int(data.get('days', 3))
            }
        
        return jsonify({
            'code': 200,
            'msg': '模型配置更新成功',
            'data': config_dict
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error in update_model_config: {error_msg}")
        print(traceback_str)
        return jsonify({'code': 500, 'msg': f'服务器错误: {error_msg}'}), 500


# --- 训练数据监控 ---
@admin_bp.route('/data/stats', methods=['GET'])
@jwt_required()
def get_training_data_stats():
    """获取训练数据统计信息"""
    try:
        # 1. 城市统计
        total_cities = City.query.filter_by(status=1).count()
        
        # 2. 数据记录统计
        total_records = FluDailyCase.query.count()
        
        # 3. 数据日期范围
        earliest_date = db.session.query(func.min(FluDailyCase.date)).scalar()
        latest_date = db.session.query(func.max(FluDailyCase.date)).scalar()
        
        # 4. 有数据的城市数量
        cities_with_data = db.session.query(func.count(func.distinct(FluDailyCase.city_id))).scalar()
        
        # 5. 最近30天的数据量
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_records = FluDailyCase.query.filter(
            FluDailyCase.date >= thirty_days_ago
        ).count()
        
        return jsonify({
            'code': 200,
            'data': {
                'summary': {
                    'total_cities': total_cities,
                    'cities_with_data': cities_with_data or 0,
                    'total_records': total_records,
                    'recent_records_30d': recent_records,
                    'earliest_date': earliest_date.strftime('%Y-%m-%d') if earliest_date else None,
                    'latest_date': latest_date.strftime('%Y-%m-%d') if latest_date else None
                }
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_bp.route('/data/provinces', methods=['GET'])
@jwt_required()
def get_provinces_list():
    """获取省份列表（用于训练数据监控）"""
    try:
        provinces = Province.query.filter_by(status=1).order_by(Province.province_name).all()
        result = []
        for province in provinces:
            # 统计该省份下的城市数量
            city_count = City.query.filter_by(province_id=province.id, status=1).count()
            result.append({
                'id': province.id,
                'province_code': province.province_code,
                'province_name': province.province_name,
                'city_count': city_count
            })
        
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_bp.route('/data/cities', methods=['GET'])
@jwt_required()
def get_cities_list():
    """获取城市列表（用于训练数据监控），默认返回深圳、北京、上海三个城市"""
    try:
        search_keyword = request.args.get('search', '').strip()
        
        # 默认显示的城市列表（按顺序：深圳、北京、上海）
        default_cities = ['深圳市', '北京市', '上海市']
        
        # 如果没有搜索关键词，返回默认的三个城市
        if not search_keyword:
            result = []
            for city_name in default_cities:
                city = City.query.filter_by(city_name=city_name, status=1).first()
                if city:
                    city_dict = city.to_dict()
                    # 添加数据统计
                    city_data_count = FluDailyCase.query.filter_by(city_id=city.id).count()
                    latest_city_date = db.session.query(func.max(FluDailyCase.date)).filter(
                        FluDailyCase.city_id == city.id
                    ).scalar()
                    
                    days_since_last = None
                    if latest_city_date:
                        days_since_last = (date.today() - latest_city_date).days
                    
                    city_dict['data_count'] = city_data_count
                    city_dict['latest_date'] = latest_city_date.strftime('%Y-%m-%d') if latest_city_date else None
                    city_dict['days_since_last'] = days_since_last
                    city_dict['status'] = 'good' if city_data_count >= 30 and (days_since_last is None or days_since_last <= 7) else 'warning'
                    result.append(city_dict)
            
            return jsonify({
                'code': 200,
                'data': result,
                'total': len(result)
            })
        
        # 如果有搜索关键词，进行搜索
        query = City.query.filter_by(status=1)
        query = query.filter(City.city_name.like(f'%{search_keyword}%'))
        
        cities = query.order_by(City.city_name).all()
        result = []
        for city in cities:
            city_dict = city.to_dict()
            # 添加数据统计
            city_data_count = FluDailyCase.query.filter_by(city_id=city.id).count()
            latest_city_date = db.session.query(func.max(FluDailyCase.date)).filter(
                FluDailyCase.city_id == city.id
            ).scalar()
            
            days_since_last = None
            if latest_city_date:
                days_since_last = (date.today() - latest_city_date).days
            
            city_dict['data_count'] = city_data_count
            city_dict['latest_date'] = latest_city_date.strftime('%Y-%m-%d') if latest_city_date else None
            city_dict['days_since_last'] = days_since_last
            city_dict['status'] = 'good' if city_data_count >= 30 and (days_since_last is None or days_since_last <= 7) else 'warning'
            result.append(city_dict)
        
        return jsonify({
            'code': 200,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_bp.route('/data/historical', methods=['GET'])
@jwt_required()
def get_historical_data():
    """获取历史数据（用于图表展示，默认显示最近两周）"""
    try:
        city_name = request.args.get('city_name')
        days = int(request.args.get('days', 14))  # 默认14天（最近两周）
        
        if not city_name:
            return jsonify({'code': 400, 'msg': '缺少城市名称参数'}), 400
        
        # 获取历史数据（最近N天）
        historical_data = FluDataService.get_historical_data(city_name, days)
        
        # 如果没有最近N天的数据，尝试获取所有可用数据（但只取最近N天）
        if not historical_data:
            city = CityService.get_city_by_name(city_name)
            if city:
                # 获取所有数据，然后只取最近N天
                all_data = FluDailyCase.query.filter(
                    FluDailyCase.city_id == city.id
                ).order_by(desc(FluDailyCase.date)).limit(days).all()
                # 反转顺序，使其按日期正序排列
                historical_data = list(reversed(all_data))
        
        # 格式化数据
        chart_data = {
            'dates': [],
            'confirmed': [],
            'active': [],
            'recovered': [],
            'deaths': []
        }
        
        if historical_data:
            for case in historical_data:
                chart_data['dates'].append(case.date.strftime('%Y-%m-%d'))
                chart_data['confirmed'].append(case.confirmed or 0)
                chart_data['active'].append(case.active or 0)
                chart_data['recovered'].append(case.recovered or 0)
                chart_data['deaths'].append(case.deaths or 0)
        else:
            # 返回空数据，但结构完整
            print(f"警告：城市 '{city_name}' 没有历史数据")
        
        return jsonify({
            'code': 200,
            'data': chart_data,
            'msg': f'获取到 {len(chart_data["dates"])} 条数据' if chart_data['dates'] else '该城市暂无数据'
        })
    except Exception as e:
        print(f"获取历史数据错误: {e}")
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_bp.route('/data/daily', methods=['GET'])
@jwt_required()
def get_daily_data_list():
    """获取每日数据列表（用于表格展示）"""
    try:
        city_name = request.args.get('city_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        query = FluDailyCase.query
        
        if city_name:
            city = CityService.get_city_by_name(city_name)
            if city:
                query = query.filter_by(city_id=city.id)
        
        if start_date:
            query = query.filter(FluDailyCase.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(FluDailyCase.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # 排序
        query = query.order_by(desc(FluDailyCase.date))
        
        # 分页
        total = query.count()
        data = query.offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for case in data:
            result.append({
                'id': case.id,
                'date': case.date.strftime('%Y-%m-%d'),
                'city_name': case.city.city_name if case.city else '',
                'confirmed': case.confirmed or 0,
                'active': case.active or 0,
                'recovered': case.recovered or 0,
                'deaths': case.deaths or 0,
                'severe': case.severe or 0
            })
        
        return jsonify({
            'code': 200,
            'data': {
                'list': result,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500