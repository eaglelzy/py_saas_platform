#!/usr/bin/env python3
"""
测试数据库清理脚本

用于清理测试过程中生成的数据库文件。
"""

import os
import sys
import argparse
from pathlib import Path


def cleanup_test_databases(verbose: bool = False):
    """
    清理测试数据库文件
    
    Args:
        verbose: 是否显示详细信息
    """
    # 获取测试数据库目录
    test_db_dir = Path(__file__).parent
    
    if not test_db_dir.exists():
        if verbose:
            print(f"测试数据库目录不存在: {test_db_dir}")
        return
    
    # 查找所有数据库文件
    db_files = list(test_db_dir.glob("*.db"))
    
    if not db_files:
        if verbose:
            print("没有找到测试数据库文件")
        return
    
    # 删除数据库文件
    deleted_count = 0
    for db_file in db_files:
        try:
            db_file.unlink()
            deleted_count += 1
            if verbose:
                print(f"已删除: {db_file.name}")
        except Exception as e:
            if verbose:
                print(f"删除失败 {db_file.name}: {e}")
    
    if verbose:
        print(f"总共删除了 {deleted_count} 个数据库文件")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="清理测试数据库文件")
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="显示详细信息"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="只显示将要删除的文件，不实际删除"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        # 只显示将要删除的文件
        test_db_dir = Path(__file__).parent
        db_files = list(test_db_dir.glob("*.db"))
        
        if db_files:
            print("将要删除的数据库文件:")
            for db_file in db_files:
                print(f"  - {db_file.name}")
        else:
            print("没有找到数据库文件")
    else:
        # 实际清理
        cleanup_test_databases(verbose=args.verbose)


if __name__ == "__main__":
    main()
