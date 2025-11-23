/**
 * 训练信息打印工具
 * 用于在前端控制台打印模型训练时的数据字段等信息
 */

export interface TrainingData {
  training_params?: {
    epochs: number;
    batch_size: number;
    validation_split: number;
    historical_days: number;
  };
  city_info?: {
    city_id: number;
    city_name: string;
    total_population: number;
  };
  data_fields?: {
    source_table: string;
    query_date_range: {
      start: string;
      end: string;
    };
    raw_records_count: number;
    field_stats: any;
    date_range: any;
    data_quality: any;
  };
  data_stats?: {
    count: number;
    min: number;
    max: number;
    avg: number;
    median: number;
    first_5: number[];
    last_5: number[];
  };
  model_config?: {
    sequence_length: number;
    input_shape: string;
    model_structure: string;
    optimizer: string;
    loss_function: string;
    metrics: string;
  };
  training_timeline?: {
    start_time: string;
    end_time: string;
    duration_seconds: number;
    duration_formatted: string;
  };
  training_history?: {
    final_loss?: number;
    final_val_loss?: number;
    final_mae?: number;
    final_val_mae?: number;
    all_epochs?: {
      loss: number[];
      val_loss: number[];
      mae: number[];
      val_mae: number[];
    };
  };
  model_files?: {
    model_path?: string;
    model_size_bytes?: number;
    model_size_mb?: number;
    scaler_path?: string;
    scaler_size_bytes?: number;
    scaler_size_kb?: number;
  };
  database_record?: {
    record_id?: number;
    table_name: string;
    old_models_deactivated: number;
  };
}

export function printTrainingInfo(data: TrainingData) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 LSTM模型训练 - 训练参数信息');
  console.log('='.repeat(80));
  
  if (data.training_params) {
    console.log(`城市名称: ${data.city_info?.city_name || '未知'}`);
    console.log(`训练轮数 (epochs): ${data.training_params.epochs}`);
    console.log(`批次大小 (batch_size): ${data.training_params.batch_size}`);
    console.log(`验证集比例 (validation_split): ${data.training_params.validation_split}`);
    console.log(`历史数据天数 (historical_days): ${data.training_params.historical_days}`);
  }
  console.log('-'.repeat(80));
  
  if (data.city_info) {
    console.log('🏙️  城市信息');
    console.log(`城市ID: ${data.city_info.city_id}`);
    console.log(`城市名称: ${data.city_info.city_name}`);
    console.log(`总人口数: ${data.city_info.total_population ? data.city_info.total_population.toLocaleString() : '未设置'}`);
    console.log('-'.repeat(80));
  }
  
  if (data.data_fields) {
    console.log('📋 数据字段使用情况');
    console.log(`数据来源表: ${data.data_fields.source_table}`);
    console.log(`查询日期范围: ${data.data_fields.query_date_range.start} 至 ${data.data_fields.query_date_range.end}`);
    console.log(`查询到的原始记录数: ${data.data_fields.raw_records_count}`);
    
    if (data.data_fields.field_stats) {
      const fs = data.data_fields.field_stats;
      console.log('\n字段统计:');
      if (fs.active) {
        console.log(`  ✅ active (活跃病例数) - 核心字段: ${fs.active.count}/${fs.active.total} 条有值 (${fs.active.percentage.toFixed(1)}%)`);
      }
      if (fs.confirmed) {
        console.log(`  📊 confirmed (累计确诊数): ${fs.confirmed.count}/${fs.confirmed.total} 条有值 (${fs.confirmed.percentage.toFixed(1)}%)`);
      }
      if (fs.recovered) {
        console.log(`  📊 recovered (累计康复数): ${fs.recovered.count}/${fs.recovered.total} 条有值 (${fs.recovered.percentage.toFixed(1)}%)`);
      }
      if (fs.new_cases) {
        console.log(`  📊 new_cases (新增病例数): ${fs.new_cases.count}/${fs.new_cases.total} 条有值 (${fs.new_cases.percentage.toFixed(1)}%)`);
      }
    }
    
    if (data.data_fields.date_range) {
      const dr = data.data_fields.date_range;
      console.log(`\n数据日期范围:`);
      console.log(`  最早日期: ${dr.start}`);
      console.log(`  最新日期: ${dr.end}`);
      console.log(`  日期跨度: ${dr.days} 天`);
    }
    
    if (data.data_fields.data_quality) {
      const dq = data.data_fields.data_quality;
      console.log(`\n数据质量分析:`);
      console.log(`  使用 active 字段: ${dq.active_based} 条`);
      console.log(`  使用 confirmed - recovered 计算: ${dq.calc_based} 条`);
      console.log(`  使用 confirmed 字段: ${dq.confirmed_based} 条`);
      console.log(`  无效数据（跳过）: ${dq.invalid} 条`);
    }
    console.log('-'.repeat(80));
  }
  
  if (data.data_stats) {
    const ds = data.data_stats;
    console.log('📈 训练数据序列信息');
    console.log(`有效数据点数: ${ds.count}`);
    console.log(`数据范围: ${ds.min.toFixed(2)} ~ ${ds.max.toFixed(2)}`);
    console.log(`数据平均值: ${ds.avg.toFixed(2)}`);
    console.log(`数据中位数: ${ds.median.toFixed(2)}`);
    console.log(`\n前5条数据: [${ds.first_5.join(', ')}]`);
    console.log(`后5条数据: [${ds.last_5.join(', ')}]`);
    console.log('-'.repeat(80));
  }
  
  if (data.model_config) {
    const mc = data.model_config;
    console.log('🤖 LSTM模型配置');
    console.log(`序列长度 (sequence_length): ${mc.sequence_length} 天`);
    console.log(`输入形状: ${mc.input_shape}`);
    console.log(`模型结构: ${mc.model_structure}`);
    console.log(`优化器: ${mc.optimizer}`);
    console.log(`损失函数: ${mc.loss_function}`);
    console.log(`评估指标: ${mc.metrics}`);
    console.log('-'.repeat(80));
  }
  
  if (data.training_timeline) {
    const tl = data.training_timeline;
    console.log('🚀 训练时间线');
    console.log(`训练开始时间: ${tl.start_time}`);
    console.log(`训练结束时间: ${tl.end_time}`);
    console.log(`训练耗时: ${tl.duration_seconds} 秒 (${tl.duration_formatted})`);
    console.log('-'.repeat(80));
  }
  
  if (data.training_history) {
    const th = data.training_history;
    console.log('📊 训练指标');
    if (th.final_loss !== undefined && th.final_loss !== null) {
      console.log(`最终训练损失 (loss): ${th.final_loss.toFixed(6)}`);
    }
    if (th.final_val_loss !== undefined && th.final_val_loss !== null) {
      console.log(`最终验证损失 (val_loss): ${th.final_val_loss.toFixed(6)}`);
    }
    if (th.final_mae !== undefined && th.final_mae !== null) {
      console.log(`最终平均绝对误差 (mae): ${th.final_mae.toFixed(2)}`);
    }
    if (th.final_val_mae !== undefined && th.final_val_mae !== null) {
      console.log(`最终验证平均绝对误差 (val_mae): ${th.final_val_mae.toFixed(2)}`);
    }
    
    if (th.all_epochs && th.all_epochs.loss && th.all_epochs.loss.length > 0) {
      const epochs = th.all_epochs.loss.length;
      console.log(`\n训练过程 (共 ${epochs} 轮):`);
      if (epochs <= 10) {
        // 如果轮数少，全部显示
        for (let i = 0; i < epochs; i++) {
          const loss = th.all_epochs.loss[i];
          const valLoss = th.all_epochs.val_loss?.[i];
          if (valLoss !== undefined) {
            console.log(`  Epoch ${i + 1}: loss=${loss.toFixed(6)}, val_loss=${valLoss.toFixed(6)}`);
          } else {
            console.log(`  Epoch ${i + 1}: loss=${loss.toFixed(6)}`);
          }
        }
      } else {
        // 显示前5轮和后5轮
        console.log('  前5轮:');
        for (let i = 0; i < Math.min(5, epochs); i++) {
          const loss = th.all_epochs.loss[i];
          const valLoss = th.all_epochs.val_loss?.[i];
          if (valLoss !== undefined) {
            console.log(`    Epoch ${i + 1}: loss=${loss.toFixed(6)}, val_loss=${valLoss.toFixed(6)}`);
          } else {
            console.log(`    Epoch ${i + 1}: loss=${loss.toFixed(6)}`);
          }
        }
        console.log('  ...');
        console.log('  后5轮:');
        for (let i = Math.max(0, epochs - 5); i < epochs; i++) {
          const loss = th.all_epochs.loss[i];
          const valLoss = th.all_epochs.val_loss?.[i];
          if (valLoss !== undefined) {
            console.log(`    Epoch ${i + 1}: loss=${loss.toFixed(6)}, val_loss=${valLoss.toFixed(6)}`);
          } else {
            console.log(`    Epoch ${i + 1}: loss=${loss.toFixed(6)}`);
          }
        }
      }
    }
    console.log('-'.repeat(80));
  }
  
  if (data.model_files) {
    const mf = data.model_files;
    console.log('💾 模型保存信息');
    if (mf.model_path) {
      console.log(`模型文件路径: ${mf.model_path}`);
      if (mf.model_size_bytes) {
        console.log(`模型文件大小: ${mf.model_size_bytes.toLocaleString()} 字节 (${mf.model_size_mb} MB)`);
      }
    }
    if (mf.scaler_path) {
      console.log(`Scaler文件路径: ${mf.scaler_path}`);
      if (mf.scaler_size_bytes) {
        console.log(`Scaler文件大小: ${mf.scaler_size_bytes.toLocaleString()} 字节 (${mf.scaler_size_kb} KB)`);
      }
    }
    console.log('-'.repeat(80));
  }
  
  if (data.database_record) {
    const dr = data.database_record;
    console.log('💾 数据库保存信息');
    if (dr.old_models_deactivated > 0) {
      console.log(`  已将 ${dr.old_models_deactivated} 个旧模型标记为非激活`);
    }
    if (dr.record_id) {
      console.log(`  ✅ 训练记录已保存到数据库 (记录ID: ${dr.record_id})`);
    }
    console.log(`  数据表: ${dr.table_name}`);
    console.log('-'.repeat(80));
  }
  
  console.log('='.repeat(80));
  console.log('✅ LSTM模型训练流程完成!');
  console.log('='.repeat(80) + '\n');
}

