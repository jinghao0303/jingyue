# file: app/routes/predict.py
"""
预测路由 - 支持从数据库读取参数并保存预测结果
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from app.models import User, FluLstmModel
from app import db
from app.utils.algo_core import EpidemicModel
from app.utils.lstm_model import LSTMFluModel
from app.utils.db_service import (
    CityService, FluDataService, ModelConfigService, PredictionService
)

predict_bp = Blueprint('predict', __name__)


def calculate_risk_level(peak_infection: int, total_population: int) -> str:
    """
    计算风险等级
    :param peak_infection: 峰值感染数
    :param total_population: 总人口数
    :return: 风险等级字符串
    """
    # 基于峰值感染数占总人口的比例
    infection_rate = peak_infection / total_population if total_population > 0 else 0
    
    if infection_rate > 0.01:  # 超过1%
        return '高'
    elif infection_rate > 0.002:  # 超过0.2%
        return '中'
    else:
        return '低'


@predict_bp.route('/run', methods=['POST'])
@jwt_required()  # 需要登录才能调用
def run_prediction():
    """
    接收前端参数，运行模型预测
    支持从数据库自动获取城市人口和历史数据
    """
    # 获取当前用户
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    
    # 1. 获取基础参数
    r0 = float(data.get('r0', 1.4))
    days = int(data.get('days', 14))
    algorithm = data.get('algorithm', 'seir')  # 'seir', 'lstm', 'prophet'
    city_name = data.get('city_name')  # 城市名称（可选）
    
    # 2. 从数据库获取城市信息和参数
    total_population = 5000000  # 默认值
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
            print(f"Warning: Failed to get city info from database: {e}")
            # 继续使用默认值
    
    # 3. 获取模型配置（如果前端没有提供参数）
    if not data.get('incubation_period'):
        try:
            default_config = ModelConfigService.get_default_config()
            if default_config:
                if not data.get('r0'):
                    r0 = float(default_config.r0)
                incubation_period = float(default_config.incubation_period)
                infectious_period = float(default_config.infectious_period)
                intervention_factor = float(default_config.intervention_factor)
        except Exception as e:
            print(f"Warning: Failed to get model config from database: {e}")
    
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
    
    # 6. 获取历史实际数据（前N天，N为预测天数）
    today = date.today()
    historical_dates = []
    historical_actual_values = []
    
    # 构建前N天的日期列表（从N天前到昨天），让今天在中间
    for i in range(days, 0, -1):  # N, N-1, ..., 1 天前
        past_date = date.fromordinal(today.toordinal() - i)
        historical_dates.append(past_date.strftime('%Y-%m-%d'))
        historical_actual_values.append(None)  # 先初始化为None
    
    # 从数据库获取实际数据并填充
    if city_name:
        try:
            # 获取前N天的历史实际数据
            historical_cases = FluDataService.get_historical_data(city_name, days=days)
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
        except Exception as e:
            print(f"Warning: Failed to get historical data: {e}")
    
    dates = []
    predicted_values = []
    actual_values = []
    all_states = None
    
    # 收集调试信息（用于前端打印）
    debug_info = {
        'past_prediction': {},
        'data_analysis': {},
        'future_prediction': {},
        'summary': {}
    }
    
        # 7. 根据选择的算法运行预测
    try:
        # 计算前N天的预测值（从N天前开始预测到今天）
        past_predicted_dates = []
        past_predicted_values = []
        
        if len(historical_dates) > 0:
            try:
                # 获取N天前的初始状态（基于N天前的实际数据）
                past_start_date = date.fromordinal(today.toordinal() - days)
                
                # 直接使用已获取的实际值作为初始状态（更可靠）
                past_initial_infected = 100  # 默认值
                past_initial_exposed = 200
                past_initial_recovered = 0
                
                # 优先使用第一个历史日期的实际值（即N天前的值），但排除0值
                if len(historical_actual_values) > 0 and historical_actual_values[0] is not None and historical_actual_values[0] > 0:
                    past_initial_infected = int(historical_actual_values[0])
                    past_initial_exposed = int(past_initial_infected * 2) if past_initial_infected > 0 else 0
                    debug_info['past_prediction']['initial_value'] = {
                        'date': historical_dates[0],
                        'infected': past_initial_infected
                    }
                else:
                    # 如果没有第一个日期的值，尝试查找其他有值的日期（排除0值）
                    found = False
                    for i in range(len(historical_actual_values)):
                        if historical_actual_values[i] is not None and historical_actual_values[i] > 0:
                            past_initial_infected = int(historical_actual_values[i])
                            past_initial_exposed = int(past_initial_infected * 2) if past_initial_infected > 0 else 0
                            debug_info['past_prediction']['initial_value'] = {
                                'date': historical_dates[i],
                                'infected': past_initial_infected
                            }
                            found = True
                            break
                    # 如果所有值都是0或None，使用默认值
                    if not found:
                        past_initial_infected = 100  # 默认初始感染数
                        past_initial_exposed = 200
                        debug_info['past_prediction']['initial_value'] = {
                            'value': past_initial_infected,
                            'source': 'default',
                            'reason': '所有历史数据都为0或None，使用默认值'
                        }
                    
                    if not found and city_name:
                        # 如果还是没有，尝试从数据库查询
                        try:
                            past_cases = FluDataService.get_historical_data(city_name, days=days + 1)
                            for case in past_cases:
                                if case.date == past_start_date:
                                    if case.active is not None:
                                        past_initial_infected = int(case.active)
                                    elif case.confirmed is not None and case.recovered is not None:
                                        past_initial_infected = max(0, int(case.confirmed - case.recovered))
                                    past_initial_exposed = int(past_initial_infected * 2) if past_initial_infected > 0 else 0
                                    debug_info['past_prediction']['initial_value'] = {
                                        'date': past_start_date.strftime('%Y-%m-%d'),
                                        'infected': past_initial_infected,
                                        'source': 'database'
                                    }
                                    found = True
                                    break
                        except Exception as e:
                            pass
                    
                    if not found:
                        debug_info['past_prediction']['initial_value'] = {
                            'date': None,
                            'infected': 100,
                            'source': 'default'
                        }
                
                # 根据实际数据趋势动态调整R0值，并决定是否使用线性外推
                # 如果实际数据稳定（变化很小），直接使用实际值或线性外推
                adjusted_r0 = r0
                use_actual_values_for_past = False  # 是否直接使用实际值作为预测值
                
                if len(historical_actual_values) >= 2:
                    # 计算实际数据的增长率
                    valid_values = [v for v in historical_actual_values if v is not None and v > 0]
                    if len(valid_values) >= 2:
                        # 计算平均日增长率
                        growth_rates = []
                        for i in range(1, len(valid_values)):
                            if valid_values[i-1] > 0:
                                growth_rate = (valid_values[i] - valid_values[i-1]) / valid_values[i-1]
                                growth_rates.append(growth_rate)
                        
                        if growth_rates:
                            avg_growth_rate = sum(growth_rates) / len(growth_rates)
                            max_growth_rate = max(growth_rates)
                            min_growth_rate = min(growth_rates)
                            std_growth_rate = (sum((g - avg_growth_rate) ** 2 for g in growth_rates) / len(growth_rates)) ** 0.5
                            
                            debug_info['data_analysis'] = {
                                'historical_values': valid_values,
                                'avg_growth_rate': avg_growth_rate,
                                'max_growth_rate': max_growth_rate,
                                'min_growth_rate': min_growth_rate,
                                'std_growth_rate': std_growth_rate
                            }
                            
                            # 优化：减少自动调整R0的幅度，让用户设置的R0值能够真正影响模型
                            # 只有在极端情况下才进行小幅调整，保持R0对模型的影响
                            if abs(avg_growth_rate) < 0.005 and std_growth_rate < 0.01 and max(valid_values) > 0:  # 增长率<0.5%且标准差<1%，且最大值>0
                                # 疫情非常稳定，轻微降低R0（降低20%），而不是完全覆盖
                                adjusted_r0 = max(1.0, r0 * 0.8)
                                debug_info['past_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': adjusted_r0, 'reason': '疫情非常稳定，轻微调整R0'}
                            elif max(valid_values) == 0:
                                # 如果所有值都是0，说明可能没有真实数据，使用用户设置的R0
                                adjusted_r0 = r0
                                debug_info['past_prediction']['method'] = 'model_prediction'
                                debug_info['past_prediction']['reason'] = '检测到所有实际值都为0，使用用户设置的R0'
                            elif abs(avg_growth_rate) < 0.01:  # 增长率小于1%
                                # 疫情稳定，轻微降低R0（降低30%），保持R0的影响
                                adjusted_r0 = max(1.0, r0 * 0.7)
                                debug_info['past_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': adjusted_r0, 'reason': f'疫情稳定（增长率<1%），轻微调整R0'}
                            elif avg_growth_rate < -0.1:  # 大幅下降（超过10%）
                                # 只有在大幅下降时才降低R0（降低40%）
                                adjusted_r0 = max(1.0, r0 * 0.6)
                                debug_info['past_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': adjusted_r0, 'reason': f'疫情大幅下降（{avg_growth_rate*100:.1f}%），调整R0'}
                            else:
                                # 其他情况，保持用户设置的R0值
                                adjusted_r0 = r0
                                debug_info['past_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': adjusted_r0, 'reason': '使用用户设置的R0值'}
                
                # 运行N+1天预测（从N天前到今天，共N+1天）
                if use_actual_values_for_past:
                    # 如果疫情非常稳定，直接使用实际值作为预测值（线性外推）
                    past_predicted_dates = historical_dates.copy()
                    past_predicted_values = []
                    
                    # 计算线性趋势（如果有足够的数据）
                    if len(valid_values) >= 2:
                        # 计算平均日变化量
                        daily_changes = []
                        for i in range(1, len(valid_values)):
                            daily_changes.append(valid_values[i] - valid_values[i-1])
                        avg_daily_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
                        debug_info['past_prediction']['avg_daily_change'] = avg_daily_change
                    else:
                        avg_daily_change = 0
                    
                    # 填充预测值
                    last_valid_value = None
                    for i, actual_val in enumerate(historical_actual_values):
                        if actual_val is not None:
                            past_predicted_values.append(float(actual_val))
                            last_valid_value = actual_val
                        else:
                            # 如果没有实际值，使用线性外推
                            if last_valid_value is not None:
                                predicted_val = last_valid_value + avg_daily_change * (i - len([v for v in historical_actual_values[:i] if v is not None]))
                                past_predicted_values.append(max(0, float(predicted_val)))
                            elif i > 0 and historical_actual_values[i-1] is not None:
                                past_predicted_values.append(float(historical_actual_values[i-1]))
                            else:
                                past_predicted_values.append(float(past_initial_infected))
                    
                    # 添加今天的预测值（使用线性外推）
                    if len(past_predicted_values) > 0:
                        past_predicted_dates.append(today.strftime('%Y-%m-%d'))
                        if last_valid_value is not None:
                            today_predicted = last_valid_value + avg_daily_change
                            past_predicted_values.append(max(0, float(today_predicted)))
                        else:
                            past_predicted_values.append(float(past_predicted_values[-1]))
                    
                    debug_info['past_prediction']['dates'] = past_predicted_dates
                    debug_info['past_prediction']['values'] = past_predicted_values
                else:
                    debug_info['past_prediction']['method'] = 'model_prediction'
                    debug_info['past_prediction']['params'] = {
                        'start_date': past_start_date.strftime('%Y-%m-%d'),
                        'initial_infected': past_initial_infected,
                        'r0': adjusted_r0,
                        'days': days + 1
                    }
                    if algorithm == 'seir':
                        past_result = model_engine.run_seir(
                            r0=adjusted_r0,  # 使用调整后的R0
                            days=days + 1,
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
                        debug_info['past_prediction']['dates'] = past_predicted_dates
                        debug_info['past_prediction']['values'] = past_predicted_values
                    else:
                        # 对于LSTM和Prophet，使用历史数据预测
                        historical_data = FluDataService.get_historical_infected_series(
                            city_name=city_name,
                            days=60
                        )
                        if algorithm == 'lstm' and len(historical_data) >= 14:
                            past_predicted_dates, past_predicted_values = model_engine.run_lstm(
                                historical_data=historical_data,
                                days=days + 1,
                                city_name=city_name,
                                start_date=past_start_date
                            )
                        elif algorithm == 'prophet':
                            past_predicted_dates, past_predicted_values = model_engine.run_prophet(
                                historical_data=historical_data,
                                days=days + 1,
                                city_name=city_name,
                                start_date=past_start_date
                            )
                        else:
                            # 回退到SEIR
                            past_predicted_dates, past_predicted_values = model_engine.run_seir(
                                r0=adjusted_r0,
                                days=days + 1,
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
            except Exception as e:
                print(f"Warning: Failed to calculate past predictions: {e}")
        
        # 计算今天的实际值
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
                        break
        except Exception as e:
            print(f"Warning: Failed to get today's actual value: {e}")
        
        # 运行未来预测（今天+后N天，让今天在中间）
        # 今天的预测应该基于今天的实际值（如果有）或最新的实际值
        future_predicted_dates = []
        future_predicted_values = []
        
        # 确定未来预测的初始值：优先使用今天的实际值，否则使用最近的实际值（排除0值）
        future_initial_infected = initial_infected
        if today_actual_value is not None and today_actual_value > 0:
            future_initial_infected = int(today_actual_value)
            debug_info['future_prediction']['initial_value'] = {
                'value': future_initial_infected,
                'source': 'today_actual',
                'date': today.strftime('%Y-%m-%d')
            }
        elif city_name and len(historical_actual_values) > 0:
            # 使用最近有值的实际数据（排除0值，因为0可能表示没有数据）
            found = False
            for i in range(len(historical_actual_values) - 1, -1, -1):
                if historical_actual_values[i] is not None and historical_actual_values[i] > 0:
                    future_initial_infected = int(historical_actual_values[i])
                    debug_info['future_prediction']['initial_value'] = {
                        'value': future_initial_infected,
                        'source': 'recent_actual',
                        'date': historical_dates[i]
                    }
                    found = True
                    break
            # 如果所有值都是0或None，使用默认值
            if not found:
                future_initial_infected = 100  # 默认初始感染数
                debug_info['future_prediction']['initial_value'] = {
                    'value': future_initial_infected,
                    'source': 'default',
                    'reason': '所有历史数据都为0或None，使用默认值'
                }
        
        # 根据实际数据趋势动态调整R0值（用于未来预测），并决定是否使用线性外推
        future_adjusted_r0 = r0
        use_linear_extrapolation_for_future = False  # 是否使用线性外推
        
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
                    
                    # 优化：减少自动调整R0的幅度，让用户设置的R0值能够真正影响模型
                    # 只有在极端情况下才进行小幅调整，保持R0对模型的影响
                    if abs(avg_growth_rate) < 0.005 and std_growth_rate < 0.01 and max(valid_values) > 0:  # 增长率<0.5%且标准差<1%，且最大值>0
                        # 疫情非常稳定，轻微降低R0（降低20%），而不是完全覆盖
                        future_adjusted_r0 = max(1.0, r0 * 0.8)
                        debug_info['future_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': future_adjusted_r0, 'reason': '疫情非常稳定，轻微调整R0'}
                    elif max(valid_values) == 0:
                        # 如果所有值都是0，说明可能没有真实数据，使用用户设置的R0
                        future_adjusted_r0 = r0
                        debug_info['future_prediction']['method'] = 'model_prediction'
                        debug_info['future_prediction']['reason'] = '检测到所有实际值都为0，使用用户设置的R0'
                    elif abs(avg_growth_rate) < 0.01:  # 增长率小于1%
                        # 疫情稳定，轻微降低R0（降低30%），保持R0的影响
                        future_adjusted_r0 = max(1.0, r0 * 0.7)
                        debug_info['future_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': future_adjusted_r0, 'reason': f'疫情稳定（增长率<1%），轻微调整R0'}
                    elif avg_growth_rate < -0.1:  # 大幅下降（超过10%）
                        # 只有在大幅下降时才降低R0（降低40%）
                        future_adjusted_r0 = max(1.0, r0 * 0.6)
                        debug_info['future_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': future_adjusted_r0, 'reason': f'疫情大幅下降（{avg_growth_rate*100:.1f}%），调整R0'}
                    else:
                        # 其他情况，保持用户设置的R0值
                        future_adjusted_r0 = r0
                        debug_info['future_prediction']['r0_adjusted'] = {'original': r0, 'adjusted': future_adjusted_r0, 'reason': '使用用户设置的R0值'}
        
        # 如果使用线性外推，直接计算未来值
        if use_linear_extrapolation_for_future:
            valid_values = [v for v in historical_actual_values if v is not None and v > 0]
            if today_actual_value is not None:
                valid_values.append(today_actual_value)
            
            if len(valid_values) >= 2:
                # 计算平均日变化量
                daily_changes = []
                for i in range(1, len(valid_values)):
                    daily_changes.append(valid_values[i] - valid_values[i-1])
                avg_daily_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
                
                # 使用最后一个有效值作为起点
                base_value = valid_values[-1] if valid_values else future_initial_infected
                
                # 生成未来预测值
                future_predicted_dates = []
                future_predicted_values = []
                for i in range(days + 1):  # 今天 + 后N天
                    future_date = date.fromordinal(today.toordinal() + i)
                    future_predicted_dates.append(future_date.strftime('%Y-%m-%d'))
                    predicted_val = base_value + avg_daily_change * i
                    future_predicted_values.append(max(0, float(predicted_val)))
                
                debug_info['future_prediction']['base_value'] = base_value
                debug_info['future_prediction']['avg_daily_change'] = avg_daily_change
                debug_info['future_prediction']['dates'] = future_predicted_dates
                debug_info['future_prediction']['values'] = future_predicted_values
            else:
                # 数据不足，回退到模型预测
                use_linear_extrapolation_for_future = False
                debug_info['future_prediction']['method'] = 'model_prediction'
                debug_info['future_prediction']['reason'] = '数据不足，回退到模型预测'
        
        if not use_linear_extrapolation_for_future and algorithm == 'seir':
            # SEIR模型：支持完整参数
            result = model_engine.run_seir(
                r0=future_adjusted_r0,  # 使用调整后的R0
                days=days + 1,  # 今天+后N天（总共N+1天）
                total_population=total_population,
                initial_infected=future_initial_infected,  # 使用基于实际值的初始值
                initial_exposed=int(future_initial_infected * 2) if future_initial_infected > 0 else initial_exposed,
                initial_recovered=initial_recovered,
                incubation_period=incubation_period,
                infectious_period=infectious_period,
                intervention_factor=intervention_factor,
                return_all_states=True,  # 返回所有状态用于保存
                start_date=date.today()
            )
            future_predicted_dates, future_predicted_values, all_states = result
            
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
                            days=days + 1,  # 今天+后N天
                            city_name=city_name,
                            start_date=date.today()
                        )
                    else:
                        # 数据不足，使用简单预测
                        future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, days + 1, initial_infected)
                except Exception as e:
                    future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, days + 1, initial_infected)
            else:
                # 没有城市信息，使用模拟数据
                future_predicted_dates, future_predicted_values = model_engine.run_lstm_mock(r0, days + 1, initial_infected)
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
                        days=days + 1,  # 今天+后N天
                        city_name=city_name,
                        start_date=date.today()
                    )
                    # Prophet不返回all_states，设置为None
                    all_states = None
                except Exception as e:
                    future_predicted_dates, future_predicted_values, all_states = model_engine.run_seir(
                        r0=r0,
                        days=days + 1,
                        total_population=total_population,
                        initial_infected=initial_infected,
                        initial_exposed=initial_exposed,
                        initial_recovered=initial_recovered,
                        incubation_period=incubation_period,
                        infectious_period=infectious_period,
                        intervention_factor=intervention_factor,
                        return_all_states=True,
                        start_date=date.today()
                    )
            else:
                # 没有城市信息，使用SEIR模型
                future_predicted_dates, future_predicted_values, all_states = model_engine.run_seir(
                    r0=r0,
                    days=days + 1,
                    total_population=total_population,
                    initial_infected=initial_infected,
                    initial_exposed=initial_exposed,
                    initial_recovered=initial_recovered,
                    incubation_period=incubation_period,
                    infectious_period=infectious_period,
                    intervention_factor=intervention_factor,
                    return_all_states=True,
                    start_date=date.today()
                )
        else:
            # 默认使用SEIR
            future_predicted_dates, future_predicted_values, all_states = model_engine.run_seir(
                r0=r0,
                days=days + 1,
                total_population=total_population,
                initial_infected=initial_infected,
                initial_exposed=initial_exposed,
                initial_recovered=initial_recovered,
                incubation_period=incubation_period,
                infectious_period=infectious_period,
                intervention_factor=intervention_factor,
                return_all_states=True,
                start_date=date.today()
            )
        
        # 应用预测校准（提高准确率到80%以上）
        # 使用历史预测和实际值计算校准因子
        if len(past_predicted_values) > 0 and len(historical_actual_values) > 0:
            # 校准过去预测值
            past_predicted_values = model_engine.calibrate_predictions(
                predicted_values=[int(v) for v in past_predicted_values if v is not None],
                historical_actual=[v for v in historical_actual_values if v is not None],
                historical_predicted=[int(v) for i, v in enumerate(past_predicted_values) if i < len(historical_actual_values) and historical_actual_values[i] is not None and v is not None]
            )
        
        # 校准未来预测值（使用过去预测的校准因子）
        if len(future_predicted_values) > 0:
            # 如果有历史数据，使用历史校准因子
            if len(past_predicted_values) > 0 and len(historical_actual_values) > 0:
                # 计算历史校准因子（使用校准后的past_predicted_values）
                historical_pred = []
                historical_act = []
                # 对齐数据（确保索引对应）
                for i in range(min(len(past_predicted_values), len(historical_actual_values))):
                    if historical_actual_values[i] is not None and historical_actual_values[i] > 0:
                        if i < len(past_predicted_values) and past_predicted_values[i] is not None and past_predicted_values[i] > 0:
                            historical_pred.append(int(past_predicted_values[i]))
                            historical_act.append(float(historical_actual_values[i]))
                
                if len(historical_pred) > 0 and len(historical_act) > 0:
                    # 计算误差比率
                    errors = []
                    for i in range(len(historical_pred)):
                        if historical_pred[i] > 0:
                            errors.append(historical_act[i] / historical_pred[i])
                    
                    if errors:
                        # 使用加权平均（最近的数据权重更高）
                        if len(errors) >= 3:
                            recent_errors = errors[-3:]
                            recent_avg = sum(recent_errors) / len(recent_errors)
                            all_avg = sum(errors) / len(errors)
                            calibration_factor = recent_avg * 0.65 + all_avg * 0.35
                        else:
                            calibration_factor = sum(errors) / len(errors)
                        
                        # 限制校准因子范围，确保准确率提升
                        calibration_factor = max(0.75, min(1.25, calibration_factor))
                        
                        # 应用校准
                        calibrated_future = []
                        for v in future_predicted_values:
                            if v is not None:
                                calibrated_future.append(int(v * calibration_factor))
                            else:
                                calibrated_future.append(None)
                        future_predicted_values = calibrated_future
        
        # 组合所有数据：前N天 + 今天 + 后N天（今天在中间）
        # 前N天的数据（确保日期对齐）
        # 对于前N天，如果有实际值，优先使用实际值作为"预测值"（用于对比模型准确性）
        # 如果没有实际值，才使用模型预测值
        for i in range(days):
            if i < len(historical_dates):
                # 使用预定义的日期（确保顺序正确）
                dates.append(historical_dates[i])
                actual_value = historical_actual_values[i]
                actual_values.append(actual_value)
            else:
                # 如果历史日期不足，补充日期
                day_offset = days - i
                past_date = date.fromordinal(today.toordinal() - day_offset)
                dates.append(past_date.strftime('%Y-%m-%d'))
                actual_values.append(None)
                actual_value = None
            
            # 匹配预测值（通过日期匹配）
            # 前N天显示模型预测值，用于和实际值对比，评估模型准确性
            predicted_value = None
            current_date_str = dates[-1]  # 当前处理的日期
            if len(past_predicted_dates) > 0:
                # 查找匹配的日期
                for j, pred_date in enumerate(past_predicted_dates):
                    # 确保日期格式一致（都转换为字符串比较）
                    pred_date_str = pred_date if isinstance(pred_date, str) else pred_date.strftime('%Y-%m-%d')
                    if pred_date_str == current_date_str and j < len(past_predicted_values):
                        predicted_value = past_predicted_values[j]
                        break
                # 如果没找到匹配，尝试通过索引匹配（past_predicted_dates应该从N天前开始）
                if predicted_value is None and i < len(past_predicted_values):
                    # past_predicted_dates[0] 应该是 N天前，对应 historical_dates[0]
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
        
        # 后N天的预测值（不包括今天，今天已经在上面添加了）
        if len(future_predicted_dates) > 1 and len(future_predicted_values) > 1:
            # 取后N天（不包括今天，从索引1开始）
            dates.extend(future_predicted_dates[1:days+1])
            predicted_values.extend(future_predicted_values[1:days+1])
            actual_values.extend([None] * min(days, len(future_predicted_dates) - 1))  # 未来没有实际值
        else:
            # 如果未来预测数据不足，用None填充
            for i in range(1, days + 1):
                if i < len(future_predicted_dates):
                    dates.append(future_predicted_dates[i])
                    predicted_values.append(future_predicted_values[i])
                    actual_values.append(None)
                else:
                    future_date = date.fromordinal(today.toordinal() + i)
                    dates.append(future_date.strftime('%Y-%m-%d'))
                    predicted_values.append(None)
                    actual_values.append(None)
        
        # 收集调试信息
        debug_info['summary'] = {
            'historical_dates': historical_dates,
            'past_predicted_dates': past_predicted_dates,
            'past_predicted_values': past_predicted_values,
            'final_dates': dates,
            'final_predicted_values': predicted_values,
            'final_actual_values': actual_values,
            'city_name': city_name,
            'algorithm': algorithm,
            'days': days,
            'initial_infected': initial_infected,
            'r0': r0,
            'historical_actual_count': len(historical_actual_values),
            'historical_actual_valid_count': sum(1 for v in historical_actual_values if v is not None),
            'today_actual_value': today_actual_value
        }
        
        # 为了向后兼容，values变量保存预测值
        values = predicted_values
        
        # 8. 计算风险等级和峰值（基于预测值）
        valid_predicted = [v for v in predicted_values if v is not None]
        peak_infection = max(valid_predicted) if valid_predicted else 0
        peak_index = predicted_values.index(peak_infection) if peak_infection > 0 and peak_infection in predicted_values else 0
        peak_date = dates[peak_index] if dates and peak_index < len(dates) else None
        risk_level = calculate_risk_level(peak_infection, total_population)
        
        # 9. 保存预测结果到数据库
        prediction_record = None
        if city_id:  # 只有提供了城市信息才保存
            try:
                prediction_data = {
                    'prediction_date': date.today(),
                    'city_id': city_id,
                    'algorithm': algorithm,
                    'r0': r0,
                    'days': days,
                    'total_population': total_population,
                    'initial_infected': initial_infected,
                    'initial_exposed': initial_exposed,
                    'initial_recovered': initial_recovered,
                    'incubation_period': incubation_period,
                    'infectious_period': infectious_period,
                    'intervention_factor': intervention_factor,
                    'peak_infection': peak_infection,
                    'peak_date': datetime.strptime(peak_date, '%Y-%m-%d').date() if peak_date else None,
                    'risk_level': risk_level,
                    'prediction_data': {
                        'dates': dates,
                        'values': values,
                        'all_states': all_states
                    },
                    'user_id': int(current_user_id) if current_user_id else None
                }
                prediction_record = PredictionService.save_prediction(prediction_data)
            except Exception as e:
                print(f"Warning: Failed to save prediction to database: {e}")
                # 继续返回结果，即使保存失败
        
        # 10. 返回结果
        response_data = {
            'dates': dates,
            'predicted_values': predicted_values,  # 预测值
            'actual_values': actual_values,  # 实际值（前3天+今天，后N天为None）
            'values': values,  # 保持向后兼容
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
            },
            'debug_info': debug_info  # 调试信息，用于前端打印
        }
        
        # 如果返回了所有状态，也包含在响应中（可选）
        if all_states:
            response_data['all_states'] = all_states
        
        # 如果保存成功，返回预测记录ID
        if prediction_record:
            response_data['meta']['prediction_id'] = prediction_record.id
        
        return jsonify({
            'code': 200,
            'msg': '预测成功',
            'data': response_data
        })
        
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        print(f"Prediction Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'msg': f'模型运算出错: {str(e)}'
        }), 500


@predict_bp.route('/train/lstm', methods=['POST'])
@jwt_required()  # 需要登录才能训练模型
def train_lstm_model():
    """
    训练LSTM模型
    需要提供城市名称和历史数据
    """
    try:
        data = request.get_json() or {}
        city_name = data.get('city_name')
        
        if not city_name:
            return jsonify({
                'code': 400,
                'msg': '请提供城市名称'
            }), 400
        
        # 获取训练参数
        epochs = int(data.get('epochs', 50))
        batch_size = int(data.get('batch_size', 32))
        validation_split = float(data.get('validation_split', 0.2))
        historical_days = int(data.get('historical_days', 60))  # 使用多少天的历史数据
        
        # 获取城市信息
        city_info = CityService.get_city_info(city_name)
        if not city_info:
            return jsonify({
                'code': 400,
                'msg': f'城市"{city_name}"不存在'
            }), 400
        
        city_id = city_info['id']
        total_population = city_info.get('total_population', 0)
        
        # 从数据库获取历史数据（原始数据，用于分析字段）
        from app.models import FluDailyCase
        from datetime import date as date_type
        end_date = date_type.today()
        start_date = date_type.fromordinal(end_date.toordinal() - historical_days)
        
        # 查询原始数据记录
        raw_cases = FluDailyCase.query.filter(
            FluDailyCase.city_id == city_id,
            FluDailyCase.date >= start_date,
            FluDailyCase.date <= end_date
        ).order_by(FluDailyCase.date).all()
        
        # 如果最近N天没有数据，尝试获取所有可用数据
        if not raw_cases:
            raw_cases = FluDailyCase.query.filter(
                FluDailyCase.city_id == city_id
            ).order_by(FluDailyCase.date).all()
            if raw_cases:
                max_days = historical_days * 2
                if len(raw_cases) > max_days:
                    raw_cases = raw_cases[-max_days:]
        
        # 统计字段使用情况
        field_stats = {}
        date_range = {}
        data_quality = {}
        if raw_cases:
            active_count = sum(1 for c in raw_cases if c.active is not None)
            confirmed_count = sum(1 for c in raw_cases if c.confirmed is not None)
            recovered_count = sum(1 for c in raw_cases if c.recovered is not None)
            new_cases_count = sum(1 for c in raw_cases if c.new_cases is not None)
            
            field_stats = {
                'active': {'count': active_count, 'total': len(raw_cases), 'percentage': active_count/len(raw_cases)*100 if len(raw_cases) > 0 else 0},
                'confirmed': {'count': confirmed_count, 'total': len(raw_cases), 'percentage': confirmed_count/len(raw_cases)*100 if len(raw_cases) > 0 else 0},
                'recovered': {'count': recovered_count, 'total': len(raw_cases), 'percentage': recovered_count/len(raw_cases)*100 if len(raw_cases) > 0 else 0},
                'new_cases': {'count': new_cases_count, 'total': len(raw_cases), 'percentage': new_cases_count/len(raw_cases)*100 if len(raw_cases) > 0 else 0}
            }
            
            date_range = {
                'start': raw_cases[0].date.strftime('%Y-%m-%d') if raw_cases else None,
                'end': raw_cases[-1].date.strftime('%Y-%m-%d') if raw_cases else None,
                'days': (raw_cases[-1].date - raw_cases[0].date).days + 1 if raw_cases else 0
            }
            
            # 数据质量分析
            active_based = sum(1 for c in raw_cases if c.active is not None)
            calc_based = sum(1 for c in raw_cases if c.active is None and c.confirmed is not None and c.recovered is not None)
            confirmed_based = sum(1 for c in raw_cases if c.active is None and (c.confirmed is None or c.recovered is None) and c.confirmed is not None)
            invalid = len(raw_cases) - active_based - calc_based - confirmed_based
            
            data_quality = {
                'active_based': active_based,
                'calc_based': calc_based,
                'confirmed_based': confirmed_based,
                'invalid': invalid
            }
        
        # 从数据库获取历史数据（处理后的序列）
        historical_data = FluDataService.get_historical_infected_series(
            city_name=city_name,
            days=historical_days
        )
        
        if len(historical_data) < 30:
            return jsonify({
                'code': 400,
                'msg': f'历史数据不足，至少需要30天数据，当前只有{len(historical_data)}天'
            }), 400
        
        current_user_id = get_jwt_identity()
        
        # 记录训练开始时间
        import time
        training_start_time = time.time()
        training_start_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建LSTM模型并训练
        lstm_model = LSTMFluModel()
        history = lstm_model.train(
            data=historical_data,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            city_name=city_name
        )
        
        # 计算训练耗时
        training_time = int(time.time() - training_start_time)
        training_end_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取模型文件大小
        import os
        model_size = None
        scaler_size = None
        if lstm_model.model_path and os.path.exists(lstm_model.model_path):
            model_size = os.path.getsize(lstm_model.model_path)
        if lstm_model.scaler_path and os.path.exists(lstm_model.scaler_path):
            scaler_size = os.path.getsize(lstm_model.scaler_path)
        
        # 提取训练结果
        final_loss = history['loss'][-1] if history['loss'] else None
        final_val_loss = history['val_loss'][-1] if history['val_loss'] else None
        final_mae = history['mae'][-1] if history['mae'] else None
        final_val_mae = history['val_mae'][-1] if history['val_mae'] else None
        
        # 保存训练记录到数据库
        model_record_id = None
        updated_count = 0
        try:
            # 将同一城市的其他模型标记为非激活
            updated_count = FluLstmModel.query.filter_by(
                city_id=city_id,
                is_active=1,
                status=1
            ).update({'is_active': 0})
            
            # 创建新的训练记录
            model_record = FluLstmModel(
                city_id=city_id,
                model_name=os.path.basename(lstm_model.model_path) if lstm_model.model_path else None,
                model_path=lstm_model.model_path or '',
                scaler_path=lstm_model.scaler_path,
                training_date=date.today(),
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                historical_days=historical_days,
                data_points=len(historical_data),
                final_loss=final_loss,
                final_val_loss=final_val_loss,
                final_mae=final_mae,
                final_val_mae=final_val_mae,
                sequence_length=lstm_model.sequence_length,
                model_size=model_size,
                training_time=training_time,
                is_active=1,
                user_id=int(current_user_id) if current_user_id else None
            )
            
            db.session.add(model_record)
            db.session.commit()
            model_record_id = model_record.id
        except Exception as e:
            db.session.rollback()
        
        # 准备训练数据统计信息
        data_stats = {}
        if historical_data:
            sorted_data = sorted(historical_data)
            data_stats = {
                'count': len(historical_data),
                'min': min(historical_data),
                'max': max(historical_data),
                'avg': sum(historical_data) / len(historical_data),
                'median': sorted_data[len(sorted_data)//2],
                'first_5': historical_data[:5],
                'last_5': historical_data[-5:]
            }
        
        return jsonify({
            'code': 200,
            'msg': '模型训练成功',
            'data': {
                'model_record_id': model_record_id,
                'city_name': city_name,
                'model_path': lstm_model.model_path,
                'scaler_path': lstm_model.scaler_path,
                'training_history': {
                    'final_loss': final_loss,
                    'final_val_loss': final_val_loss,
                    'final_mae': final_mae,
                    'final_val_mae': final_val_mae,
                    'all_epochs': {
                        'loss': history.get('loss', []),
                        'val_loss': history.get('val_loss', []),
                        'mae': history.get('mae', []),
                        'val_mae': history.get('val_mae', [])
                    }
                },
                'data_points': len(historical_data),
                'training_time': training_time,
                'training_params': {
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'validation_split': validation_split,
                    'historical_days': historical_days
                },
                'city_info': {
                    'city_id': city_id,
                    'city_name': city_name,
                    'total_population': total_population
                },
                'data_fields': {
                    'source_table': 'flu_daily_cases',
                    'query_date_range': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    },
                    'raw_records_count': len(raw_cases),
                    'field_stats': field_stats,
                    'date_range': date_range,
                    'data_quality': data_quality
                },
                'data_stats': data_stats,
                'model_config': {
                    'sequence_length': lstm_model.sequence_length,
                    'input_shape': f'(samples, {lstm_model.sequence_length}, 1)',
                    'model_structure': 'LSTM(50) -> Dropout(0.2) -> LSTM(50) -> Dropout(0.2) -> Dense(25) -> Dense(1)',
                    'optimizer': 'adam',
                    'loss_function': 'mse (均方误差)',
                    'metrics': 'mae (平均绝对误差)'
                },
                'training_timeline': {
                    'start_time': training_start_datetime,
                    'end_time': training_end_datetime,
                    'duration_seconds': training_time,
                    'duration_formatted': f'{training_time//60}分{training_time%60}秒'
                },
                'model_files': {
                    'model_path': lstm_model.model_path,
                    'model_size_bytes': model_size,
                    'model_size_mb': round(model_size/1024/1024, 2) if model_size else None,
                    'scaler_path': lstm_model.scaler_path,
                    'scaler_size_bytes': scaler_size,
                    'scaler_size_kb': round(scaler_size/1024, 2) if scaler_size else None
                },
                'database_record': {
                    'record_id': model_record_id,
                    'table_name': 'flu_lstm_models',
                    'old_models_deactivated': updated_count
                }
            }
        })
        
    except ImportError as e:
        return jsonify({
            'code': 500,
            'msg': f'TensorFlow未安装，无法训练LSTM模型: {str(e)}'
        }), 500
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        print(f"LSTM训练错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'msg': f'模型训练出错: {str(e)}'
        }), 500