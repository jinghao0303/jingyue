#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 flu_model_config 表添加缺失的字段
- days: 预测天数
- default_algorithm: 默认预测算法
"""
import pymysql
import sys
import os

# 添加父目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def add_missing_columns():
    """添加缺失的字段到 flu_model_config 表"""
    try:
        # 解析数据库连接字符串
        # 格式: mysql+pymysql://user:password@host:port/database
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        if db_uri.startswith('mysql+pymysql://'):
            db_uri = db_uri.replace('mysql+pymysql://', '')
        
        parts = db_uri.split('@')
        if len(parts) != 2:
            print("错误：无法解析数据库连接字符串")
            return False
        
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        if len(user_pass) != 2 or len(host_db) != 2:
            print("错误：无法解析数据库连接字符串")
            return False
        
        user = user_pass[0]
        password = user_pass[1]
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        database = host_db[1]
        
        print(f"连接数据库: {host}:{port}/{database}")
        
        # 连接数据库
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print("✓ 数据库连接成功")
        
        # 检查并添加 days 字段
        print("\n检查 days 字段...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'flu_model_config'
            AND COLUMN_NAME = 'days'
        """, (database,))
        
        if cursor.fetchone()[0] == 0:
            print("  添加 days 字段...")
            cursor.execute("""
                ALTER TABLE `flu_model_config` 
                ADD COLUMN `days` INT DEFAULT 3 COMMENT '预测天数，默认3天' 
                AFTER `intervention_factor`
            """)
            print("  ✓ days 字段添加成功")
            
            # 更新现有默认配置的预测天数
            cursor.execute("""
                UPDATE `flu_model_config` 
                SET `days` = 3 
                WHERE `is_default` = 1 AND (`days` IS NULL OR `days` = 0)
            """)
            print("  ✓ 已更新默认配置的预测天数为 3")
        else:
            print("  ✓ days 字段已存在")
        
        # 检查并添加 default_algorithm 字段
        print("\n检查 default_algorithm 字段...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'flu_model_config'
            AND COLUMN_NAME = 'default_algorithm'
        """, (database,))
        
        if cursor.fetchone()[0] == 0:
            print("  添加 default_algorithm 字段...")
            cursor.execute("""
                ALTER TABLE `flu_model_config` 
                ADD COLUMN `default_algorithm` VARCHAR(20) DEFAULT 'seir' 
                COMMENT '默认预测算法：seir/lstm/prophet' 
                AFTER `intervention_factor`
            """)
            print("  ✓ default_algorithm 字段添加成功")
            
            # 更新现有默认配置的算法
            cursor.execute("""
                UPDATE `flu_model_config` 
                SET `default_algorithm` = 'seir' 
                WHERE `is_default` = 1
            """)
            print("  ✓ 已更新默认配置的算法为 seir")
        else:
            print("  ✓ default_algorithm 字段已存在")
        
        # 提交更改
        conn.commit()
        print("\n✓ 所有字段检查完成！")
        
        # 验证
        print("\n验证当前默认配置:")
        cursor.execute("""
            SELECT id, config_name, days, default_algorithm, is_default
            FROM flu_model_config
            WHERE is_default = 1
        """)
        results = cursor.fetchall()
        for row in results:
            print(f"  ID: {row[0]}, 名称: {row[1]}, 预测天数: {row[2]}, 算法: {row[3]}, 是否默认: {row[4]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("为 flu_model_config 表添加缺失字段")
    print("=" * 50)
    
    if add_missing_columns():
        print("\n" + "=" * 50)
        print("✓ 完成！")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ 失败！")
        print("=" * 50)
        exit(1)

