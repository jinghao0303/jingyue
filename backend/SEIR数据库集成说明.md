# SEIR模型数据库集成说明

## 一、数据库初始化

### 1.1 执行顺序

**重要**：请按以下顺序执行SQL文件：

```bash
# 1. 先创建地区表结构（省-市-区县）
mysql -u root -p Infectious_disease_data < database/region_tables.sql

# 2. 再创建流感数据表结构
mysql -u root -p Infectious_disease_data < database/seir_flu_tables.sql
```

### 1.2 验证表结构

执行以下SQL验证表是否创建成功：

```sql
USE Infectious_disease_data;

-- 查看所有表
SHOW TABLES;

-- 应该看到以下表：
-- provinces, cities, districts, city_population
-- flu_daily_cases, flu_model_config, flu_seir_predictions, flu_prediction_details
```

## 二、数据模型说明

### 2.1 地区表结构（多表关联）

```
provinces (省份表)
  └── cities (城市表) - 通过 province_id 关联
        ├── districts (区县表) - 通过 city_id 关联
        ├── city_population (人口配置表) - 通过 city_id 关联
        ├── flu_daily_cases (历史数据表) - 通过 city_id 关联
        └── flu_seir_predictions (预测结果表) - 通过 city_id 关联
```

### 2.2 多表查询示例

```sql
-- 查询城市及其省份、人口信息
SELECT 
    c.city_name,
    p.province_name,
    cp.total_population
FROM cities c
JOIN provinces p ON c.province_id = p.id
LEFT JOIN city_population cp ON c.id = cp.city_id
WHERE c.city_name = '清远市';

-- 查询城市的最新病例数据
SELECT 
    c.city_name,
    p.province_name,
    fdc.date,
    fdc.active,
    fdc.recovered
FROM flu_daily_cases fdc
JOIN cities c ON fdc.city_id = c.id
JOIN provinces p ON c.province_id = p.id
WHERE c.city_name = '清远市'
ORDER BY fdc.date DESC
LIMIT 1;
```

## 三、API使用说明

### 3.1 预测接口调用

**接口**：`POST /api/predict/run`

**请求头**：
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**：

#### 基础参数（必需）
```json
{
  "algorithm": "seir",
  "r0": 1.4,
  "days": 14
}
```

#### 完整参数（可选，会自动从数据库获取）
```json
{
  "algorithm": "seir",
  "r0": 1.4,
  "days": 14,
  "city_name": "清远市",           // 提供城市名称，自动获取人口和历史数据
  "total_population": 4000000,    // 可选，覆盖数据库值
  "initial_infected": 100,         // 可选，覆盖数据库值
  "initial_exposed": 200,          // 可选，自动计算
  "initial_recovered": 0,          // 可选，从数据库获取
  "incubation_period": 5.0,        // 可选，从配置表获取
  "infectious_period": 7.0,        // 可选，从配置表获取
  "intervention_factor": 1.0     // 可选，从配置表获取
}
```

### 3.2 自动数据获取逻辑

1. **如果提供 `city_name`**：
   - 自动从 `cities` 表查询城市信息
   - 自动从 `city_population` 表获取总人口数
   - 自动从 `flu_daily_cases` 表获取最新病例数据作为初始状态
   - 自动从 `flu_model_config` 表获取默认模型参数

2. **如果未提供 `city_name`**：
   - 使用默认值（总人口500万，初始感染100）

3. **前端参数优先级**：
   - 前端提供的参数会覆盖数据库查询的值

### 3.3 响应格式

```json
{
  "code": 200,
  "msg": "预测成功",
  "data": {
    "dates": ["2024-01-16", "2024-01-17", ...],
    "values": [120, 135, 160, ...],
    "all_states": {
      "susceptible": [4997180, 4997045, ...],
      "exposed": [200, 215, ...],
      "infected": [120, 135, ...],
      "recovered": [0, 17, ...]
    },
    "meta": {
      "algorithm": "seir",
      "max_cases": 3500,
      "peak_date": "2024-01-25",
      "risk_level": "中",
      "total_population": 4000000,
      "initial_infected": 100,
      "r0": 1.4,
      "incubation_period": 5.0,
      "infectious_period": 7.0,
      "prediction_id": 123  // 如果保存成功
    }
  }
}
```

## 四、数据库服务使用

### 4.1 城市服务

```python
from app.utils.db_service import CityService

# 获取城市信息（包含省份、人口）
city_info = CityService.get_city_info('清远市')
# 返回：{'id': 1, 'city_name': '清远市', 'province_name': '广东省', 'total_population': 4000000, ...}

# 获取城市人口
population = CityService.get_city_population(city_name='清远市')
# 返回：4000000
```

### 4.2 流感数据服务

```python
from app.utils.db_service import FluDataService

# 获取最新病例数据
latest = FluDataService.get_latest_cases(city_name='清远市')
# 返回：FluDailyCase对象

# 获取初始状态（用于SEIR模型）
initial_state = FluDataService.get_initial_state(city_name='清远市')
# 返回：{'initial_infected': 820, 'initial_exposed': 1640, 'initial_recovered': 11600}
```

### 4.3 模型配置服务

```python
from app.utils.db_service import ModelConfigService

# 获取默认配置
config = ModelConfigService.get_default_config()
# 返回：FluModelConfig对象，包含r0、潜伏期、传染期等参数
```

### 4.4 预测结果服务

```python
from app.utils.db_service import PredictionService

# 保存预测结果
prediction_data = {
    'prediction_date': date.today(),
    'city_id': 1,
    'algorithm': 'seir',
    'r0': 1.4,
    # ... 其他参数
}
prediction = PredictionService.save_prediction(prediction_data)

# 查询历史预测
predictions = PredictionService.get_predictions_by_city('清远市', limit=10)
```

## 五、数据导入

### 5.1 导入历史病例数据

```sql
-- 示例：导入清远市的病例数据
INSERT INTO flu_daily_cases (
    date, city_id, confirmed, active, recovered, deaths, new_cases, new_recovered
)
SELECT 
    '2024-01-15', 
    c.id, 
    12450, 820, 11600, 30, 120, 85
FROM cities c 
WHERE c.city_name = '清远市'
ON DUPLICATE KEY UPDATE
    confirmed = VALUES(confirmed),
    active = VALUES(active),
    recovered = VALUES(recovered);
```

### 5.2 添加新城市

```sql
-- 1. 确保省份存在
INSERT INTO provinces (province_code, province_name) 
VALUES ('44', '广东省')
ON DUPLICATE KEY UPDATE province_name = VALUES(province_name);

-- 2. 添加城市
INSERT INTO cities (city_code, city_name, province_id, latitude, longitude)
SELECT '4419', '新城市', p.id, 23.5, 113.0
FROM provinces p
WHERE p.province_code = '44';

-- 3. 添加人口配置
INSERT INTO city_population (city_id, total_population, population_year)
SELECT c.id, 3000000, 2023
FROM cities c
WHERE c.city_name = '新城市';
```

## 六、常见问题

### Q1: 如果城市不存在怎么办？
A: 系统会使用默认值（总人口500万，初始感染100），预测仍然可以运行。

### Q2: 如果没有历史数据怎么办？
A: 系统会使用默认初始状态（感染100，潜伏200，康复0）。

### Q3: 如何查看预测历史？
A: 查询 `flu_seir_predictions` 表，或使用 `PredictionService.get_predictions_by_city()`。

### Q4: 预测结果会自动保存吗？
A: 是的，如果提供了 `city_name` 且城市存在于数据库中，预测结果会自动保存。

### Q5: 如何修改模型默认参数？
A: 更新 `flu_model_config` 表中 `is_default=1` 的记录。

## 七、性能优化建议

1. **索引**：所有表已创建必要的索引，支持快速查询
2. **缓存**：可以考虑对城市信息和配置进行缓存
3. **批量查询**：如果需要查询多个城市，使用 `IN` 查询而不是循环

## 八、下一步扩展

1. **添加区县级别预测**：使用 `districts` 表支持更细粒度的预测
2. **历史数据对比**：对比预测结果和实际数据，评估模型准确性
3. **多场景对比**：支持同时运行多个场景（不同R0值）并保存对比结果

