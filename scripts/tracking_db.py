#!/usr/bin/env python3
"""
tracking_db.py — SQLite 数据库操作模块

功能：
- 初始化数据库
- 章节 CRUD
- 角色弧光 CRUD
- 编年史 CRUD
- 导出到 Markdown
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# 默认数据库路径（相对于小说根目录）
DB_NAME = ".tracking/tracking.db"

# 角色映射
CHARACTER_IDS = {
    '陆天': 'A01', '叶琳': 'A02', '苏清雪': 'A03',
    '陈朵朵': 'A04', '赵婉清': 'A05',
    '李明辉': 'B01', '陈浩': 'C01', '周天成': 'B02',
}
CHARACTER_NAMES = {v: k for k, v in CHARACTER_IDS.items()}

# ==================== 数据库初始化 ====================

def get_connection(db_path: str) -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str) -> None:
    """初始化数据库"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 章节表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id              INTEGER PRIMARY KEY,
            title           TEXT,
            words           INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'pending',
            core_event      TEXT,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 角色弧光表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_arcs (
            id              TEXT PRIMARY KEY,
            name            TEXT,
            arc_type        TEXT,
            start_state     TEXT,
            current_state   TEXT,
            current_chapter INTEGER DEFAULT 0,
            key_moments     TEXT DEFAULT '[]'
        )
    """)
    
    # 编年史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chronicle (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id      INTEGER,
            time_label      TEXT,
            event           TEXT,
            chapter         INTEGER
        )
    """)
    
    # 世界状态表（当前主角境界/处境等）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_state (
            key             TEXT PRIMARY KEY,
            value           TEXT
        )
    """)
    
    # 元数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key             TEXT PRIMARY KEY,
            value           TEXT
        )
    """)

    # 伏笔钩子表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plot_hooks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id      INTEGER,
            plot            TEXT,
            status          TEXT DEFAULT 'active',
            resolved_chapter INTEGER,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {db_path}")

# ==================== 章节操作 ====================

def insert_or_update_chapter(db_path: str, chapter_id: int, title: str = None,
                             words: int = 0, status: str = "done",
                             core_event: str = "") -> None:
    """插入或更新章节"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO chapters (id, title, words, status, core_event, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            title       = COALESCE(excluded.title, title),
            words       = excluded.words,
            status      = excluded.status,
            core_event  = excluded.core_event,
            updated_at  = CURRENT_TIMESTAMP
    """, (chapter_id, title, words, status, core_event))
    
    conn.commit()
    conn.close()

def get_chapter(db_path: str, chapter_id: int) -> Optional[Dict]:
    """获取单个章节"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_chapters(db_path: str) -> List[Dict]:
    """获取所有章节（按 id 排序）"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chapters ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_completed_chapters(db_path: str) -> List[Dict]:
    """获取已完成章节"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chapters WHERE status='done' ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==================== 角色弧光操作 ====================

def init_character_arcs(db_path: str, arcs: List[Dict]) -> None:
    """初始化角色弧光列表"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    for arc in arcs:
        key_moments = json.dumps(arc.get('key_moments', []), ensure_ascii=False)
        cursor.execute("""
            INSERT OR IGNORE INTO character_arcs
            (id, name, arc_type, start_state, current_state, current_chapter, key_moments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (arc['id'], arc['name'], arc['arc_type'], arc['start_state'],
              arc.get('current_state', arc['start_state']),
              arc.get('current_chapter', 0), key_moments))
    conn.commit()
    conn.close()

def update_character_arc(db_path: str, char_id: str, chapter_id: int,
                         new_state: str = None, moment: str = None) -> None:
    """更新角色弧光"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 获取当前 key_moments
    cursor.execute("SELECT key_moments FROM character_arcs WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    
    moments = json.loads(row['key_moments'] or "[]")
    
    # 添加新转折点
    if moment:
        moments.append({"chapter": chapter_id, "event": moment})
    
    # 更新状态
    if new_state:
        cursor.execute("""
            UPDATE character_arcs
            SET current_state = ?, current_chapter = ?, key_moments = ?
            WHERE id = ?
        """, (new_state, chapter_id, json.dumps(moments, ensure_ascii=False), char_id))
    else:
        cursor.execute("""
            UPDATE character_arcs
            SET current_chapter = ?, key_moments = ?
            WHERE id = ?
        """, (chapter_id, json.dumps(moments, ensure_ascii=False), char_id))
    
    conn.commit()
    conn.close()

def touch_character(db_path: str, char_id: str, chapter_id: int) -> None:
    """更新角色的最新互动章节（不添加转折点）"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE character_arcs
        SET current_chapter = ?
        WHERE id = ? AND current_chapter < ?
    """, (chapter_id, char_id, chapter_id))
    conn.commit()
    conn.close()

def get_all_character_arcs(db_path: str) -> List[Dict]:
    """获取所有角色弧光"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM character_arcs ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['key_moments'] = json.loads(d['key_moments'] or "[]")
        result.append(d)
    return result

def get_character_arc(db_path: str, char_id: str) -> Optional[Dict]:
    """获取单个角色弧光"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM character_arcs WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['key_moments'] = json.loads(d['key_moments'] or "[]")
        return d
    return None

# ==================== 伏笔钩子操作 ====================

def add_plot_hook(db_path: str, chapter_id: int, plot: str) -> int:
    """添加伏笔钩子，返回自增ID"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plot_hooks (chapter_id, plot, status)
        VALUES (?, ?, 'active')
    """, (chapter_id, plot))
    hook_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return hook_id

def get_active_plots(db_path: str) -> List[Dict]:
    """获取所有活跃伏笔"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM plot_hooks
        WHERE status = 'active'
        ORDER BY chapter_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def resolve_plot_hook(db_path: str, hook_id: int, resolved_chapter: int) -> None:
    """标记伏笔已解开"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE plot_hooks
        SET status = 'resolved', resolved_chapter = ?
        WHERE id = ?
    """, (resolved_chapter, hook_id))
    conn.commit()
    conn.close()

def get_plot_by_id(db_path: str, hook_id: int) -> Optional[Dict]:
    """根据ID获取伏笔"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plot_hooks WHERE id = ?", (hook_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ==================== 编年史操作 ====================

def append_chronicle(db_path: str, chapter_id: int, time_label: str,
                     event: str) -> None:
    """追加编年史条目（如果不存在）"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 检查是否已存在
    cursor.execute("""
        SELECT 1 FROM chronicle 
        WHERE chapter_id=? AND time_label=? AND event=?
    """, (chapter_id, time_label, event))
    if cursor.fetchone():
        conn.close()
        return  # 已存在，跳过
    
    cursor.execute("""
        INSERT INTO chronicle (chapter_id, time_label, event, chapter)
        VALUES (?, ?, ?, ?)
    """, (chapter_id, time_label, event, chapter_id))
    conn.commit()
    conn.close()

def get_chronicle(db_path: str) -> List[Dict]:
    """获取全部编年史"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chronicle ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==================== 世界状态操作 ====================

def set_world_state(db_path: str, key: str, value: str) -> None:
    """设置世界状态"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO world_state (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_world_state(db_path: str, key: str) -> Optional[str]:
    """获取世界状态"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM world_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def get_all_world_state(db_path: str) -> Dict[str, str]:
    """获取全部世界状态"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM world_state")
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

# ==================== 元数据操作 ====================

def set_meta(db_path: str, key: str, value: str) -> None:
    """设置元数据"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meta (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_meta(db_path: str, key: str) -> Optional[str]:
    """获取元数据"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def update_meta(db_path: str, key: str, value: str) -> None:
    """更新元数据（兼容性别名）"""
    set_meta(db_path, key, value)

# ==================== 工具函数 ====================

def find_novel_root(book_name: str) -> str:
    """查找小说根目录"""
    novels_dir = os.path.expanduser("~/hermes/novels/")
    for chapter_dir in os.listdir(novels_dir):
        if book_name in chapter_dir:
            return os.path.join(novels_dir, chapter_dir)
    direct = os.path.join(novels_dir, book_name)
    if os.path.exists(direct):
        return direct
    raise FileNotFoundError(f"找不到小说: {book_name}")

def get_db_path(book_name: str) -> str:
    """获取数据库路径"""
    root = find_novel_root(book_name)
    return os.path.join(root, DB_NAME)

# ==================== 主函数 ====================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 tracking_db.py <书名> [init]")
        sys.exit(1)
    
    book_name = sys.argv[1]
    db_path = get_db_path(book_name)
    
    if len(sys.argv) >= 3 and sys.argv[2] == "init":
        init_db(db_path)
        print(f"数据库路径: {db_path}")
    else:
        # 测试连接
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()
        print(f"数据库: {db_path}")
        print(f"表: {tables}")