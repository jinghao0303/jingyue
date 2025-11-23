# file: app/utils/db_service.py
"""
数据库查询服务
用于SEIR模型从数据库获取参数和历史数据
"""
from app import db
from app.models import (
    City, CityPopulation, FluDailyCase, FluModelConfig,
    Province, District, FluLstmModel
)
from datetime import datetime, date
from sqlalchemy import desc


class CityService:
    """城市相关查询服务"""

    @staticmethod
    def get_city_by_name(city_name: str):
        """
        根据城市名称获取城市信息（支持多表查询）
        返回：City对象，包含省份信息
        """
        return City.query.join(Province).filter(
            City.city_name == city_name,
            City.status == 1
        ).first()

    @staticmethod
    def get_city_population(city_name: str = None, city_id: int = None):
        """
        获取城市人口数
        参数：city_name 或 city_id 二选一
        返回：人口数（int），如果不存在返回None
        """
        if city_id:
            city_pop = CityPopulation.query.filter_by(
                city_id=city_id,
                status=1
            ).first()
        elif city_name:
            city = CityService.get_city_by_name(city_name)
            if city and city.population:
                city_pop = city.population
            else:
                return None
        else:
            return None

        return city_pop.total_population if city_pop else None

    @staticmethod
    def get_city_info(city_name: str):
        """
        获取完整的城市信息（多表查询）
        返回：dict，包含城市、省份、人口等信息
        """
        city = CityService.get_city_by_name(city_name)
        if not city:
            return None

        result = city.to_dict()
        
        # 添加人口信息
        if city.population:
            result['total_population'] = city.population.total_population
            result['population_year'] = city.population.population_year
        else:
            result['total_population'] = 5000000  # 默认值
            result['population_year'] = None

        return result


class FluDataService:
    """流感数据查询服务"""

    @staticmethod
    def get_latest_cases(city_name: str = None, city_id: int = None):
        """
        获取指定城市的最新病例数据
        用于SEIR模型的初始状态
        返回：FluDailyCase对象，如果不存在返回None
        """
        if city_id:
            latest = FluDailyCase.query.filter_by(
                city_id=city_id
            ).order_by(desc(FluDailyCase.date)).first()
        elif city_name:
            city = CityService.get_city_by_name(city_name)
            if not city:
                return None
            latest = FluDailyCase.query.filter_by(
                city_id=city.id
            ).order_by(desc(FluDailyCase.date)).first()
        else:
            return None

        return latest

    @staticmethod
    def get_initial_state(city_name: str = None, city_id: int = None):
        """
        获取SEIR模型的初始状态
        返回：dict，包含 initial_infected, initial_exposed, initial_recovered
        """
        latest = FluDataService.get_latest_cases(city_name, city_id)
        
        if latest:
            # 从历史数据获取
            initial_infected = latest.active or 100  # 活跃病例作为初始感染数
            initial_recovered = latest.recovered or 0
            # 潜伏者通常是感染者的1.5-2倍
            initial_exposed = int(initial_infected * 2) if initial_infected > 0 else 0
        else:
            # 使用默认值
            initial_infected = 100
            initial_exposed = 200
            initial_recovered = 0

        return {
            'initial_infected': initial_infected,
            'initial_exposed': initial_exposed,
            'initial_recovered': initial_recovered
        }

    @staticmethod
    def get_historical_data(city_name: str, days: int = 30):
        """
        获取历史数据（用于模型验证）
        返回：list of FluDailyCase对象
        """
        city = CityService.get_city_by_name(city_name)
        if not city:
            return []

        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)

        return FluDailyCase.query.filter(
            FluDailyCase.city_id == city.id,
            FluDailyCase.date >= start_date,
            FluDailyCase.date <= end_date
        ).order_by(FluDailyCase.date).all()
    
    @staticmethod
    def get_historical_infected_series(city_name: str, days: int = 60):
        """
        获取历史感染数据序列（用于LSTM训练和预测）
        返回：list of float，按日期排序的感染人数列表
        """
        city = CityService.get_city_by_name(city_name)
        if not city:
            print(f"警告：未找到城市 '{city_name}'")
            return []
        
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)
        
        # 查询数据，优先使用有active字段的数据，如果没有则使用confirmed字段
        cases = FluDailyCase.query.filter(
            FluDailyCase.city_id == city.id,
            FluDailyCase.date >= start_date,
            FluDailyCase.date <= end_date
        ).order_by(FluDailyCase.date).all()
        
        # 如果最近N天没有数据，尝试获取所有可用数据
        if not cases:
            print(f"信息：城市 '{city_name}' 在最近 {days} 天内没有数据，尝试获取所有可用数据...")
            cases = FluDailyCase.query.filter(
                FluDailyCase.city_id == city.id
            ).order_by(FluDailyCase.date).all()
            
            if not cases:
                print(f"警告：城市 '{city_name}' 没有任何历史数据")
                return []
            else:
                # 只取最近的数据（最多取days*2天，避免数据过多）
                max_days = days * 2
                if len(cases) > max_days:
                    cases = cases[-max_days:]
                print(f"信息：获取到 {len(cases)} 条历史数据（日期范围：{cases[0].date} 到 {cases[-1].date}）")
        
        # 提取活跃病例数（active字段）作为感染人数
        # 如果active为NULL，尝试使用confirmed - recovered作为活跃病例数
        infected_series = []
        for case in cases:
            if case.active is not None:
                infected_series.append(float(case.active))
            elif case.confirmed is not None and case.recovered is not None:
                # 使用 confirmed - recovered 作为活跃病例数
                active = max(0, case.confirmed - case.recovered)
                infected_series.append(float(active))
            elif case.confirmed is not None:
                # 如果只有confirmed，使用它（但这不是理想情况）
                infected_series.append(float(case.confirmed))
            else:
                # 如果都没有，跳过这条记录（不添加0，避免数据质量差）
                continue
        
        print(f"信息：城市 '{city_name}' 获取到 {len(infected_series)} 条有效数据（共查询到 {len(cases)} 条记录）")
        return infected_series


class ModelConfigService:
    """模型配置查询服务"""

    @staticmethod
    def get_default_config():
        """
        获取默认模型配置
        返回：FluModelConfig对象或None
        如果字段不存在，使用原始SQL查询避免错误
        """
        try:
            # 先尝试正常查询
            return FluModelConfig.query.filter_by(
                is_default=1,
                status=1
            ).first()
        except Exception as e:
            # 如果查询失败（可能是字段不存在），使用原始SQL
            error_str = str(e)
            if 'Unknown column' in error_str or 'days' in error_str or 'default_algorithm' in error_str:
                try:
                    # 先检查哪些字段存在
                    from sqlalchemy import text, inspect
                    inspector = inspect(db.engine)
                    columns = [col['name'] for col in inspector.get_columns('flu_model_config')]
                    
                    # 构建SQL查询，动态包含存在的字段
                    base_fields = [
                        'id', 'config_name', 'config_type', 'r0',
                        'incubation_period', 'infectious_period', 'intervention_factor',
                        'vaccination_rate', 'mortality_rate', 'description',
                        'is_default', 'status', 'created_at', 'updated_at'
                    ]
                    
                    select_fields = base_fields.copy()
                    field_index_map = {}
                    
                    # 如果字段存在，添加到查询中
                    if 'days' in columns:
                        select_fields.append('days')
                    if 'default_algorithm' in columns:
                        select_fields.append('default_algorithm')
                    
                    # 构建字段索引映射
                    for i, field in enumerate(select_fields):
                        field_index_map[field] = i
                    
                    sql_query = f"""
                        SELECT {', '.join(select_fields)}
                        FROM flu_model_config
                        WHERE is_default = 1 AND status = 1
                        LIMIT 1
                    """
                    
                    result = db.session.execute(text(sql_query))
                    row = result.fetchone()
                    if row:
                        # 创建一个简单的对象来存储数据
                        class SimpleConfig:
                            def __init__(self, row_data, field_map, available_columns):
                                self.id = row_data[field_map['id']]
                                self.config_name = row_data[field_map['config_name']]
                                self.config_type = row_data[field_map['config_type']]
                                self.r0 = row_data[field_map['r0']]
                                self.incubation_period = row_data[field_map['incubation_period']]
                                self.infectious_period = row_data[field_map['infectious_period']]
                                self.intervention_factor = row_data[field_map['intervention_factor']]
                                self.vaccination_rate = row_data[field_map.get('vaccination_rate', None)]
                                self.mortality_rate = row_data[field_map.get('mortality_rate', None)]
                                self.description = row_data[field_map.get('description', None)]
                                self.is_default = row_data[field_map['is_default']]
                                self.status = row_data[field_map['status']]
                                self.created_at = row_data[field_map.get('created_at', None)]
                                self.updated_at = row_data[field_map.get('updated_at', None)]
                                
                                # 如果字段存在，使用数据库中的值；否则使用默认值
                                if 'days' in available_columns and 'days' in field_map:
                                    self.days = row_data[field_map['days']] or 3
                                else:
                                    self.days = 3
                                
                                if 'default_algorithm' in available_columns and 'default_algorithm' in field_map:
                                    self.default_algorithm = row_data[field_map['default_algorithm']] or 'seir'
                                else:
                                    self.default_algorithm = 'seir'
                        
                        return SimpleConfig(row, field_index_map, columns)
                    return None
                except Exception as e2:
                    import traceback
                    print(f"Error in fallback SQL query: {str(e2)}")
                    print(traceback.format_exc())
                    return None
            else:
                import traceback
                print(f"Error in ModelConfigService.get_default_config(): {str(e)}")
                print(traceback.format_exc())
                return None

    @staticmethod
    def get_config_by_name(config_name: str):
        """
        根据配置名称获取配置
        返回：FluModelConfig对象
        """
        return FluModelConfig.query.filter_by(
            config_name=config_name,
            status=1
        ).first()

    @staticmethod
    def get_all_configs():
        """
        获取所有可用的配置
        返回：list of FluModelConfig对象
        """
        return FluModelConfig.query.filter_by(status=1).all()


class PredictionService:
    """预测结果服务"""

    @staticmethod
    def save_prediction(prediction_data: dict):
        """
        保存预测结果到数据库
        参数：prediction_data字典，包含所有预测信息
        返回：FluSeirPrediction对象
        """
        from app.models import FluSeirPrediction

        prediction = FluSeirPrediction(
            prediction_date=prediction_data.get('prediction_date', date.today()),
            city_id=prediction_data['city_id'],
            algorithm=prediction_data.get('algorithm', 'seir'),
            r0=prediction_data['r0'],
            days=prediction_data['days'],
            total_population=prediction_data['total_population'],
            initial_infected=prediction_data['initial_infected'],
            initial_exposed=prediction_data.get('initial_exposed'),
            initial_recovered=prediction_data.get('initial_recovered', 0),
            incubation_period=prediction_data.get('incubation_period', 5.0),
            infectious_period=prediction_data.get('infectious_period', 7.0),
            intervention_factor=prediction_data.get('intervention_factor', 1.0),
            peak_infection=prediction_data.get('peak_infection'),
            peak_date=prediction_data.get('peak_date'),
            risk_level=prediction_data.get('risk_level'),
            prediction_data=prediction_data.get('prediction_data'),  # JSON格式
            user_id=prediction_data.get('user_id')
        )

        try:
            db.session.add(prediction)
            db.session.commit()
            return prediction
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_predictions_by_city(city_name: str, limit: int = 10):
        """
        获取指定城市的预测历史
        返回：list of FluSeirPrediction对象
        """
        city = CityService.get_city_by_name(city_name)
        if not city:
            return []

        return FluSeirPrediction.query.filter_by(
            city_id=city.id,
            status=1
        ).order_by(desc(FluSeirPrediction.created_at)).limit(limit).all()


class LstmModelService:
    """LSTM模型服务"""

    @staticmethod
    def get_active_model(city_name: str = None, city_id: int = None):
        """
        获取指定城市的激活LSTM模型
        参数：city_name 或 city_id 二选一
        返回：FluLstmModel对象，如果不存在返回None
        """
        if city_id:
            model = FluLstmModel.query.filter_by(
                city_id=city_id,
                is_active=1,
                status=1
            ).first()
        elif city_name:
            city = CityService.get_city_by_name(city_name)
            if not city:
                return None
            model = FluLstmModel.query.filter_by(
                city_id=city.id,
                is_active=1,
                status=1
            ).first()
        else:
            return None

        return model

