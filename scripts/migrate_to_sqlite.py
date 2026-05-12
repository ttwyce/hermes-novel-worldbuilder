#!/usr/bin/env python3
"""
migrate_to_sqlite.py — 将现有 MD 追踪文件迁移到 SQLite

用法：
  python3 migrate_to_sqlite.py <书名>

示例：
  python3 migrate_to_sqlite.py "时光缓缓"
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# ============================================================
# 以下为示例数据占位符 — 迁移时请替换为实际小说数据
# ============================================================

# 角色弧光初始数据（示例占位符）
INIT_ARCS = [
    {
        'id': 'A01', 'name': '主角', 'arc_type': '觉醒型',
        'start_state': '起点状态描述',
        'current_state': '当前状态描述',
        'current_chapter': 1,
        'key_moments': [
            {'chapter': 1, 'event': '关键转折点1'},
            {'chapter': 5, 'event': '关键转折点2'},
        ]
    },
    {
        'id': 'A02', 'name': '女主1', 'arc_type': '深化型',
        'start_state': '起点状态描述',
        'current_state': '当前状态描述',
        'current_chapter': 1,
        'key_moments': [
            {'chapter': 1, 'event': '首次登场'},
        ]
    },
]

# 已知的章节数据（示例占位符）
EXISTING_CHAPTERS = [
    (1, 3000, "第1章核心事件"),
    (2, 3200, "第2章核心事件"),
    (3, 2800, "第3章核心事件"),
]

# 已知编年史（示例占位符）
EXISTING_CHRONICLE = [
    (1, "时间点A", "事件描述A"),
    (2, "时间点B", "事件描述B"),
    (3, "时间点C", "事件描述C"),
]

# ============================================================


def migrate(book_name: str) -> None:
    """执行迁移"""
    print(f"\n🔄 迁移追踪数据到 SQLite")
    print(f"  书名: {book_name}")
    
    # 初始化数据库
    db_path = tracking_db.get_db_path(book_name)
    tracking_db.init_db(db_path)
    print(f"  数据库: {db_path}")
    
    # 1. 导入章节
    print("\n📚 导入章节数据...")
    for ch_id, words, core_event in EXISTING_CHAPTERS:
        tracking_db.insert_or_update_chapter(
            db_path, ch_id,
            title=f"第{ch_id}章",
            words=words,
            status="done",
            core_event=core_event
        )
        print(f"  ✅ 第{ch_id}章: {words}字")
    
    # 2. 导入角色弧光
    print("\n👥 导入角色弧光...")
    tracking_db.init_character_arcs(db_path, INIT_ARCS)
    for arc in INIT_ARCS:
        print(f"  ✅ {arc['id']} {arc['name']}")
    
    # 3. 导入编年史
    print("\n📅 导入编年史...")
    for ch_id, time_label, event in EXISTING_CHRONICLE:
        tracking_db.append_chronicle(db_path, ch_id, time_label, event)
    print(f"  ✅ {len(EXISTING_CHRONICLE)} 条记录")
    
    # 4. 导出全部 MD 文件
    print("\n📤 导出 Markdown 文件...")
    import export_md
    export_md.export_all(book_name)
    
    # 5. 验证
    print("\n=== 验证数据库 ===")
    chapters = tracking_db.get_all_chapters(db_path)
    completed = [c for c in chapters if c['status'] == 'done']
    print(f"  章节: {len(completed)}/?? 完成")
    print(f"  总字数: {sum(c['words'] for c in completed)}")
    
    arcs = tracking_db.get_all_character_arcs(db_path)
    print(f"  角色弧光: {len(arcs)} 个")
    
    chronicle = tracking_db.get_chronicle(db_path)
    print(f"  编年史: {len(chronicle)} 条")
    
    print("\n🎉 迁移完成！")
    print(f"\n数据库路径: {db_path}")
    print("MD 文件已同步到 大纲/ 目录")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 migrate_to_sqlite.py <书名>")
        sys.exit(1)
    
    book_name = sys.argv[1]
    migrate(book_name)