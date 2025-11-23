from . import db
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(db.Model):
    __tablename__ = 'sys_users'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 存储加密后的哈希值
    real_name = db.Column(db.String(64))
    role = db.Column(db.String(20), default='public')
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        """
        返回给前端的信息
        警告：绝对不要在这里包含 self.password
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


# ============================================
# 地区相关模型
# ============================================

class Province(db.Model):
    """省份表"""
    __tablename__ = 'provinces'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    province_code = db.Column(db.String(10), unique=True, nullable=False)
    province_name = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    cities = relationship('City', back_populates='province', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'province_code': self.province_code,
            'province_name': self.province_name
        }


class City(db.Model):
    """城市表"""
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city_code = db.Column(db.String(10), unique=True, nullable=False)
    city_name = db.Column(db.String(50), nullable=False)
    province_id = db.Column(db.Integer, ForeignKey('provinces.id'), nullable=False)
    latitude = db.Column(db.Numeric(10, 6))
    longitude = db.Column(db.Numeric(10, 6))
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    province = relationship('Province', back_populates='cities')
    population = relationship('CityPopulation', back_populates='city', uselist=False)
    daily_cases = relationship('FluDailyCase', back_populates='city', lazy='dynamic')
    predictions = relationship('FluSeirPrediction', back_populates='city', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'city_code': self.city_code,
            'city_name': self.city_name,
            'province_id': self.province_id,
            'province_name': self.province.province_name if self.province else None,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None
        }


class District(db.Model):
    """区县表"""
    __tablename__ = 'districts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    district_code = db.Column(db.String(10), unique=True, nullable=False)
    district_name = db.Column(db.String(50), nullable=False)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    city = relationship('City')

    def to_dict(self):
        return {
            'id': self.id,
            'district_code': self.district_code,
            'district_name': self.district_name,
            'city_id': self.city_id
        }


class CityPopulation(db.Model):
    """城市人口配置表"""
    __tablename__ = 'city_population'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), unique=True, nullable=False)
    total_population = db.Column(db.Integer, nullable=False, default=5000000)
    population_year = db.Column(db.Integer)
    data_source = db.Column(db.String(100))
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    city = relationship('City', back_populates='population')

    def to_dict(self):
        return {
            'id': self.id,
            'city_id': self.city_id,
            'city_name': self.city.city_name if self.city else None,
            'total_population': self.total_population,
            'population_year': self.population_year,
            'data_source': self.data_source
        }


# ============================================
# 流感数据相关模型
# ============================================

class FluDailyCase(db.Model):
    """流感每日病例数据表"""
    __tablename__ = 'flu_daily_cases'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    confirmed = db.Column(db.Integer, default=0)
    active = db.Column(db.Integer, default=0)  # 当前活跃病例数（用于SEIR初始感染数）
    recovered = db.Column(db.Integer, default=0)  # 累计康复数（用于SEIR初始康复者）
    deaths = db.Column(db.Integer, default=0)
    new_cases = db.Column(db.Integer, default=0)
    new_recovered = db.Column(db.Integer, default=0)
    new_deaths = db.Column(db.Integer, default=0)
    hospitalized = db.Column(db.Integer, default=0)
    severe = db.Column(db.Integer, default=0)
    data_source = db.Column(db.String(100))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    city = relationship('City', back_populates='daily_cases')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'city_id': self.city_id,
            'city_name': self.city.city_name if self.city else None,
            'confirmed': self.confirmed,
            'active': self.active,
            'recovered': self.recovered,
            'deaths': self.deaths,
            'new_cases': self.new_cases,
            'new_recovered': self.new_recovered,
            'new_deaths': self.new_deaths,
            'hospitalized': self.hospitalized,
            'severe': self.severe
        }


class FluModelConfig(db.Model):
    """流感模型参数配置表"""
    __tablename__ = 'flu_model_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_name = db.Column(db.String(100), nullable=False)
    config_type = db.Column(db.String(20), default='scenario')
    r0 = db.Column(db.Numeric(5, 2), nullable=False)
    incubation_period = db.Column(db.Numeric(4, 2), default=5.0)
    infectious_period = db.Column(db.Numeric(4, 2), default=7.0)
    intervention_factor = db.Column(db.Numeric(3, 2), default=1.0)
    vaccination_rate = db.Column(db.Numeric(4, 3), default=0.0)
    mortality_rate = db.Column(db.Numeric(6, 5), default=0.0001)
    days = db.Column(db.Integer, default=3)  # 预测天数，默认3天
    default_algorithm = db.Column(db.String(20), default='seir')  # 默认预测算法：seir/lstm/prophet
    description = db.Column(db.Text)
    is_default = db.Column(db.SmallInteger, default=0)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            return {
                'id': self.id if hasattr(self, 'id') else None,
                'config_name': self.config_name if hasattr(self, 'config_name') else '默认配置',
                'config_type': getattr(self, 'config_type', 'default'),
                'r0': float(self.r0) if hasattr(self, 'r0') and self.r0 is not None else 1.4,
                'incubation_period': float(self.incubation_period) if hasattr(self, 'incubation_period') and self.incubation_period is not None else 5.0,
                'infectious_period': float(self.infectious_period) if hasattr(self, 'infectious_period') and self.infectious_period is not None else 7.0,
                'intervention_factor': float(self.intervention_factor) if hasattr(self, 'intervention_factor') and self.intervention_factor is not None else 1.0,
                'vaccination_rate': float(self.vaccination_rate) if hasattr(self, 'vaccination_rate') and self.vaccination_rate is not None else None,
                'mortality_rate': float(self.mortality_rate) if hasattr(self, 'mortality_rate') and self.mortality_rate is not None else None,
                'days': int(self.days) if hasattr(self, 'days') and self.days is not None else 3,
                'default_algorithm': self.default_algorithm if hasattr(self, 'default_algorithm') and self.default_algorithm else 'seir',
                'description': getattr(self, 'description', None),
                'is_default': getattr(self, 'is_default', 0),
                'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self, 'updated_at') and self.updated_at else None
            }
        except Exception as e:
            import traceback
            print(f"Error in FluModelConfig.to_dict(): {str(e)}")
            print(traceback.format_exc())
            # 返回基本字段
            return {
                'default_algorithm': 'seir',
                'r0': 1.4,
                'incubation_period': 5.0,
                'infectious_period': 7.0,
                'intervention_factor': 1.0,
                'days': 3
            }


class FluSeirPrediction(db.Model):
    """SEIR模型预测结果表"""
    __tablename__ = 'flu_seir_predictions'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    prediction_date = db.Column(db.Date, nullable=False)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    algorithm = db.Column(db.String(20), nullable=False, default='seir')
    r0 = db.Column(db.Numeric(5, 2), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    total_population = db.Column(db.Integer, nullable=False)
    initial_infected = db.Column(db.Integer, nullable=False)
    initial_exposed = db.Column(db.Integer)
    initial_recovered = db.Column(db.Integer, default=0)
    incubation_period = db.Column(db.Numeric(4, 2), default=5.0)
    infectious_period = db.Column(db.Numeric(4, 2), default=7.0)
    intervention_factor = db.Column(db.Numeric(3, 2), default=1.0)
    peak_infection = db.Column(db.Integer)
    peak_date = db.Column(db.Date)
    risk_level = db.Column(db.String(10))
    prediction_data = db.Column(db.JSON)  # 存储预测详细数据
    user_id = db.Column(db.BigInteger, ForeignKey('sys_users.user_id'))
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    city = relationship('City', back_populates='predictions')
    user = relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d') if self.prediction_date else None,
            'city_id': self.city_id,
            'city_name': self.city.city_name if self.city else None,
            'algorithm': self.algorithm,
            'r0': float(self.r0) if self.r0 else None,
            'days': self.days,
            'total_population': self.total_population,
            'initial_infected': self.initial_infected,
            'initial_exposed': self.initial_exposed,
            'initial_recovered': self.initial_recovered,
            'incubation_period': float(self.incubation_period) if self.incubation_period else None,
            'infectious_period': float(self.infectious_period) if self.infectious_period else None,
            'peak_infection': self.peak_infection,
            'peak_date': self.peak_date.strftime('%Y-%m-%d') if self.peak_date else None,
            'risk_level': self.risk_level,
            'prediction_data': self.prediction_data,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class FluPredictionDetail(db.Model):
    """预测结果详情表（每日数据）"""
    __tablename__ = 'flu_prediction_details'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    prediction_id = db.Column(db.BigInteger, ForeignKey('flu_seir_predictions.id'), nullable=False)
    predict_date = db.Column(db.Date, nullable=False)
    day_index = db.Column(db.Integer, nullable=False)
    susceptible = db.Column(db.Integer)
    exposed = db.Column(db.Integer)
    infected = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    new_cases = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    prediction = relationship('FluSeirPrediction')

    def to_dict(self):
        return {
            'id': self.id,
            'prediction_id': self.prediction_id,
            'predict_date': self.predict_date.strftime('%Y-%m-%d') if self.predict_date else None,
            'day_index': self.day_index,
            'susceptible': self.susceptible,
            'exposed': self.exposed,
            'infected': self.infected,
            'recovered': self.recovered,
            'new_cases': self.new_cases
        }


class FluLstmModel(db.Model):
    """LSTM模型训练记录表"""
    __tablename__ = 'flu_lstm_models'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    model_name = db.Column(db.String(200), nullable=False)
    model_path = db.Column(db.String(500), nullable=False)
    scaler_path = db.Column(db.String(500))
    training_date = db.Column(db.Date, nullable=False)
    epochs = db.Column(db.Integer, nullable=False)
    batch_size = db.Column(db.Integer, nullable=False)
    validation_split = db.Column(db.Numeric(3, 2), nullable=False)
    historical_days = db.Column(db.Integer, nullable=False)
    data_points = db.Column(db.Integer, nullable=False)
    final_loss = db.Column(db.Numeric(10, 6))
    final_val_loss = db.Column(db.Numeric(10, 6))
    final_mae = db.Column(db.Numeric(10, 2))
    final_val_mae = db.Column(db.Numeric(10, 2))
    sequence_length = db.Column(db.Integer, default=14)
    model_size = db.Column(db.BigInteger)
    training_time = db.Column(db.Integer)
    status = db.Column(db.SmallInteger, default=1)
    is_active = db.Column(db.SmallInteger, default=1)  # 是否当前激活模型
    user_id = db.Column(db.BigInteger, ForeignKey('sys_users.user_id'))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    city = relationship('City')
    user = relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'city_id': self.city_id,
            'city_name': self.city.city_name if self.city else None,
            'model_name': self.model_name,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path,
            'training_date': self.training_date.strftime('%Y-%m-%d') if self.training_date else None,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'validation_split': float(self.validation_split) if self.validation_split else None,
            'historical_days': self.historical_days,
            'data_points': self.data_points,
            'final_loss': float(self.final_loss) if self.final_loss else None,
            'final_val_loss': float(self.final_val_loss) if self.final_val_loss else None,
            'final_mae': float(self.final_mae) if self.final_mae else None,
            'final_val_mae': float(self.final_val_mae) if self.final_val_mae else None,
            'sequence_length': self.sequence_length,
            'model_size': self.model_size,
            'training_time': self.training_time,
            'status': self.status,
            'is_active': self.is_active,
            'user_id': self.user_id,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }