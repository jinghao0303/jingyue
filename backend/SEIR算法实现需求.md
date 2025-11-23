# SEIR 流感预测算法实现需求文档

## 一、算法概述

**SEIR模型**是经典的传染病动力学模型，用于预测**流行性感冒（流感）**的传播趋势。

### 1.1 模型状态说明

SEIR模型包含四个状态：
- **S (Susceptible)**: 易感者 - 未感染且可能被感染的人群
- **E (Exposed)**: 潜伏者 - 已感染但未发病（无症状或症状不明显）
- **I (Infectious)**: 感染者 - 已发病且具有传染性（有症状）
- **R (Recovered)**: 康复者 - 已康复或死亡，不再具有传染性

### 1.2 流感特性参数

根据医学研究，流感的典型参数：
- **潜伏期**：3-7天（平均5天）
- **传染期**：5-10天（平均7天）
- **基本传染数R0**：1.2-2.0（季节性流感）
- **死亡率**：0.01%-0.1%（相对较低）

## 二、当前实现状态

✅ **已实现**：基础SEIR模型
- 使用差分方程迭代
- 支持R0、预测天数、初始感染数参数

⚠️ **需要改进**：
- 参数硬编码（潜伏期、传染期）
- 缺少历史数据校准
- 缺少防控措施影响
- 缺少更详细的输出（S、E、I、R各状态）

## 三、所需数据清单

### 3.1 必需参数（前端已提供）

| 参数名 | 类型 | 说明 | 默认值 | 来源 |
|--------|------|------|--------|------|
| `r0` | float | 基本传染数 | 1.4 | 前端用户输入 |
| `days` | int | 预测天数 | 14 | 前端用户输入 |
| `algorithm` | string | 算法类型 | 'seir' | 前端选择 |

### 3.2 需要添加的参数（建议前端提供）

| 参数名 | 类型 | 说明 | 默认值 | 建议范围 |
|--------|------|------|--------|----------|
| `total_population` | int | 总人口数 | 5000000 | 根据城市动态获取 |
| `initial_infected` | int | 初始感染数 | 100 | 可选，可从前端输入 |
| `incubation_period` | float | 潜伏期（天） | 5.0 | 3-7天（流感） |
| `infectious_period` | float | 传染期（天） | 7.0 | 5-10天（流感） |
| `initial_exposed` | int | 初始潜伏者数 | null | 可选，默认=initial_infected*2 |
| `initial_recovered` | int | 初始康复者数 | 0 | 可选 |

### 3.3 可选高级参数（未来扩展）

| 参数名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `mortality_rate` | float | 死亡率 | 0.001 |
| `vaccination_rate` | float | 疫苗接种率 | 0.0 |
| `intervention_factor` | float | 防控措施影响因子 | 1.0 |
| `seasonal_factor` | float | 季节性因子 | 1.0 |

### 3.4 数据库表结构

已创建完整的数据库表结构（详见 `database/seir_flu_tables.sql`），包含以下表：

#### 3.4.1 城市人口配置表 (`city_population`)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | INT | 主键ID | 1 |
| `city_name` | VARCHAR(50) | 城市名称 | '清远市' |
| `province` | VARCHAR(50) | 省份名称 | '广东省' |
| `total_population` | INT | 总人口数（用于SEIR模型） | 4000000 |
| `latitude` | DECIMAL(10,6) | 纬度 | 23.7000 |
| `longitude` | DECIMAL(10,6) | 经度 | 113.0500 |
| `status` | TINYINT | 状态：1-启用，0-禁用 | 1 |

#### 3.4.2 流感历史数据表 (`flu_daily_cases`)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | BIGINT | 主键ID | 1 |
| `date` | DATE | 日期 | '2024-01-15' |
| `city_name` | VARCHAR(50) | 城市名称 | '清远市' |
| `confirmed` | INT | 累计确诊数 | 12450 |
| `active` | INT | 当前活跃病例数（正在患病） | 820 |
| `recovered` | INT | 累计康复数 | 11600 |
| `deaths` | INT | 累计死亡数 | 30 |
| `new_cases` | INT | 当日新增病例 | 120 |
| `new_recovered` | INT | 当日新增康复 | 85 |
| `new_deaths` | INT | 当日新增死亡 | 1 |
| `hospitalized` | INT | 当前住院人数 | 150 |
| `severe` | INT | 重症病例数 | 12 |
| `data_source` | VARCHAR(100) | 数据来源 | 'CDC' |
| `remark` | TEXT | 备注信息 | NULL |

**用途**：
- 存储每日流感确诊病例数据
- 用于模型校准和验证
- 用于反推R0值和初始状态

#### 3.4.3 SEIR模型预测结果表 (`flu_seir_predictions`)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | BIGINT | 主键ID | 1 |
| `prediction_date` | DATE | 预测日期（起始日期） | '2024-01-15' |
| `city_name` | VARCHAR(50) | 城市名称 | '清远市' |
| `algorithm` | VARCHAR(20) | 算法类型：seir/lstm/prophet | 'seir' |
| `r0` | DECIMAL(5,2) | 基本传染数 | 1.40 |
| `days` | INT | 预测天数 | 14 |
| `total_population` | INT | 总人口数 | 4000000 |
| `initial_infected` | INT | 初始感染数 | 820 |
| `initial_exposed` | INT | 初始潜伏者数 | 1640 |
| `initial_recovered` | INT | 初始康复者数 | 11600 |
| `incubation_period` | DECIMAL(4,2) | 潜伏期（天） | 5.00 |
| `infectious_period` | DECIMAL(4,2) | 传染期（天） | 7.00 |
| `intervention_factor` | DECIMAL(3,2) | 防控措施影响因子（0-1） | 1.00 |
| `peak_infection` | INT | 预测峰值感染数 | 3500 |
| `peak_date` | DATE | 预测峰值日期 | '2024-01-25' |
| `risk_level` | VARCHAR(10) | 风险等级：低/中/高 | '中' |
| `prediction_data` | JSON | 预测详细数据（dates和values） | {...} |
| `user_id` | BIGINT | 创建预测的用户ID | 1 |

**用途**：
- 存储每次模型预测的结果
- 用于历史查询和对比分析
- 支持多场景对比

#### 3.4.4 流感模型参数配置表 (`flu_model_config`)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | INT | 主键ID | 1 |
| `config_name` | VARCHAR(100) | 配置名称 | '默认配置' |
| `config_type` | VARCHAR(20) | 配置类型：scenario/default | 'default' |
| `r0` | DECIMAL(5,2) | 基本传染数 | 1.40 |
| `incubation_period` | DECIMAL(4,2) | 潜伏期（天） | 5.00 |
| `infectious_period` | DECIMAL(4,2) | 传染期（天） | 7.00 |
| `intervention_factor` | DECIMAL(3,2) | 防控措施影响因子 | 1.00 |
| `vaccination_rate` | DECIMAL(4,3) | 疫苗接种率（0-1） | 0.000 |
| `mortality_rate` | DECIMAL(6,5) | 死亡率 | 0.00010 |
| `description` | TEXT | 配置说明 | '流感默认参数' |
| `is_default` | TINYINT | 是否默认配置 | 1 |

**用途**：
- 存储不同场景下的模型参数配置
- 支持快速切换不同防控措施场景
- 预设常用配置（无防控、轻度防控、严格防控）

#### 3.4.5 预测结果详情表 (`flu_prediction_details`)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | BIGINT | 主键ID | 1 |
| `prediction_id` | BIGINT | 预测记录ID | 1 |
| `predict_date` | DATE | 预测的日期 | '2024-01-16' |
| `day_index` | INT | 预测的第几天 | 1 |
| `susceptible` | INT | 易感者数量（S） | 3997180 |
| `exposed` | INT | 潜伏者数量（E） | 1640 |
| `infected` | INT | 感染者数量（I） | 820 |
| `recovered` | INT | 康复者数量（R） | 11600 |
| `new_cases` | INT | 当日新增病例 | 120 |

**用途**：
- 存储每日预测的详细数据（S、E、I、R各状态）
- 如果预测数据量大，可以单独存储
- 支持详细的数据分析和可视化

## 四、改进后的SEIR模型接口设计

### 4.1 函数签名

```python
def run_seir(
    self,
    r0: float,                    # 基本传染数
    days: int,                    # 预测天数
    total_population: int = 5000000,  # 总人口
    initial_infected: int = 100,      # 初始感染数
    initial_exposed: int = None,      # 初始潜伏者（None则自动计算）
    initial_recovered: int = 0,       # 初始康复者
    incubation_period: float = 5.0,   # 潜伏期（天）
    infectious_period: float = 7.0,   # 传染期（天）
    intervention_factor: float = 1.0,  # 防控措施因子（0-1，1表示无防控）
    return_all_states: bool = False    # 是否返回S、E、I、R全部状态
) -> tuple:
    """
    返回: (dates, infected_values, [可选: all_states_dict])
    """
```

### 4.2 返回数据格式

**当前返回**：
```json
{
  "dates": ["2024-01-16", "2024-01-17", ...],
  "values": [120, 135, 160, ...]  // 仅感染者数量
}
```

**改进后返回**（如果`return_all_states=True`）：
```json
{
  "dates": ["2024-01-16", "2024-01-17", ...],
  "infected": [120, 135, 160, ...],      // I: 感染者
  "exposed": [240, 270, 320, ...],        // E: 潜伏者
  "recovered": [0, 17, 34, ...],         // R: 康复者
  "susceptible": [4999640, 4999578, ...]  // S: 易感者
}
```

## 五、实现步骤

### 阶段1：基础改进（立即实现）
1. ✅ 将硬编码参数改为可配置
2. ✅ 添加总人口参数（可从城市信息获取）
3. ✅ 改进参数验证和错误处理
4. ✅ 添加更详细的日志输出

### 阶段2：数据集成（后续）
1. 连接数据库，读取历史数据
2. 根据历史数据校准初始状态
3. 实现R0自动估算功能

### 阶段3：高级功能（未来）
1. 添加防控措施影响
2. 添加疫苗接种影响
3. 添加季节性因子
4. 实现多场景对比

## 六、前端需要配合的改动

### 6.1 参数输入界面（可选增强）

可以在前端添加更多参数输入：
```vue
<el-form-item label="总人口数">
  <el-input-number v-model="modelParams.total_population" :min="10000" :max="50000000" />
</el-form-item>

<el-form-item label="初始感染数">
  <el-input-number v-model="modelParams.initial_infected" :min="1" :max="10000" />
</el-form-item>

<el-form-item label="潜伏期（天）">
  <el-input-number v-model="modelParams.incubation_period" :min="1" :max="14" :step="0.5" />
</el-form-item>

<el-form-item label="传染期（天）">
  <el-input-number v-model="modelParams.infectious_period" :min="3" :max="21" :step="0.5" />
</el-form-item>
```

### 6.2 API调用参数

前端调用时需要传递：
```typescript
const params = {
  algorithm: 'seir',
  r0: 1.4,
  days: 14,
  // 新增参数（可选）
  total_population: 5000000,
  initial_infected: 100,
  incubation_period: 5.0,
  infectious_period: 7.0
};
```

## 七、数据来源和获取方式

### 7.1 总人口数
- **数据来源**：`city_population` 表
- **获取方式**：根据用户定位的城市名称，从数据库查询
- **默认值**：如果城市不存在，使用500万
- **实现**：后端根据 `city_name` 查询 `total_population` 字段

### 7.2 初始感染数
- **数据来源**：`flu_daily_cases` 表
- **获取方式**：查询指定城市的最新日期记录，使用 `active` 字段
- **默认值**：如果无历史数据，使用100
- **实现**：
  ```sql
  SELECT active FROM flu_daily_cases 
  WHERE city_name = ? 
  ORDER BY date DESC LIMIT 1
  ```

### 7.3 初始潜伏者数
- **计算方式**：通常为初始感染数的 1.5-2 倍
- **默认计算**：`initial_exposed = initial_infected * 2`
- **可选**：从历史数据中估算

### 7.4 初始康复者数
- **数据来源**：`flu_daily_cases` 表
- **获取方式**：查询最新日期的 `recovered` 字段
- **默认值**：0

### 7.5 潜伏期/传染期
- **数据来源**：`flu_model_config` 表（默认配置）
- **默认值**：
  - 潜伏期：5.0 天（流感典型值）
  - 传染期：7.0 天（流感典型值）
- **可调整**：前端可以传递自定义值，或从配置表读取场景配置

### 7.6 R0值
- **数据来源**：前端用户输入
- **默认值**：1.4（季节性流感的典型值）
- **参考范围**：
  - 无防控措施：1.8-2.2
  - 轻度防控：1.2-1.5
  - 严格防控：0.8-1.2

## 八、测试数据示例

```python
# 测试用例1：基础预测
r0 = 1.4
days = 14
total_population = 5000000
initial_infected = 100

# 测试用例2：高传染性
r0 = 3.0
days = 30
total_population = 10000000
initial_infected = 500

# 测试用例3：低传染性
r0 = 0.8
days = 14
total_population = 1000000
initial_infected = 50
```

## 九、数据库使用说明

### 9.1 初始化数据库

执行SQL文件创建所有表：
```bash
mysql -u root -p Infectious_disease_data < database/seir_flu_tables.sql
```

### 9.2 数据导入

#### 导入城市配置
表 `city_population` 已包含默认城市数据，如需添加新城市：
```sql
INSERT INTO city_population (city_name, province, total_population, latitude, longitude)
VALUES ('新城市', '省份', 人口数, 纬度, 经度);
```

#### 导入历史数据
如果有历史流感数据，导入到 `flu_daily_cases` 表：
```sql
INSERT INTO flu_daily_cases (date, city_name, confirmed, active, recovered, deaths, new_cases)
VALUES ('2024-01-15', '清远市', 12450, 820, 11600, 30, 120);
```

### 9.3 查询示例

#### 获取城市人口
```sql
SELECT total_population FROM city_population WHERE city_name = '清远市';
```

#### 获取最新病例数据
```sql
SELECT * FROM flu_daily_cases 
WHERE city_name = '清远市' 
ORDER BY date DESC LIMIT 1;
```

#### 获取预测历史
```sql
SELECT * FROM flu_seir_predictions 
WHERE city_name = '清远市' 
ORDER BY created_at DESC LIMIT 10;
```

## 十、下一步行动

1. ✅ **数据库表结构**：已完成，执行SQL文件即可
2. 🔄 **改进SEIR模型**：添加数据库查询功能，支持从数据库读取参数
3. 🔄 **后端API改进**：支持从数据库读取城市人口和历史数据
4. 🔄 **测试验证**：使用数据库数据进行模型测试

---

## 十一、注意事项

1. **流感特性**：本系统专门用于流感预测，参数设置基于流感的医学特性
2. **数据准确性**：历史数据的准确性直接影响模型预测效果
3. **定期更新**：建议每日更新 `flu_daily_cases` 表的数据
4. **数据备份**：预测结果表会不断增长，建议定期备份和归档

