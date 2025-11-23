# file: app/utils/prophet_model.py
"""
Prophet 时间序列预测模型用于流感预测
Prophet是Facebook开发的时间序列预测库，适合有季节性模式的数据
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Tuple, List, Optional, Dict
import json

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None
    print("⚠️ 警告: Prophet未安装，将使用简单预测方法。安装命令: pip install prophet")


class ProphetFluModel:
    """
    Prophet模型用于流感感染人数预测
    适合有季节性、趋势性的时间序列数据
    """
    
    def __init__(self):
        """初始化Prophet模型"""
        self.model = None
        self.model_dir = "models"
        
        # 创建模型目录
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir, exist_ok=True)
    
    def prepare_data(self, data: List[float], dates: Optional[List[str]] = None) -> pd.DataFrame:
        """
        准备Prophet模型所需的数据格式
        
        :param data: 时间序列数据（一维数组）
        :param dates: 日期列表（可选），如果为None则自动生成
        :return: DataFrame with columns ['ds', 'y']
        """
        if dates is None:
            # 如果没有提供日期，从今天往前推
            end_date = date.today()
            dates = []
            for i in range(len(data) - 1, -1, -1):
                d = end_date - timedelta(days=len(data) - 1 - i)
                dates.append(d.strftime('%Y-%m-%d'))
        
        # 确保日期和数据的长度一致
        min_len = min(len(data), len(dates))
        data = data[:min_len]
        dates = dates[:min_len]
        
        # 创建DataFrame
        df = pd.DataFrame({
            'ds': pd.to_datetime(dates),
            'y': data
        })
        
        return df
    
    def train(
        self,
        data: List[float],
        dates: Optional[List[str]] = None,
        city_name: Optional[str] = None,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        seasonality_mode: str = 'additive',
        changepoint_prior_scale: float = 0.05
    ) -> Dict:
        """
        训练Prophet模型
        
        :param data: 训练数据（时间序列）
        :param dates: 日期列表（可选）
        :param city_name: 城市名称（用于保存模型）
        :param yearly_seasonality: 是否启用年度季节性
        :param weekly_seasonality: 是否启用周季节性
        :param daily_seasonality: 是否启用日季节性
        :param seasonality_mode: 季节性模式（'additive' 或 'multiplicative'）
        :param changepoint_prior_scale: 变化点先验尺度（控制模型灵活性）
        :return: 训练信息
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet未安装，无法训练模型。请运行: pip install prophet")
        
        if len(data) < 30:
            raise ValueError(f"训练数据不足，至少需要30个数据点，当前只有{len(data)}个")
        
        # 准备数据
        df = self.prepare_data(data, dates)
        
        # 创建并配置Prophet模型
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            seasonality_mode=seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale
        )
        
        # 训练模型
        self.model.fit(df)
        
        # 保存模型（如果提供了城市名称）
        if city_name:
            model_path = os.path.join(
                self.model_dir,
                f"prophet_model_{city_name}_{datetime.now().strftime('%Y%m%d')}.json"
            )
            self.save_model(model_path)
        
        return {
            'data_points': len(data),
            'date_range': {
                'start': df['ds'].min().strftime('%Y-%m-%d'),
                'end': df['ds'].max().strftime('%Y-%m-%d')
            }
        }
    
    def save_model(self, model_path: str):
        """保存模型到文件"""
        if not self.model:
            raise ValueError("模型未训练，无法保存")
        
        # Prophet模型序列化（保存参数）
        model_json = {
            'yearly_seasonality': self.model.yearly_seasonality,
            'weekly_seasonality': self.model.weekly_seasonality,
            'daily_seasonality': self.model.daily_seasonality,
            'seasonality_mode': self.model.seasonality_mode,
            'changepoint_prior_scale': self.model.changepoint_prior_scale
        }
        
        with open(model_path, 'w') as f:
            json.dump(model_json, f)
    
    def load_model(self, model_path: str):
        """加载模型（Prophet模型需要重新训练，这里只加载配置）"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        with open(model_path, 'r') as f:
            model_json = json.load(f)
        
        # 重新创建模型（Prophet不支持直接加载，需要重新训练）
        self.model = Prophet(
            yearly_seasonality=model_json.get('yearly_seasonality', True),
            weekly_seasonality=model_json.get('weekly_seasonality', True),
            daily_seasonality=model_json.get('daily_seasonality', False),
            seasonality_mode=model_json.get('seasonality_mode', 'additive'),
            changepoint_prior_scale=model_json.get('changepoint_prior_scale', 0.05)
        )
    
    def predict(
        self,
        historical_data: List[float],
        days: int = 7,
        historical_dates: Optional[List[str]] = None,
        start_date: Optional[date] = None
    ) -> Tuple[List[str], List[int]]:
        """
        使用Prophet模型进行预测
        
        :param historical_data: 历史数据（用于训练和预测的输入序列）
        :param days: 预测天数
        :param historical_dates: 历史数据的日期列表（可选）
        :param start_date: 预测起始日期
        :return: (dates, predicted_values)
        """
        if not PROPHET_AVAILABLE:
            print("⚠️ Prophet库未安装，使用简单预测方法")
            return self._simple_predict(historical_data, days, start_date)
        
        if len(historical_data) < 30:
            print(f"⚠️ 历史数据不足（{len(historical_data)}天），Prophet需要至少30天数据")
            raise ValueError(f"历史数据不足，至少需要30个数据点，当前只有{len(historical_data)}个")
        
        # 如果没有模型，先训练
        if self.model is None:
            print(f"📊 正在使用Prophet模型进行预测（数据量：{len(historical_data)}天）...")
            df = self.prepare_data(historical_data, historical_dates)
            self.model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            self.model.fit(df)
            print("✅ Prophet模型训练完成")
        
        # 创建未来日期DataFrame
        if start_date is None:
            start_date = date.today()
        
        # 生成未来日期
        future_dates = []
        for i in range(days):
            future_date = start_date + timedelta(days=i + 1)
            future_dates.append(future_date)
        
        future_df = pd.DataFrame({
            'ds': pd.to_datetime(future_dates)
        })
        
        # 进行预测
        forecast = self.model.predict(future_df)
        
        # 提取预测值
        predictions = forecast['yhat'].values
        
        # 确保预测值为非负整数
        predictions = np.maximum(predictions, 0).astype(int)
        
        # 生成日期列表
        dates = [d.strftime('%Y-%m-%d') for d in future_dates]
        
        return dates, predictions.tolist()
    
    def _simple_predict(
        self,
        historical_data: List[float],
        days: int,
        start_date: Optional[date]
    ) -> Tuple[List[str], List[int]]:
        """
        简单预测方法（当Prophet不可用时使用，优化版）
        基于历史数据的趋势和季节性进行预测
        """
        if start_date is None:
            start_date = date.today()
        
        if not historical_data or len(historical_data) == 0:
            # 如果没有历史数据，返回默认值
            current = 100
            predictions = []
            dates = []
            for i in range(days):
                predictions.append(int(current))
                pred_date = start_date + timedelta(days=i + 1)
                dates.append(pred_date.strftime('%Y-%m-%d'))
            return dates, predictions
        
        # 使用更多历史数据（至少14天，最多60天）
        lookback = min(max(14, len(historical_data)), 60)
        recent_data = historical_data[-lookback:]
        
        # 计算趋势（使用线性回归的思想）
        if len(recent_data) >= 7:
            # 短期趋势（最近7天）
            short_trend = (recent_data[-1] - recent_data[-7]) / 7
            # 中期趋势（如果数据足够）
            mid_trend = (recent_data[-1] - recent_data[0]) / len(recent_data) if len(recent_data) >= 14 else short_trend
            # 加权平均（短期权重更高）
            trend = short_trend * 0.6 + mid_trend * 0.4
        else:
            trend = (recent_data[-1] - recent_data[0]) / len(recent_data) if len(recent_data) > 1 else 0
        
        # 计算移动平均（用于平滑）
        window = min(14, len(recent_data))
        avg_value = np.mean(recent_data[-window:])
        
        # 计算周季节性（如果有足够数据）
        weekly_pattern = []
        if len(recent_data) >= 14:
            # 计算每周同一天的平均值
            for day_of_week in range(7):
                day_values = [recent_data[i] for i in range(len(recent_data) - 1, -1, -1) if i % 7 == day_of_week]
                if day_values:
                    weekly_pattern.append(np.mean(day_values))
                else:
                    weekly_pattern.append(avg_value)
        else:
            weekly_pattern = [avg_value] * 7
        
        # 当前值
        current = recent_data[-1]
        
        # 预测未来值（考虑趋势、季节性和均值回归）
        predictions = []
        dates = []
        
        for i in range(days):
            # 趋势预测
            trend_pred = current + trend
            
            # 均值回归（向移动平均回归）
            mean_reversion = avg_value * 0.2 + current * 0.8
            
            # 季节性调整（周模式）
            day_of_week = i % 7
            seasonal_factor = weekly_pattern[day_of_week] / avg_value if avg_value > 0 else 1.0
            seasonal_factor = max(0.9, min(1.1, seasonal_factor))  # 限制在0.9-1.1之间
            
            # 组合预测（趋势50%，均值回归30%，季节性20%）
            current = (trend_pred * 0.5 + mean_reversion * 0.3) * seasonal_factor + current * 0.2
            
            # 添加阻尼，避免极端预测
            if abs(trend) > current * 0.15:  # 如果趋势变化超过15%
                current = current * 0.85 + recent_data[-1] * 0.15  # 向当前值回归15%
            
            current = max(0, current)  # 确保非负
            predictions.append(int(round(current)))
            
            pred_date = start_date + timedelta(days=i + 1)
            dates.append(pred_date.strftime('%Y-%m-%d'))
        
        return dates, predictions

