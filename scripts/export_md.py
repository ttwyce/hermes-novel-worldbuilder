#!/usr/bin/env python3
"""
export_md.py — 从 SQLite 数据库导出 Markdown 追踪文件

导出文件：
- 大纲/进度看板.md
- 大纲/剧情线追踪.md
- 大纲/编年史.md
- 大纲/角色弧光追踪.md
"""

import os
import sys
from datetime import datetime
from typing import List, Dict

# 导入同目录的 tracking_db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# ==================== 导出进度看板 ====================

def export_progress_board(db_path: str, out_path: str, book_name: str = None) -> None:
    """导出进度看板.md"""
    if book_name is None:
        book_name = "小说"
    chapters = tracking_db.get_all_chapters(db_path)
    completed = [c for c in chapters if c['status'] == 'done']
    total_words = sum(c['words'] for c in completed)
    
    # 优先从 meta 读取计划总章数，否则降级
    planned = tracking_db.get_meta(db_path, 'planned_chapters')
    word_count = tracking_db.get_meta(db_path, 'chapter_word_count')
    total = int(planned) if planned else (len(chapters) or 150)
    wc = int(word_count) if word_count else 3000
    
    # 读取模板文件，在"## 待处理问题"前插入章节进度表
    existing_text = ""
    if os.path.exists(out_path):
        with open(out_path, 'r', encoding='utf-8') as f:
            existing_text = f.read()
    else:
        existing_text = None
    
    # 生成新章节进度表
    chapter_lines = [
        "",
        "## 章节进度",
        "",
        "### 卷一：铺垫与启程",
        "",
        "| 章节 | 状态 | 字数 | 备注 |",
        "|------|------|------|------|",
    ]
    for ch in chapters:
        if ch['status'] == 'done':
            chapter_lines.append(f"| 第{ch['id']}章 | ✅完成 | {ch['words']} | {ch['core_event'] or ''} |")
        else:
            chapter_lines.append(f"| 第{ch['id']}章 | 🔲 待写 | | |")
    chapter_lines.extend([
        "",
        f"**已写章节**：{len(completed)}/{total}（{len(completed)*100//max(total,1)}%）",
        f"**总字数**：{total_words}字",
        "",
    ])
    
    if existing_text is None:
        # 无模板，纯生成
        lines = [
            "# 进度看板",
            "",
            f"## {book_name}",
            "",
            f"**总目标**：{total}章 / {total * wc // 10000}万字",
            "",
            "---",
        ] + chapter_lines + [
            "---",
            "",
            "## 当前世界状态",
            "",
            f"- **更新时间**：{datetime.now().strftime('%Y-%m-%d')}",
        ]
    else:
        # 有模板：在"## 待处理问题"前插入章节进度
        marker = "## 待处理问题（BLOCKERS）"
        if marker in existing_text:
            parts = existing_text.split(marker)
            lines_text = parts[0].rstrip('\n') + '\n\n' + '\n'.join(chapter_lines) + '\n\n---\n\n' + marker + parts[1]
        else:
            # 模板格式不符，直接替换末尾
            lines_text = existing_text + '\n\n' + '\n'.join(chapter_lines)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(lines_text)

# ==================== 导出剧情线追踪 ====================

def export_tracking(db_path: str, out_path: str, book_name: str = None) -> None:
    """导出剧情线追踪.md"""
    chapters = tracking_db.get_completed_chapters(db_path)
    
    lines = [
        "# 剧情线追踪",
        "",
        f"## {book_name or '小说'}",
        "",
        "---",
    ]
    
    for ch in chapters:
        lines.extend([
            f"",
            f"### 第{ch['id']}章 {'（已完成）' if ch['status'] == 'done' else ''}",
            f"",
            f"**字数**：{ch['words']}字 ✅" if ch['status'] == 'done' else f"**字数**：—",
            f"",
            f"**核心事件**：{ch['core_event'] or '—'}",
            f"",
            "---",
        ])
    
    # 写入文件
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# ==================== 导出编年史 ====================

def export_chronicle(db_path: str, out_path: str, book_name: str = None) -> None:
    """导出编年史.md"""
    if book_name is None:
        book_name = "小说"
    chronicle = tracking_db.get_chronicle(db_path)
    
    # 按时间/章节分组
    lines = [
        "# 编年史",
        "",
        f"## {book_name}",
        "",
        "---",
        "",
        "### 故事开始",
        "",
        "| 时间 | 事件 | 章节 |",
        "|------|------|------|",
    ]
    
    for entry in chronicle:
        lines.append(f"| 第{entry['chapter']}章 | {entry['event']} | 第{entry['chapter']}章 |")
    
    lines.extend([
        "",
        "---",
        f"**更新时间**：{datetime.now().strftime('%Y-%m-%d')}",
    ])
    
    # 写入文件
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# ==================== 导出角色弧光追踪 ====================

def export_arc_tracking(db_path: str, out_path: str, novel_name: str) -> None:
    """导出角色弧光追踪.md"""
    arcs = tracking_db.get_all_character_arcs(db_path)
    
    arc_type_names = {
        '觉醒型': '觉醒型',
        '深化型': '深化型',
        '悬念型': '悬念型',
        '堕落型': '堕落型',
    }
    
    lines = [
        "# 角色弧光追踪",
        "",
        f"> 追踪每个核心角色在故事中的成长/堕落轨迹 | 每章写完后更新",
        "",
        "---",
        "",
        "## 弧光定义表",
        "",
        "| 角色ID | 角色名 | 弧光类型 | 起点状态 | 终点状态 | 当前阶段 |",
        "|--------|--------|--------|---------|---------|---------|",
    ]
    
    for arc in arcs:
        current_ch = f"第{arc['current_chapter']}章" if arc['current_chapter'] else "—"
        lines.append(f"| {arc['id']} | {arc['name']} | {arc['arc_type']} | {arc['start_state']} | {arc.get('end_state', '—')} | {current_ch} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 弧光详细记录",
        "",
    ])
    
    for arc in arcs:
        lines.extend([
            f"### {arc['id']}：{arc['name']}",
            f"",
            f"- **弧光类型**：{arc['arc_type']}",
            f"- **起点**：{arc['start_state']}",
            f"- **当前阶段**：{arc['current_state']}",
            f"- **关键转折点**：",
        ])
        
        for moment in arc['key_moments']:
            lines.append(f"  - 第{moment['chapter']}章：{moment['event']}")
        
        lines.append(f"- **当前心理状态**：{arc['current_state']}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## 本章弧光变化记录",
        "",
    ])
    
    # 写入文件
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# ==================== 一键导出全部 ====================

def export_all(book_name: str) -> None:
    """导出全部追踪文件"""
    db_path = tracking_db.get_db_path(book_name)
    novel_root = tracking_db.find_novel_root(book_name)
    outline_dir = os.path.join(novel_root, "大纲")
    
    print(f"导出到: {outline_dir}")
    
    export_progress_board(db_path, os.path.join(outline_dir, "进度看板.md"), book_name)
    print("  ✅ 进度看板.md")
    
    export_tracking(db_path, os.path.join(outline_dir, "剧情线追踪.md"), book_name)
    print("  ✅ 剧情线追踪.md")
    
    export_chronicle(db_path, os.path.join(outline_dir, "编年史.md"), book_name)
    print("  ✅ 编年史.md")
    
    export_arc_tracking(db_path, os.path.join(outline_dir, "角色弧光追踪.md"), book_name)
    print("  ✅ 角色弧光追踪.md")
    
    print("\n🎉 全部导出完成！")

# ==================== 主函数 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 export_md.py <书名>")
        sys.exit(1)
    
    book_name = sys.argv[1]
    export_all(book_name)