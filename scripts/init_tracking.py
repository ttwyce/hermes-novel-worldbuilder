#!/usr/bin/env python3
"""
init_tracking.py — 初始化小说追踪数据库（通用）

用法：
  python3 init_tracking.py <书名> [--主角 主角名]

示例：
  python3 init_tracking.py "我的新小说"
  python3 init_tracking.py "我的新小说" --主角 "张三"

功能：
  - 初始化数据库（5张表）
  - 自动添加主角角色（ID: A01）
  - 打印数据库路径

新小说使用流程：
  1. python3 init_tracking.py "书名"
  2. 在大纲/角色弧光追踪.md 手动添加角色信息（或通过其他方式）
  3. 写章节时 python3 post_chapter.py "书名" 1 3000 "事件"
  4. 检查上下文 python3 get_context.py "书名" 2
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db
import json

def init_tracking(book_name: str, protagonist: str = None,
                  planned_chapters: int = 150,
                  chapter_word_count: int = 3000) -> str:
    """初始化追踪数据库，返回路径"""
    db_path = tracking_db.get_db_path(book_name)
    
    # 初始化数据库（创建表）
    tracking_db.init_db(db_path)
    
    # 添加默认主角（如果没有提供书名就叫"主角"）
    if protagonist is None:
        protagonist = "主角"
    
    protagonist_arc = {
        'id': 'A01',
        'name': protagonist,
        'arc_type': '觉醒型',
        'start_state': '起点状态',
        'current_state': '起点状态',
        'current_chapter': 0,
        'key_moments': []
    }
    
    tracking_db.init_character_arcs(db_path, [protagonist_arc])
    
    # 存储计划元数据
    tracking_db.set_meta(db_path, 'planned_chapters', str(planned_chapters))
    tracking_db.set_meta(db_path, 'chapter_word_count', str(chapter_word_count))
    
    return db_path

def add_character(db_path: str, char_id: str, name: str, arc_type: str, 
                  start_state: str, current_state: str = None) -> None:
    """添加角色"""
    if current_state is None:
        current_state = start_state
    
    arc = {
        'id': char_id,
        'name': name,
        'arc_type': arc_type,
        'start_state': start_state,
        'current_state': current_state,
        'current_chapter': 0,
        'key_moments': []
    }
    
    tracking_db.init_character_arcs(db_path, [arc])

def add_plot(db_path: str, chapter_id: int, plot: str) -> int:
    """添加伏笔"""
    return tracking_db.add_plot_hook(db_path, chapter_id, plot)

def main():
    parser = argparse.ArgumentParser(description='初始化小说追踪数据库')
    parser.add_argument('book_name', help='小说名称')
    parser.add_argument('--主角', dest='protagonist', help='主角名称（默认：主角）')
    
    args = parser.parse_args()
    
    try:
        db_path = init_tracking(args.book_name, args.protagonist)
        
        print(f"""
✅ 追踪数据库初始化完成！

书名：{args.book_name}
路径：{db_path}

已添加：
  - 主角：A01 {args.protagonist or '主角'}
  - 5张表：chapters / character_arcs / chronicle / plot_hooks / world_state

下一步：
  1. 在大纲/角色弧光追踪.md 添加其他角色
  2. 或使用 add_character() 函数添加
  3. 使用 get_context.py 获取章节上下文
        """)
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("提示：确保小说目录存在于 ~/novels/")
        sys.exit(2)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()