# file: app/routes/public.py
"""
公众数据路由 - 无需登录即可访问
"""
from flask import Blueprint, jsonify, request
import random
from app.utils.algo_core import EpidemicModel
from app.utils.db_service import (
    CityService, FluDataService, ModelConfigService
)
from datetime import date

public_bp = Blueprint('public', __name__)


@public_bp.route('/stats', methods=['GET'])
def get_public_stats():
    """
    获取公众大屏的实时数据
    """
    # 模拟数据库中的实时统计数据
    # 实际项目中，这里应该查询 Database 的 'DailyStats' 表

    total_confirmed = 12450 + random.randint(0, 50)  # 模拟数字跳动
    cured = 8900 + random.randint(0, 20)

    return jsonify({
        'code': 200,
        'data': {
            'risk_level': 2,  # 1:低, 2:中, 3:高 (前端根据这个数字变色)
            'risk_text': '中风险',
            'stats': {
                'confirmed': total_confirmed,
                'cured': cured,
                'suspected': 342,
                'death': 12
            },
            'news': [
                "市疾控中心发布最新防控指南",
                "昨日新增确诊病例轨迹公布",
                "疫苗接种点开放时间调整通知"
            ]
        }
    })


@public_bp.route('/model/config', methods=['GET'])
def get_default_model_config():
    """获取默认模型配置（公众端使用，无需登录）"""
    try:
        config = ModelConfigService.get_default_config()
        if config:
            # 安全获取字段，即使字段不存在也使用默认值
            default_algorithm = getattr(config, 'default_algorithm', None)
            if not default_algorithm or default_algorithm == '':
                default_algorithm = 'seir'
            r0 = float(config.r0) if hasattr(config, 'r0') and config.r0 else 1.4
            incubation_period = float(config.incubation_period) if hasattr(config, 'incubation_period') and config.incubation_period else 5.0
            infectious_period = float(config.infectious_period) if hasattr(config, 'infectious_period') and config.infectious_period else 7.0
            intervention_factor = float(config.intervention_factor) if hasattr(config, 'intervention_factor') and config.intervention_factor else 1.0
            days = int(config.days) if hasattr(config, 'days') and config.days else 3
            
            return jsonify({
                'code': 200,
                'data': {
                    'default_algorithm': default_algorithm,
                    'r0': r0,
                    'incubation_period': incubation_period,
                    'infectious_period': infectious_period,
                    'intervention_factor': intervention_factor,
                    'days': days
                }
            })
        else:
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
        print(f"Warning: Failed to get default model config: {e}")
        print(traceback.format_exc())
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


@public_bp.route('/predict', methods=['POST'])
def get_public_predict():
    """
    公开的预测接口 - 无需登录即可调用
    根据用户位置（城市）自动获取数据并使用配置的默认模型预测
    """
    data = request.get_json() or {}
    
    # 1. 从数据库获取默认模型配置（包括默认算法和预测天数）
    default_algorithm = 'seir'
    default_days = 3
    try:
        default_config = ModelConfigService.get_default_config()
        if default_config:
            # 安全获取字段，即使字段不存在也使用默认值
            default_algorithm = getattr(default_config, 'default_algorithm', None) or 'seir'
            default_days = int(getattr(default_config, 'days', None) or 3)
    except Exception as e:
        print(f"Warning: Failed to get default model config: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 获取基础参数（优先使用前端传入的值，否则使用配置的默认值）
    r0 = float(data.get('r0', 1.4))
    days = int(data.get('days', default_days))
    # 如果前端没有指定算法，使用配置的默认算法
    algorithm = data.get('algorithm') or default_algorithm
    city_name = data.get('city_name')  # 城市名称（必需，根据用户位置获取）
    
    # 2. 从数据库获取城市信息和参数
    total_population = 5000000
    city_id = None
    initial_infected = 100
    initial_exposed = None
    initial_recovered = 0
    incubation_period = 5.0
    infectious_period = 7.0
    intervention_factor = 1.0
    
    # 如果提供了城市名称，从数据库查询
    if city_name:
        try:
            city_info = CityService.get_city_info(city_name)
            if city_info:
                city_id = city_info['id']
                total_population = city_info.get('total_population', 5000000)
                
                # 获取历史数据作为初始状态
                initial_state = FluDataService.get_initial_state(city_name=city_name)
                initial_infected = initial_state['initial_infected']
                initial_exposed = initial_state['initial_exposed']
                initial_recovered = initial_state['initial_recovered']
        except Exception as e:
            print(f"Warning: Failed to get city info: {e}")
    
    # 3. 获取模型配置
    if not data.get('incubation_period'):
        try:
            default_config = ModelConfigService.get_default_config()
            if default_config:
                if not data.get('r0'):
                    r0 = float(getattr(default_config, 'r0', 1.4) or 1.4)
                incubation_period = float(getattr(default_config, 'incubation_period', 5.0) or 5.0)
                infectious_period = float(getattr(default_config, 'infectious_period', 7.0) or 7.0)
                intervention_factor = float(getattr(default_config, 'intervention_factor', 1.0) or 1.0)
        except Exception as e:
            print(f"Warning: Failed to get model config: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. 允许前端覆盖参数
    total_population = int(data.get('total_population', total_population))
    initial_infected = int(data.get('initial_infected', initial_infected))
    initial_exposed = int(data.get('initial_exposed')) if data.get('initial_exposed') else None
    initial_recovered = int(data.get('initial_recovered', initial_recovered))
    incubation_period = float(data.get('incubation_period', incubation_period))
    infectious_period = float(data.get('infectious_period', infectious_period))
    intervention_factor = float(data.get('intervention_factor', intervention_factor))
    
    # 5. 初始化模型引擎
    model_engine = EpidemicModel(total_population=total_population)
    
    # 6. 获取历史实际数据（前3天）
    today = date.today()
    historical_dates = []
    historical_actual_values = []
    
    # 构建前3天的日期列表（从3天前到昨天）
    for i in range(3, 0, -1):  # 3, 2, 1 天前
        past_date = date.fromordinal(today.toordinal() - i)
        historical_dates.append(past_date.strftime('%Y-%m-%d'))
        historical_actual_values.append(None)  # 先初始化为None
    
    # 从数据库获取实际数据并填充
    if city_name:
        try:
            # 获取前3天的历史实际数据
            historical_cases = FluDataService.get_historical_data(city_name, days=3)
            # 创建日期到数据的映射
            case_dict = {}
            for case in historical_cases:
                if case.date < today:  # 只取今天之前的数据
                    case_dict[case.date] = case
            
            # 填充实际值
            for i, date_str in enumerate(historical_dates):
                case_date = date.fromisoformat(date_str)
                if case_date in case_dict:
                    case = case_dict[case_date]
                    # 统一使用active字段，如果没有则用confirmed - recovered
                    if case.active is not None:
                        historical_actual_values[i] = float(case.active)
                    elif case.confirmed is not None and case.recovered is not None:
                        historical_actual_values[i] = max(0, float(case.confirmed - case.recovered))
                    # 注意：如果只有confirmed，不使用它，保持None，因为confirmed是累计值，不是活跃病例
        except Exception as e:
            print(f"Warning: Failed to get historical data: {e}")
    
    # 7. 计算前3天的预测值（从3天前开始预测到今天）
    past_predicted_dates = []
    past_predicted_values = []
    
    if len(historical_dates) > 0:
        try:
            # 获取3天前的初始状态（基于3天前的实际数据）
            past_start_date = date.fromordinal(today.toordinal() - 3)
            
            # 获取3天前的实际数据作为初始状态
            past_initial_infected = 100  # 默认值
            past_initial_exposed = 200
            past_initial_recovered = 0
            
            if city_name:
                try:
                    # 获取3天前的数据
                    past_cases = FluDataService.get_historical_data(city_name, days=4)  # 获取4天数据以确保包含3天前
                    for case in past_cases:
                        if case.date == past_start_date:
                            # 使用active字段，如果没有则用confirmed - recovered
                            if case.active is not None:
                                past_initial_infected = int(case.active)
                            elif case.confirmed is not None and case.recovered is not None:
                                past_initial_infected = max(0, int(case.confirmed - case.recovered))
                            past_initial_recovered = int(case.recovered) if case.recovered is not None else 0
                            # 潜伏者通常是感染者的1.5-2倍
                            past_initial_exposed = int(past_initial_infected * 2) if past_initial_infected > 0 else 0
                            break
                except Exception as e:
                    print(f"Warning: Failed to get past initial state: {e}")
            
            # 根据实际数据趋势决定是否使用线性外推
            use_actual_values_for_past = False
            adjusted_r0 = r0
            
            if len(historical_actual_values) >= 2:
                valid_values = [v for v in historical_actual_values if v is not None and v > 0]
                if len(valid_values) >= 2:
                    growth_rates = []
                    for i in range(1, len(valid_values)):
                        if valid_values[i-1] > 0:
                            growth_rate = (valid_values[i] - valid_values[i-1]) / valid_values[i-1]
                            growth_rates.append(growth_rate)
                    
                    if growth_rates:
                        avg_growth_rate = sum(growth_rates) / len(growth_rates)
                        std_growth_rate = (sum((g - avg_growth_rate) ** 2 for g in growth_rates) / len(growth_rates)) ** 0.5
                        
                        print(f"📊 实际数据统计分析:")
                        print(f"  历史实际值: {valid_values}")
                        print(f"  平均日增长率: {avg_growth_rate:.4f} ({avg_growth_rate*100:.2f}%)")
                        print(f"  增长率标准差: {std_growth_rate:.4f}")
                        
                        if abs(avg_growth_rate) < 0.003 and std_growth_rate < 0.005:
                            use_actual_values_for_past = True
                            print(f"✅ 检测到疫情非常稳定，直接使用实际值进行线性外推")
                        elif abs(avg_growth_rate) < 0.005:
                            adjusted_r0 = max(1.0, r0 * 0.2)
                            print(f"⚠️ 检测到疫情非常稳定，大幅调整R0: {r0} -> {adjusted_r0}")
                        elif abs(avg_growth_rate) < 0.01:
                            adjusted_r0 = max(1.0, r0 * 0.4)
                            print(f"⚠️ 检测到疫情稳定，调整R0: {r0} -> {adjusted_r0}")
                        elif avg_growth_rate < 0:
                            adjusted_r0 = max(1.0, r0 * 0.2)
                            print(f"⚠️ 检测到疫情下降，大幅调整R0: {r0} -> {adjusted_r0}")
            
            # 运行4天预测（从3天前到今天，共4天）
            if use_actual_values_for_past:
                # 使用线性外推
                past_predicted_dates = historical_dates.copy()
                past_predicted_values = []
                
                valid_values = [v for v in historical_actual_values if v is not None and v > 0]
                if len(valid_values) >= 2:
                    daily_changes = []
                    for i in range(1, len(valid_values)):
                        daily_changes.append(valid_values[i] - valid_values[i-1])
                    avg_daily_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
                else:
                    avg_daily_change = 0
                
                last_valid_value = None
                for i, actual_val in enumerate(historical_actual_values):
                    if actual_val is not None:
                        past_predicted_values.append(float(actual_val))
                        last_valid_value = actual_val
                    else:
                        if last_valid_value is not None:
                            predicted_val = last_valid_value + avg_daily_change * (i - len([v for v in historical_actual_values[:i] if v is not None]))
                            past_predicted_values.append(max(0, float(predicted_val)))
                        elif i > 0 and historical_actual_values[i-1] is not None:
                            past_predicted_values.append(float(historical_actual_values[i-1]))
                        else:
                            past_predicted_values.append(float(past_initial_infected))
                
                if len(past_predicted_values) > 0:
                    past_predicted_dates.append(today.strftime('%Y-%m-%d'))
                    if last_valid_value is not None:
                        today_predicted = last_valid_value + avg_daily_change
                        past_predicted_values.append(max(0, float(today_predicted)))
                    else:
                        past_predicted_values.append(float(past_predicted_values[-1]))
                
                print(f"✅ 前3天使用实际值/线性外推: {past_predicted_dates}, {past_predicted_values}")
            elif algorithm == 'seir':
                past_result = model_engine.run_seir(
                    r0=adjusted_r0,
                    days=4,
                    total_population=total_population,
                    initial_infected=past_initial_infected,
                    initial_exposed=past_initial_exposed,
                    initial_recovered=past_initial_recovered,
                    incubation_period=incubation_period,
                    infectious_period=infectious_period,
                    intervention_factor=intervention_factor,
                    return_all_states=False,
                    start_date=past_start_date
                )
                past_predicted_dates, past_predicted_values = past_result
            else:
                # 对于LSTM和Prophet，使用历史数据预测
                historical_data = FluDataService.get_historical_infected_series(
                    city_name=city_name,
                    days=60
                )
                if algorithm == 'lstm' and len(historical_data) >= 14:
                    past_predicted_dates, past_predicted_values = model_engine.run_lstm(
                        historical_data=historical_data,
                        days=4,
                        city_name=city_name,
                        start_date=past_start_date
                    )
                elif algorithm == 'prophet':
                    past_predicted_dates, past_predicted_values = model_engine.run_prophet(
                        historical_data=historical_data,
                        days=4,
                        city_name=city_name,
                        start_date=past_start_date
                    )
                else:
                    # 回退到SEIR
                    past_predicted_dates, past_predicted_values = model_engine.run_seir(
                        r0=r0,
                        days=4,
                        total_population=total_population,
                        initial_infected=past_initial_infected,
                        initial_exposed=past_initial_exposed,
                        initial_recovered=past_initial_recovered,
                        incubation_period=incubation_period,
                        infectious_period=infectious_period,
                        intervention_factor=intervention_factor,
                        return_all_states=False,
                        start_date=past_start_date
                    )
            
            # 只取前3天的预测值（不包括今天）
            # 如果预测了4天（从3天前到今天），只取前3天（不包括今天）
            if len(past_predicted_dates) >= 4:
                # 如果包含今天，只取前3天
                past_predicted_dates = past_predicted_dates[:3]
                past_predicted_values = past_predicted_values[:3]
            elif len(past_predicted_dates) == 3:
                # 如果正好3天，全部使用
                pass
            else:
                # 如果少于3天，全部使用
                pass
        except Exception as e:
            print(f"Warning: Failed to calculate past predictions: {e}")
    
    # 8. 计算今天的实际值
    today_actual_value = None
    try:
        if city_name:
            today_cases = FluDataService.get_historical_data(city_name, days=1)
            for case in today_cases:
                if case.date == today:
                    # 统一使用active字段，如果没有则用confirmed - recovered
                    if case.active is not None:
                        today_actual_value = float(case.active)
                    elif case.confirmed is not None and case.recovered is not None:
                        today_actual_value = max(0, float(case.confirmed - case.recovered))
                    # 注意：如果只有confirmed，不使用它，保持None
                    break
    except Exception as e:
        print(f"Warning: Failed to get today's actual value: {e}")
    
    dates = []
    predicted_values = []
    actual_values = []
    
    # 9. 运行未来4天的预测（包括今天和后3天）
    future_predicted_dates = []
    future_predicted_values = []
    
    try:
        # 根据实际数据趋势决定是否使用线性外推
        use_linear_extrapolation_for_future = False
        future_adjusted_r0 = r0
        
        if len(historical_actual_values) >= 2:
            valid_values = [v for v in historical_actual_values if v is not None and v > 0]
            if today_actual_value is not None:
                valid_values.append(today_actual_value)
            
            if len(valid_values) >= 2:
                growth_rates = []
                for i in range(1, len(valid_values)):
                    if valid_values[i-1] > 0:
                        growth_rate = (valid_values[i] - valid_values[i-1]) / valid_values[i-1]
                        growth_rates.append(growth_rate)
                
                if growth_rates:
                    avg_growth_rate = sum(growth_rates) / len(growth_rates)
                    std_growth_rate = (sum((g - avg_growth_rate) ** 2 for g in growth_rates) / len(growth_rates)) ** 0.5
                    
                    if abs(avg_growth_rate) < 0.003 and std_growth_rate < 0.005:
                        use_linear_extrapolation_for_future = True
                        print(f"✅ 未来预测：检测到疫情非常稳定，使用线性外推")
                    elif abs(avg_growth_rate) < 0.005:
                        future_adjusted_r0 = max(1.0, r0 * 0.2)
                        print(f"⚠️ 未来预测使用调整后的R0: {r0} -> {future_adjusted_r0}")
                    elif abs(avg_growth_rate) < 0.01:
                        future_adjusted_r0 = max(1.0, r0 * 0.4)
                        print(f"⚠️ 未来预测使用调整后的R0: {r0} -> {future_adjusted_r0}")
                    elif avg_growth_rate < 0:
                        future_adjusted_r0 = max(1.0, r0 * 0.2)
                        print(f"⚠️ 未来预测使用调整后的R0: {r0} -> {future_adjusted_r0}")
        
        if use_linear_extrapolation_for_future:
            valid_values = [v for v in historical_actual_values if v is not None and v > 0]
            if today_actual_value is not None:
                valid_values.append(today_actual_value)
            
            if len(valid_values) >= 2:
                daily_changes = []
                for i in range(1, len(valid_values)):
                    daily_changes.append(valid_values[i] - valid_values[i-1])
                avg_daily_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
                
                base_value = valid_values[-1] if valid_values else initial_infected
                
                for i in range(4):  # 今天 + 后3天
                    future_date = date.fromordinal(today.toordinal() + i)
                    future_predicted_dates.append(future_date.strftime('%Y-%m-%d'))
                    predicted_val = base_value + avg_daily_change * i
                    future_predicted_values.append(max(0, float(predicted_val)))
                
                print(f"✅ 未来预测使用线性外推: {future_predicted_dates}, {future_predicted_values}")
            else:
                use_linear_extrapolation_for_future = False
        
        if not use_linear_extrapolation_for_future and algorithm == 'seir':
            result = model_engine.run_seir(
                r0=future_adjusted_r0,
                days=4,  # 今天+后3天
                total_population=total_population,
                initial_infected=initial_infected if today_actual_value is None else int(today_actual_value),
                initial_exposed=initial_exposed,
                initial_recovered=initial_recovered,
                incubation_period=incubation_period,
                infectious_period=infectious_period,
                intervention_factor=intervention_factor,
                return_all_states=False,
                start_date=date.today()
            )
            future_predicted_dates, future_predicted_values = result
        elif algorithm == 'lstm':
            # LSTM模型：需要历史数据
            if city_name:
                try:
                    # 从数据库获取历史数据
                    historical_data = FluDataService.get_historical_infected_series(
                        city_name=city_name,
                        days=60  # 获取最近60天的数据
                    )
                    if len(historical_data) >= 14:  # 至少需要14天数据
                        future_predicted_dates, future_predicted_values = model_engine.run_lstm(
                            historical_data=historical_data,
                            days=4,  # 今天+后3天
                            city_name=city_name,
                            start_date=date.today()
                        )
                    else:
                        # 数据不足，使用简单预测
                        future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, 4, initial_infected)
                except Exception as e:
                    print(f"LSTM预测失败: {e}")
                    future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, 4, initial_infected)
            else:
                # 没有城市信息，使用模拟数据
                future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, 4, initial_infected)
        elif algorithm == 'prophet':
            # Prophet模型：需要历史数据
            if city_name:
                try:
                    # 从数据库获取历史数据
                    historical_data = FluDataService.get_historical_infected_series(
                        city_name=city_name,
                        days=60  # 获取最近60天的数据
                    )
                    # 直接使用Prophet模型（内部会处理数据不足的情况）
                    future_predicted_dates, future_predicted_values = model_engine.run_prophet(
                        historical_data=historical_data,
                        days=4,  # 今天+后3天
                        city_name=city_name,
                        start_date=date.today()
                    )
                except Exception as e:
                    print(f"Prophet预测失败: {e}，使用SEIR模型")
                    future_predicted_dates, future_predicted_values = model_engine.run_seir(
                        r0=r0,
                        days=4,
                        total_population=total_population,
                        initial_infected=initial_infected,
                        initial_exposed=initial_exposed,
                        initial_recovered=initial_recovered,
                        incubation_period=incubation_period,
                        infectious_period=infectious_period,
                        intervention_factor=intervention_factor,
                        return_all_states=False,
                        start_date=date.today()
                    )
            else:
                # 没有城市信息，使用SEIR模型
                future_predicted_dates, future_predicted_values = model_engine.run_seir(
                    r0=r0,
                    days=4,
                    total_population=total_population,
                    initial_infected=initial_infected,
                    initial_exposed=initial_exposed,
                    initial_recovered=initial_recovered,
                    incubation_period=incubation_period,
                    infectious_period=infectious_period,
                    intervention_factor=intervention_factor,
                    return_all_states=False,
                    start_date=date.today()
                )
        else:
            future_predicted_dates, future_predicted_values = model_engine.run_seir(
                r0=r0,
                days=4,
                total_population=total_population,
                initial_infected=initial_infected,
                initial_exposed=initial_exposed,
                initial_recovered=initial_recovered,
                incubation_period=incubation_period,
                infectious_period=infectious_period,
                intervention_factor=intervention_factor,
                return_all_states=False,
                start_date=date.today()
            )
        
        # 10. 组合所有数据：前3天 + 今天 + 后3天
        # 前3天的数据（确保日期对齐）
        for i in range(3):
            # 使用预定义的日期（确保顺序正确）
            dates.append(historical_dates[i])
            actual_values.append(historical_actual_values[i])
            
            # 匹配预测值（通过日期匹配）
            predicted_value = None
            if len(past_predicted_dates) > 0:
                # 查找匹配的日期（确保日期格式一致）
                current_date_str = historical_dates[i]
                for j, pred_date in enumerate(past_predicted_dates):
                    # 确保日期格式一致（都转换为字符串比较）
                    pred_date_str = pred_date if isinstance(pred_date, str) else pred_date.strftime('%Y-%m-%d')
                    if pred_date_str == current_date_str and j < len(past_predicted_values):
                        predicted_value = past_predicted_values[j]
                        break
                # 如果没找到匹配，尝试通过索引匹配（past_predicted_dates应该从3天前开始）
                if predicted_value is None and i < len(past_predicted_values):
                    # past_predicted_dates[0] 应该是 3天前，对应 historical_dates[0]
                    predicted_value = past_predicted_values[i]
            predicted_values.append(predicted_value)
        
        # 今天的数据
        today_str = today.strftime('%Y-%m-%d')
        dates.append(today_str)
        if len(future_predicted_values) > 0:
            predicted_values.append(future_predicted_values[0])  # 今天的预测值
        else:
            predicted_values.append(None)
        actual_values.append(today_actual_value)  # 今天的实际值
        
        # 后3天的预测值
        if len(future_predicted_dates) > 1 and len(future_predicted_values) > 1:
            dates.extend(future_predicted_dates[1:4])  # 取后3天（不包括今天）
            predicted_values.extend(future_predicted_values[1:4])
            actual_values.extend([None, None, None])  # 未来没有实际值
        else:
            # 如果未来预测数据不足，用None填充
            for i in range(1, 4):
                if i < len(future_predicted_dates):
                    dates.append(future_predicted_dates[i])
                    predicted_values.append(future_predicted_values[i])
                    actual_values.append(None)
                else:
                    future_date = date.fromordinal(today.toordinal() + i)
                    dates.append(future_date.strftime('%Y-%m-%d'))
                    predicted_values.append(None)
                    actual_values.append(None)
        
        # 11. 计算风险等级和峰值（基于预测值）
        valid_predicted = [v for v in predicted_values if v is not None]
        peak_infection = max(valid_predicted) if valid_predicted else 0
        peak_index = predicted_values.index(peak_infection) if peak_infection > 0 and peak_infection in predicted_values else 0
        peak_date = dates[peak_index] if dates and peak_index < len(dates) else None
        
        # 计算风险等级
        infection_rate = peak_infection / total_population if total_population > 0 else 0
        if infection_rate > 0.01:
            risk_level = '高'
        elif infection_rate > 0.002:
            risk_level = '中'
        else:
            risk_level = '低'
        
        # 调试信息：打印数据用于排查
        print(f"预测数据调试信息:")
        print(f"  日期: {dates}")
        print(f"  预测值: {predicted_values}")
        print(f"  实际值: {actual_values}")
        print(f"  城市: {city_name}, 算法: {algorithm}")
        print(f"  初始感染数: {initial_infected}, R0: {r0}")
        
        return jsonify({
            'code': 200,
            'msg': '预测成功',
            'data': {
                'dates': dates,
                'predicted_values': predicted_values,  # 预测值（7天）
                'actual_values': actual_values,  # 实际值（前3天+今天，后3天为None）
                'values': predicted_values,  # 保持向后兼容
                'meta': {
                    'algorithm': algorithm,
                    'max_cases': peak_infection,
                    'peak_date': peak_date,
                    'risk_level': risk_level,
                    'total_population': total_population,
                    'initial_infected': initial_infected,
                    'r0': r0,
                    'incubation_period': incubation_period,
                    'infectious_period': infectious_period
                }
            }
        })
        
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({
            'code': 500,
            'msg': f'模型运算出错: {str(e)}'
        }), 500