#!/usr/bin/env python3
"""
get_context.py — 生成章节写作上下文

用法：
  python3 get_context.py <书名> <章节号>
  python3 get_context.py "嘴强剑仙" 13

输出：
  - 上章结尾状态
  - 当前各角色状态
  - 本章应推进的关系线
  - 未解伏笔
  - 章节衔接提示
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# 角色友好名称
NAMES = {
    'A01': '陆天', 'A02': '叶琳', 'A03': '苏清雪',
    'A04': '陈朵朵', 'A05': '赵婉清',
    'B01': '李明辉', 'B02': '周天成', 'C01': '陈浩',
}

# 伏笔列表（需要跟踪哪些没解）
UNRESOLVED_PLOTS = [
    {'id': 1, 'chapter': 2, 'plot': '陈朵朵送灵雾果（反常热情）', 'status': '伏笔中'},
    {'id': 2, 'chapter': 6, 'plot': '陆天欠苏清雪1万灵石', 'status': '进行中'},
    {'id': 3, 'chapter': 8, 'plot': '陈朵朵身世之谜', 'status': '伏笔中'},
    {'id': 4, 'chapter': 8, 'plot': '黑袍人知道陆天有系统', 'status': '伏笔中'},
    {'id': 5, 'chapter': 12, 'plot': '李明辉决定亲自对付陆天', 'status': '待爆发'},
    {'id': 6, 'chapter': 9, 'plot': '陆天欠债1万灵石', 'status': '进行中'},
]

def get_prev_chapter_info(novel_root: str, chapter_num: int) -> str:
    """获取上章信息"""
    prev_ch = chapter_num - 1
    if prev_ch < 1:
        return "第1章，无前情"
    
    chapters = tracking_db.get_all_chapters(tracking_db.get_db_path(novel_root))
    chapter = next((c for c in chapters if c['id'] == prev_ch), None)
    if not chapter:
        return f"第{prev_ch}章信息未找到"
    
    return f"第{prev_ch}章：{chapter['core_event']}（{chapter['words']}字）"

def format_arc(arc: dict) -> str:
    """格式化角色弧光信息"""
    name = NAMES.get(arc['id'], arc['id'])
    moments = arc.get('key_moments', [])
    last_moment = moments[-1] if moments else None
    
    lines = [
        f"【{name}】{arc['arc_type']}弧光",
        f"  当前状态：{arc['current_state']}",
        f"  本章前最新：第{arc['current_chapter']}章" + (f" - {last_moment['event']}" if last_moment else ""),
    ]
    return '\n'.join(lines)

def suggest_relationships_to_advance(chapter_num: int, arcs: list) -> str:
    """建议本章应推进的关系线"""
    suggestions = []
    
    for arc in arcs:
        name = NAMES.get(arc['id'], arc['name'])
        last_ch = arc['current_chapter']
        gap = chapter_num - last_ch
        
        if gap >= 3:
            suggestions.append(f"  ⚠️ {name}已{gap}章无互动，建议安排出场")
        elif gap >= 2:
            suggestions.append(f"  💡 {name}已{gap}章无互动，可考虑出场")
    
    return '\n'.join(suggestions) if suggestions else "  ✅ 主要角色近期都有互动"

def get_unresolved_plots(chapter_num: int) -> str:
    """获取未解伏笔"""
    lines = []
    for p in UNRESOLVED_PLOTS:
        if p['chapter'] <= chapter_num:
            age = chapter_num - p['chapter']
            lines.append(f"  [{p['status']}] 第{p['chapter']}章起的「{p['plot']}」（{age}章未解）")
    return '\n'.join(lines) if lines else "  ✅ 无积压伏笔"

def get_least_recent_chars(arcs: list, chapter_num: int, limit: int = 3) -> str:
    """获取最久未互动的角色"""
    char_gaps = []
    for arc in arcs:
        if arc['id'] == 'A01':  # 跳过主角
            continue
        gap = chapter_num - arc['current_chapter']
        name = NAMES.get(arc['id'], arc['name'])
        char_gaps.append((gap, name, arc))
    
    char_gaps.sort(reverse=True)
    return char_gaps[:limit]

def generate_context(book_name: str, chapter_num: int) -> str:
    """生成完整的章节上下文"""
    novel_root = tracking_db.find_novel_root(book_name)
    db_path = tracking_db.get_db_path(book_name)
    
    chapters = tracking_db.get_all_chapters(db_path)
    arcs = tracking_db.get_all_character_arcs(db_path)
    
    # 基本信息
    lines = [
        f"📖 章节上下文：第{chapter_num}章",
        "=" * 50,
        "",
        "【上章信息】",
        get_prev_chapter_info(novel_root, chapter_num),
        "",
    ]
    
    # 当前各角色状态
    lines.append("【主要角色当前状态】")
    for arc in arcs:
        if arc['id'] in ['A01', 'A02', 'A03', 'A04', 'A05']:  # 主要角色
            lines.append(format_arc(arc))
    lines.append("")
    
    # 久未互动的角色
    least_recent = get_least_recent_chars(arcs, chapter_num)
    lines.append("【久未互动的角色】（建议安排出场）")
    for gap, name, arc in least_recent:
        lines.append(f"  ⚠️ {name}：已{gap}章（上次在第{arc['current_chapter']}章）")
    lines.append("")
    
    # 关系推进建议
    lines.append("【关系线推进建议】")
    lines.append(suggest_relationships_to_advance(chapter_num, arcs))
    lines.append("")
    
    # 未解伏笔
    lines.append("【积压伏笔】")
    lines.append(get_unresolved_plots(chapter_num))
    lines.append("")
    
    # 章节衔接提示
    prev_ch = chapter_num - 1
    if prev_ch >= 1:
        chapter = next((c for c in chapters if c['id'] == prev_ch), None)
        if chapter:
            lines.append("【衔接提示】")
            lines.append(f"  上章「{chapter['core_event']}」结束")
            lines.append("  本章需要：")
            
            # 根据上章结尾建议衔接
            prev_text = chapter.get('core_event', '')
            if '大比' in prev_text:
                lines.append("  → 大比剧情需要继续（战斗结果/下轮对阵）")
            if '互怼' in prev_text or '关系升温' in prev_text:
                lines.append("  → 关系线需要承接热度")
            if '身世' in prev_text:
                lines.append("  → 伏笔需要推进")
    
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("用法: python3 get_context.py <书名> <章节号>")
        print("例:   python3 get_context.py \"嘴强剑仙\" 13")
        sys.exit(1)
    
    book_name = sys.argv[1]
    try:
        chapter_num = int(sys.argv[2])
    except ValueError:
        print("错误: 章节号必须是整数")
        sys.exit(1)
    
    try:
        context = generate_context(book_name, chapter_num)
        print(context)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()