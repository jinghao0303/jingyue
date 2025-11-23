# file: app/utils/lstm_model.py
"""
LSTM 深度学习模型用于流感预测
支持模型训练、保存、加载和预测
"""
import os
import numpy as np
from datetime import datetime, timedelta, date
from typing import Tuple, List, Optional, Dict
import json

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    from tensorflow.keras.metrics import MeanSquaredError
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    # 定义占位符类型，避免类型注解错误
    Sequential = None
    load_model = None
    LSTM = None
    Dense = None
    Dropout = None
    EarlyStopping = None
    ModelCheckpoint = None
    MeanSquaredError = None
    print("Warning: TensorFlow not installed. LSTM model will use mock mode.")

try:
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    MinMaxScaler = None
    print("Warning: scikit-learn not installed. LSTM model will use mock mode.")


class LSTMFluModel:
    """
    LSTM模型用于流感感染人数预测
    """
    
    def __init__(self, model_dir: str = "models"):
        """
        初始化LSTM模型
        :param model_dir: 模型保存目录（相对路径或绝对路径）
        """
        # 如果是相对路径，转换为绝对路径（相对于当前文件所在目录的父目录，即backend目录）
        if not os.path.isabs(model_dir):
            # 获取当前文件所在目录（app/utils/）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 获取backend目录
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            # 构建绝对路径
            model_dir = os.path.join(backend_dir, model_dir)
        
        self.model_dir = model_dir
        self.model = None
        if SKLEARN_AVAILABLE:
            self.scaler = MinMaxScaler(feature_range=(0, 1))
        else:
            self.scaler = None
        self.sequence_length = 14  # 使用过去14天的数据预测未来
        self.model_path = None
        self.scaler_path = None
        
        # 创建模型目录
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
    
    def prepare_data(
        self, 
        data: List[float], 
        sequence_length: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据：将时间序列转换为监督学习问题
        
        :param data: 时间序列数据（一维数组）
        :param sequence_length: 输入序列长度，默认使用self.sequence_length
        :return: (X, y) 特征和标签
        """
        if sequence_length is None:
            sequence_length = self.sequence_length
        
        if len(data) < sequence_length + 1:
            raise ValueError(f"数据长度({len(data)})必须大于序列长度({sequence_length + 1})")
        
        # 归一化数据
        if self.scaler is None:
            # 如果没有scaler，使用简单的归一化
            data_array = np.array(data)
            data_min, data_max = data_array.min(), data_array.max()
            if data_max > data_min:
                data_scaled = (data_array - data_min) / (data_max - data_min)
            else:
                data_scaled = data_array
        else:
            data_scaled = self.scaler.fit_transform(np.array(data).reshape(-1, 1))
            data_scaled = data_scaled.flatten()
        
        X, y = [], []
        for i in range(len(data_scaled) - sequence_length):
            X.append(data_scaled[i:i + sequence_length])
            y.append(data_scaled[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple[int, int]):
        """
        构建LSTM模型
        
        :param input_shape: 输入形状 (samples, timesteps, features)
        :return: Keras模型
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow未安装，无法构建LSTM模型")
        
        model = Sequential([
            # 第一层LSTM
            LSTM(50, return_sequences=True, input_shape=(input_shape[1], input_shape[2])),
            Dropout(0.2),
            
            # 第二层LSTM
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            
            # 全连接层
            Dense(25),
            Dense(1)  # 输出层：预测下一个值
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(
        self,
        data: List[float],
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        city_name: Optional[str] = None
    ) -> Dict:
        """
        训练LSTM模型
        
        :param data: 训练数据（时间序列）
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        :param validation_split: 验证集比例
        :param city_name: 城市名称（用于保存模型）
        :return: 训练历史记录
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow未安装，无法训练LSTM模型")
        
        if len(data) < self.sequence_length + 10:
            raise ValueError(f"训练数据不足，至少需要{self.sequence_length + 10}个数据点")
        
        # 准备数据
        X, y = self.prepare_data(data)
        
        # 重塑数据为LSTM输入格式 (samples, timesteps, features)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # 构建模型
        self.model = self.build_model(X.shape)
        
        # 设置模型保存路径
        if city_name:
            model_filename = f"lstm_model_{city_name}_{datetime.now().strftime('%Y%m%d')}.h5"
            self.model_path = os.path.join(self.model_dir, model_filename)
            scaler_filename = f"scaler_{city_name}_{datetime.now().strftime('%Y%m%d')}.json"
            self.scaler_path = os.path.join(self.model_dir, scaler_filename)
        else:
            model_filename = f"lstm_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
            self.model_path = os.path.join(self.model_dir, model_filename)
            scaler_filename = f"scaler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.scaler_path = os.path.join(self.model_dir, scaler_filename)
        
        # 回调函数
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            ModelCheckpoint(
                self.model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=0
            )
        ]
        
        # 训练模型
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=0
        )
        
        # 保存scaler
        self.save_scaler()
        
        return {
            'loss': history.history['loss'],
            'val_loss': history.history['val_loss'],
            'mae': history.history['mae'],
            'val_mae': history.history['val_mae']
        }
    
    def save_scaler(self):
        """保存scaler参数"""
        if self.scaler_path:
            scaler_data = {
                'min_': self.scaler.min_.tolist(),
                'scale_': self.scaler.scale_.tolist(),
                'data_min_': self.scaler.data_min_.tolist(),
                'data_max_': self.scaler.data_max_.tolist()
            }
            with open(self.scaler_path, 'w') as f:
                json.dump(scaler_data, f)
    
    def load_scaler(self, scaler_path: str):
        """加载scaler参数"""
        with open(scaler_path, 'r') as f:
            scaler_data = json.load(f)
        
        self.scaler.min_ = np.array(scaler_data['min_'])
        self.scaler.scale_ = np.array(scaler_data['scale_'])
        self.scaler.data_min_ = np.array(scaler_data['data_min_'])
        self.scaler.data_max_ = np.array(scaler_data['data_max_'])
    
    def load_model(self, model_path: str, scaler_path: Optional[str] = None):
        """
        加载已训练的模型
        
        :param model_path: 模型文件路径
        :param scaler_path: scaler文件路径（可选）
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow未安装，无法加载LSTM模型")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        try:
            # 尝试使用 custom_objects 来处理兼容性问题
            if MeanSquaredError is not None:
                custom_objects = {'mse': MeanSquaredError()}
                self.model = load_model(model_path, custom_objects=custom_objects, compile=False)
            else:
                self.model = load_model(model_path, compile=False)
        except Exception as e1:
            try:
                # 如果上面的方法失败，尝试不指定 custom_objects
                self.model = load_model(model_path, compile=False)
            except Exception as e2:
                # 如果还是失败，尝试使用 safe_mode=False（TensorFlow 2.13+）
                try:
                    self.model = load_model(model_path, compile=False, safe_mode=False)
                except Exception as e3:
                    # 最后尝试：重新编译模型
                    try:
                        self.model = load_model(model_path)
                        # 如果模型没有编译，重新编译
                        if not hasattr(self.model, 'optimizer') or self.model.optimizer is None:
                            self.model.compile(optimizer='adam', loss='mse', metrics=['mse'])
                    except Exception as e4:
                        raise Exception(f"模型加载失败: {e1}, {e2}, {e3}, {e4}")
        
        self.model_path = model_path
        
        if scaler_path and os.path.exists(scaler_path):
            self.load_scaler(scaler_path)
            self.scaler_path = scaler_path
    
    def predict(
        self,
        historical_data: List[float],
        days: int = 7,
        start_date: Optional[date] = None
    ) -> Tuple[List[str], List[int]]:
        """
        使用LSTM模型进行预测
        
        :param historical_data: 历史数据（用于预测的输入序列）
        :param days: 预测天数
        :param start_date: 预测起始日期
        :return: (dates, predicted_values)
        """
        if not TENSORFLOW_AVAILABLE or self.model is None:
            # 如果没有模型，使用简单预测
            return self._simple_predict(historical_data, days, start_date)
        
        if len(historical_data) < self.sequence_length:
            raise ValueError(f"历史数据不足，至少需要{self.sequence_length}个数据点")
        
        # 确定起始日期
        if start_date is None:
            start_date = date.today()
        
        # 归一化历史数据
        historical_array = np.array(historical_data[-self.sequence_length:])
        
        if self.scaler is None:
            # 简单归一化
            data_min, data_max = historical_array.min(), historical_array.max()
            if data_max > data_min:
                historical_scaled = (historical_array - data_min) / (data_max - data_min)
            else:
                historical_scaled = historical_array
        else:
            historical_array_2d = historical_array.reshape(-1, 1)
            historical_scaled = self.scaler.transform(historical_array_2d).flatten()
        
        # 预测
        predictions = []
        current_sequence = historical_scaled.copy()
        
        for _ in range(days):
            # 准备输入
            X_input = current_sequence[-self.sequence_length:].reshape(1, self.sequence_length, 1)
            
            # 预测下一个值
            next_pred = self.model.predict(X_input, verbose=0)[0][0]
            predictions.append(next_pred)
            
            # 更新序列（使用预测值）
            current_sequence = np.append(current_sequence, next_pred)
        
        # 反归一化
        if self.scaler is None:
            # 简单反归一化
            predictions_denorm = np.array(predictions) * (data_max - data_min) + data_min
        else:
            predictions_array = np.array(predictions).reshape(-1, 1)
            predictions_denorm = self.scaler.inverse_transform(predictions_array).flatten()
        
        # 确保预测值为非负整数
        predictions_denorm = np.maximum(predictions_denorm, 0).astype(int)
        
        # 生成日期列表
        dates = []
        for i in range(days):
            pred_date = start_date + timedelta(days=i + 1)
            dates.append(pred_date.strftime('%Y-%m-%d'))
        
        return dates, predictions_denorm.tolist()
    
    def _simple_predict(
        self,
        historical_data: List[float],
        days: int,
        start_date: Optional[date]
    ) -> Tuple[List[str], List[int]]:
        """
        简单预测方法（当模型不可用时使用，优化版）
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
        
        # 使用更多历史数据（至少14天，最多30天）
        lookback = min(max(14, len(historical_data)), 30)
        recent_data = historical_data[-lookback:]
        
        # 计算多个时间窗口的趋势
        trends = []
        weights = []
        
        # 短期趋势（最近3-7天）
        if len(recent_data) >= 7:
            short_trend = (recent_data[-1] - recent_data[-4]) / 3
            trends.append(short_trend)
            weights.append(0.4)
        
        # 中期趋势（最近7-14天）
        if len(recent_data) >= 14:
            mid_trend = (recent_data[-1] - recent_data[-7]) / 7
            trends.append(mid_trend)
            weights.append(0.35)
        
        # 长期趋势（全部数据）
        if len(recent_data) >= 2:
            long_trend = (recent_data[-1] - recent_data[0]) / len(recent_data)
            trends.append(long_trend)
            weights.append(0.25)
        
        # 计算加权平均趋势
        if trends:
            trend = sum(t * w for t, w in zip(trends, weights)) / sum(weights)
        else:
            trend = 0
        
        # 计算移动平均
        window = min(7, len(recent_data))
        avg_value = np.mean(recent_data[-window:])
        
        predictions = []
        dates = []
        current = recent_data[-1]
        
        for i in range(days):
            # 趋势预测
            trend_pred = current + trend
            
            # 均值回归预测
            mean_reversion = avg_value * 0.3 + current * 0.7
            
            # 组合预测（趋势60%，均值回归40%）
            current = trend_pred * 0.6 + mean_reversion * 0.4
            
            # 添加阻尼，避免极端预测
            if abs(trend) > current * 0.1:  # 如果趋势变化超过10%
                current = current * 0.9 + recent_data[-1] * 0.1
            
            current = max(0, current)  # 确保非负
            predictions.append(int(round(current)))
            
            pred_date = start_date + timedelta(days=i + 1)
            dates.append(pred_date.strftime('%Y-%m-%d'))
        
        return dates, predictions

