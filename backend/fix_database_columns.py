#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速修复：为 flu_model_config 表添加缺失字段
直接运行：python fix_database_columns.py
"""
import pymysql

# 数据库配置（从 config.py 复制）
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '629629',
    'database': 'Infectious_disease_data',
    'charset': 'utf8mb4'
}

def fix_database_columns():
    """添加缺失的字段"""
    try:
        print("=" * 60)
        print("修复数据库表：添加缺失字段")
        print("=" * 60)
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ 数据库连接成功\n")
        
        # 检查并添加 days 字段
        print("1. 检查 days 字段...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'flu_model_config'
            AND COLUMN_NAME = 'days'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            print("   → 添加 days 字段...")
            cursor.execute("""
                ALTER TABLE `flu_model_config` 
                ADD COLUMN `days` INT DEFAULT 3 COMMENT '预测天数，默认3天' 
                AFTER `intervention_factor`
            """)
            print("   ✓ days 字段添加成功")
        else:
            print("   ✓ days 字段已存在")
        
        # 检查并添加 default_algorithm 字段
        print("\n2. 检查 default_algorithm 字段...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'flu_model_config'
            AND COLUMN_NAME = 'default_algorithm'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            print("   → 添加 default_algorithm 字段...")
            cursor.execute("""
                ALTER TABLE `flu_model_config` 
                ADD COLUMN `default_algorithm` VARCHAR(20) DEFAULT 'seir' 
                COMMENT '默认预测算法：seir/lstm/prophet' 
                AFTER `intervention_factor`
            """)
            print("   ✓ default_algorithm 字段添加成功")
        else:
            print("   ✓ default_algorithm 字段已存在")
        
        # 更新现有默认配置
        print("\n3. 更新默认配置...")
        cursor.execute("""
            UPDATE `flu_model_config` 
            SET `days` = 3, `default_algorithm` = 'seir'
            WHERE `is_default` = 1 AND (`days` IS NULL OR `days` = 0 OR `default_algorithm` IS NULL)
        """)
        affected = cursor.rowcount
        if affected > 0:
            print(f"   ✓ 已更新 {affected} 条默认配置记录")
        else:
            print("   ✓ 默认配置已是最新")
        
        # 提交更改
        conn.commit()
        
        # 验证
        print("\n4. 验证当前默认配置:")
        cursor.execute("""
            SELECT id, config_name, days, default_algorithm, is_default
            FROM flu_model_config
            WHERE is_default = 1
        """)
        results = cursor.fetchall()
        if results:
            for row in results:
                print(f"   ID: {row[0]}, 名称: {row[1]}, 预测天数: {row[2]}, 算法: {row[3]}, 是否默认: {row[4]}")
        else:
            print("   ⚠ 警告：未找到默认配置")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ 修复完成！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("✗ 修复失败！")
        print("=" * 60)
        return False

if __name__ == '__main__':
    fix_database_columns()

