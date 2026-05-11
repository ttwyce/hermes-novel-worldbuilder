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
    
    marker = "## 待处理问题（BLOCKERS）"
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
        lines_text = '\n'.join(lines)
    elif marker in existing_text:
        # 在"## 待处理问题"前插入章节进度
        parts = existing_text.split(marker, 1)
        lines_text = parts[0].rstrip('\n') + '\n\n' + '\n'.join(chapter_lines) + '\n\n---\n\n' + marker + parts[1]
    else:
        # 模板格式不符，直接追加
        lines_text = existing_text.rstrip('\n') + '\n\n' + '\n'.join(chapter_lines)
    
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

# ==================== 导出伏笔钩子追踪 ====================

def export_plot_hooks(db_path: str, out_path: str, book_name: str = None) -> None:
    """导出伏笔钩子追踪.md（新增）"""
    plots = tracking_db.get_active_plots(db_path)
    
    # 同时读取已解决的伏笔
    conn = tracking_db.get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM plot_hooks WHERE status='resolved' ORDER BY resolved_chapter")
    resolved = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    status_names = {
        'active': '⏳ 进行中',
        'foreshadow': '🔮 伏笔中',
        'pending': '📌 待触发',
        'resolved': '✅ 已解开',
    }
    
    lines = [
        "# 伏笔钩子追踪",
        "",
        f"> 记录全书伏笔与回收情况 | 使用 post_chapter.py 的 [伏笔] 参数添加",
        "",
        "---",
        "",
        "## 活跃伏笔",
        "",
    ]
    
    if plots:
        lines.extend([
            "| ID | 章节 | 伏笔内容 | 持续时间 |",
            "|----|------|---------|---------|",
        ])
        for p in plots:
            age = 0  # 简化，不计算了
            lines.append(f"| {p['id']} | 第{p['chapter_id']}章 | {p['plot']} | {p['created_at'][:10]} |")
    else:
        lines.append("_暂无活跃伏笔_")
    
    lines.extend([
        "",
        "---",
        "",
        "## 已解伏笔",
        "",
    ])
    
    if resolved:
        lines.extend([
            "| ID | 埋下章节 | 解开章节 | 伏笔内容 |",
            "|----|---------|---------|---------|",
        ])
        for p in resolved:
            lines.append(f"| {p['id']} | 第{p['chapter_id']}章 | 第{p['resolved_chapter']}章 | {p['plot']} |")
    else:
        lines.append("_暂无已解伏笔_")
    
    lines.extend([
        "",
        "---",
        f"**更新时间**：{datetime.now().strftime('%Y-%m-%d')}",
    ])
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# ==================== 导出世界状态 ====================

def export_world_state(db_path: str, out_path: str, book_name: str = None) -> str:
    """导出世界状态.md（新增），返回摘要供进度看板使用"""
    ws = tracking_db.get_all_world_state(db_path)
    
    lines = [
        "# 世界状态",
        "",
        f"> 记录故事核心世界状态变化 | 由 post_chapter.py --world-state 参数写入",
        "",
        "---",
        "",
        "## 当前世界状态",
        "",
    ]
    
    if ws:
        lines.extend([
            "| 状态项 | 当前值 |",
            "|--------|--------|",
        ])
        for k, v in ws.items():
            lines.append(f"| {k} | {v} |")
    else:
        lines.append("_暂无世界状态记录_")
        lines.append("")
        lines.append("提示：使用 `python3 post_chapter.py \"书名\" N 字数 \"事件\" --world-state \"主角境界:炼气期,当前地点:青云峰\"` 添加")
    
    lines.extend([
        "",
        "---",
        f"**更新时间**：{datetime.now().strftime('%Y-%m-%d')}",
    ])
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # 返回摘要字符串
    if ws:
        items = [f"**{k}**：{v}" for k, v in ws.items()]
        return "；".join(items)
    return None

# ==================== 一键导出全部 ====================

def export_all(book_name: str, current_chapter: int = None) -> None:
    """导出全部追踪文件
    
    Args:
        book_name: 书名
        current_chapter: 当前章节号（用于显示在进度看板的'当前世界状态'中）
    """
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
    
    export_plot_hooks(db_path, os.path.join(outline_dir, "伏笔钩子追踪.md"), book_name)
    print("  ✅ 伏笔钩子追踪.md")
    
    ws_summary = export_world_state(db_path, os.path.join(outline_dir, "世界状态.md"), book_name)
    print("  ✅ 世界状态.md")
    
    # 更新进度看板的"当前世界状态"区域
    if current_chapter:
        _update_progress_board_world_state(
            os.path.join(outline_dir, "进度看板.md"),
            ws_summary, current_chapter
        )
    
    print("\n🎉 全部导出完成！")


def _update_progress_board_world_state(progress_path: str, ws_summary: str, chapter_num: int) -> None:
    """更新进度看板中的'当前世界状态'区域"""
    if not os.path.exists(progress_path):
        return
    
    with open(progress_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    marker = "## 当前世界状态"
    if marker not in content:
        return
    
    # 找到位置，在 marker 后面更新
    parts = content.split(marker, 1)
    if len(parts) < 2:
        return
    
    after_marker = parts[1]
    # 找到下一个 ## 或文件末尾
    next_header = after_marker.find("\n## ")
    if next_header > 0:
        body = after_marker[next_header:]
    else:
        body = after_marker
    
    if ws_summary:
        new_state = f"\n\n- **更新时间**：{datetime.now().strftime('%Y-%m-%d')}\n- {ws_summary}\n"
    else:
        new_state = f"\n\n- **更新时间**：{datetime.now().strftime('%Y-%m-%d')}\n- _暂无世界状态记录_\n"
    
    new_content = parts[0] + marker + new_state + body
    
    with open(progress_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

# ==================== 主函数 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 export_md.py <书名>")
        sys.exit(1)
    
    book_name = sys.argv[1]
    export_all(book_name)