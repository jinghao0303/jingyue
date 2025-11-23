# LSTM模型数据表说明

## 一、数据表概览

LSTM模型主要使用以下数据表：

### 1. **历史数据表**（已存在）
- **表名**：`flu_daily_cases`
- **用途**：存储每日流感病例数据，用于LSTM模型训练和预测
- **主要字段**：
  - `active` - **核心字段**：当前活跃病例数（用于LSTM训练和预测）
  - `date` - 日期
  - `city_id` - 城市ID
  - `confirmed` - 累计确诊数
  - `recovered` - 累计康复数
  - 其他字段...

### 2. **预测结果表**（已存在）
- **表名**：`flu_seir_predictions`
- **用途**：存储所有算法的预测结果（包括SEIR和LSTM）
- **关键字段**：
  - `algorithm` - 算法类型（'seir' 或 'lstm'）
  - `prediction_data` - JSON格式存储预测的日期和数值
  - `city_id` - 城市ID
  - 其他预测相关字段...

### 3. **LSTM模型训练记录表**（新增）
- **表名**：`flu_lstm_models`
- **用途**：记录LSTM模型的训练历史、参数和性能指标
- **创建SQL**：`backend/database/lstm_model_tables.sql`

## 二、详细字段说明

### 2.1 `flu_daily_cases` 表（LSTM使用的字段）

| 字段名 | 类型 | 说明 | LSTM用途 |
|--------|------|------|----------|
| `active` | INT | 当前活跃病例数 | **核心字段**：用于训练和预测 |
| `date` | DATE | 日期 | 用于时间序列排序 |
| `city_id` | INT | 城市ID | 用于筛选特定城市的数据 |

**注意**：LSTM模型主要使用 `active` 字段（活跃病例数）作为训练和预测的目标值。

### 2.2 `flu_seir_predictions` 表（LSTM使用的字段）

| 字段名 | 类型 | 说明 | LSTM用途 |
|--------|------|------|----------|
| `algorithm` | VARCHAR(20) | 算法类型 | 设置为 'lstm' |
| `prediction_data` | JSON | 预测详细数据 | 存储预测的dates和values数组 |
| `city_id` | INT | 城市ID | 关联城市 |
| `prediction_date` | DATE | 预测起始日期 | 记录预测时间 |
| `days` | INT | 预测天数 | 预测的天数 |
| `peak_infection` | INT | 峰值感染数 | 预测结果摘要 |
| `risk_level` | VARCHAR(10) | 风险等级 | 预测结果摘要 |

### 2.3 `flu_lstm_models` 表（新增表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | BIGINT | 主键ID |
| `city_id` | INT | 城市ID（关联cities表） |
| `model_name` | VARCHAR(200) | 模型文件名 |
| `model_path` | VARCHAR(500) | 模型文件路径 |
| `scaler_path` | VARCHAR(500) | Scaler文件路径 |
| `training_date` | DATE | 训练日期 |
| `epochs` | INT | 训练轮数 |
| `batch_size` | INT | 批次大小 |
| `validation_split` | DECIMAL(3,2) | 验证集比例 |
| `historical_days` | INT | 使用的历史数据天数 |
| `data_points` | INT | 实际使用的数据点数量 |
| `final_loss` | DECIMAL(10,6) | 最终训练损失 |
| `final_val_loss` | DECIMAL(10,6) | 最终验证损失 |
| `final_mae` | DECIMAL(10,2) | 最终平均绝对误差 |
| `final_val_mae` | DECIMAL(10,2) | 最终验证平均绝对误差 |
| `sequence_length` | INT | 输入序列长度（默认14） |
| `model_size` | BIGINT | 模型文件大小（字节） |
| `training_time` | INT | 训练耗时（秒） |
| `is_active` | TINYINT | 是否当前激活模型（1-是，0-否） |
| `status` | TINYINT | 状态（1-有效，0-已删除） |
| `user_id` | BIGINT | 训练模型的用户ID |
| `remark` | TEXT | 备注信息 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

## 三、数据流程

### 3.1 训练流程

```
1. 从 flu_daily_cases 表获取历史数据
   ↓
2. 提取 active 字段，构建时间序列
   ↓
3. 训练LSTM模型
   ↓
4. 保存模型文件到文件系统（backend/models/）
   ↓
5. 保存训练记录到 flu_lstm_models 表
```

### 3.2 预测流程

```
1. 从 flu_daily_cases 表获取最近N天的历史数据
   ↓
2. 提取 active 字段作为输入
   ↓
3. 加载已训练的模型（从文件系统）
   ↓
4. 进行预测
   ↓
5. 保存预测结果到 flu_seir_predictions 表（algorithm='lstm'）
```

## 四、数据库初始化

### 4.1 执行顺序

1. **先执行**：`region_tables.sql`（创建城市表等基础表）
2. **然后执行**：`seir_flu_tables.sql`（创建历史数据表和预测结果表）
3. **最后执行**：`lstm_model_tables.sql`（创建LSTM训练记录表）

### 4.2 SQL文件位置

- `backend/database/region_tables.sql` - 地区表
- `backend/database/seir_flu_tables.sql` - SEIR相关表
- `backend/database/lstm_model_tables.sql` - **LSTM训练记录表（新增）**

## 五、数据要求

### 5.1 训练数据要求

- **最少数据量**：至少30天的历史数据
- **推荐数据量**：60-90天的历史数据
- **数据质量**：数据应该连续，避免大量缺失值
- **核心字段**：`active` 字段必须有值

### 5.2 预测数据要求

- **最少数据量**：至少14天的历史数据（用于构建输入序列）
- **推荐数据量**：30天以上的历史数据
- **数据来源**：从 `flu_daily_cases` 表按日期排序获取

## 六、模型文件存储

### 6.1 文件系统存储

模型文件保存在文件系统中，不在数据库：

- **目录**：`backend/models/`
- **模型文件**：`lstm_model_{城市名}_{日期}.h5`
- **Scaler文件**：`scaler_{城市名}_{日期}.json`

### 6.2 数据库记录

数据库只记录模型的元数据：
- 文件路径
- 训练参数
- 性能指标
- 训练时间等

## 七、总结

### 7.1 使用的现有表

✅ **`flu_daily_cases`** - 历史数据（主要使用 `active` 字段）
✅ **`flu_seir_predictions`** - 预测结果（`algorithm='lstm'`）

### 7.2 新增的表

🆕 **`flu_lstm_models`** - LSTM模型训练记录表

### 7.3 不需要的表

❌ 不需要创建新的历史数据表（使用现有的 `flu_daily_cases`）
❌ 不需要创建新的预测结果表（使用现有的 `flu_seir_predictions`）

## 八、快速开始

1. **执行SQL创建表**：
   ```sql
   source backend/database/lstm_model_tables.sql;
   ```

2. **确保有历史数据**：
   ```sql
   -- 检查是否有足够的历史数据
   SELECT COUNT(*) FROM flu_daily_cases 
   WHERE city_id = (SELECT id FROM cities WHERE city_name = '清远市')
   AND active IS NOT NULL;
   ```

3. **训练模型**（通过API）：
   ```bash
   POST /api/predict/train/lstm
   {
     "city_name": "清远市",
     "epochs": 50
   }
   ```

4. **使用模型预测**：
   ```bash
   POST /api/predict/run
   {
     "algorithm": "lstm",
     "city_name": "清远市",
     "days": 7
   }
   ```

