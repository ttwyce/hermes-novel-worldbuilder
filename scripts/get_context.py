#!/usr/bin/env python3
"""
get_context.py — 生成章节写作上下文（通用版）

用法：
  python3 get_context.py <书名> <章节号>
  python3 get_context.py "我的小说" 5

输出：
  - 上章结尾状态
  - 当前各角色状态
  - 久未互动的角色
  - 积压的伏笔
  - 章节衔接提示

所有数据从数据库读取，适用于任何小说。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

def get_prev_chapter_info(db_path: str, chapter_num: int) -> str:
    """获取上章信息"""
    prev_ch = chapter_num - 1
    if prev_ch < 1:
        return "第1章，无前情"
    
    chapter = tracking_db.get_chapter(db_path, prev_ch)
    if not chapter:
        return f"第{prev_ch}章信息未找到"
    
    return f"第{prev_ch}章：{chapter['core_event'] or '（无描述）'}（{chapter['words']}字）"

def format_arc(arc: dict) -> str:
    """格式化角色弧光信息"""
    moments = arc.get('key_moments', [])
    last_moment = moments[-1] if moments else None
    
    lines = [
        f"【{arc['name']}】{arc['arc_type']}弧光",
        f"  当前状态：{arc['current_state']}",
    ]
    if arc['current_chapter'] > 0:
        lines.append(f"  上次互动：第{arc['current_chapter']}章" + 
                    (f" - {last_moment['event']}" if last_moment else ""))
    else:
        lines.append("  上次互动：尚未出场")
    return '\n'.join(lines)

def get_characters_with_gaps(arcs: list, chapter_num: int, limit: int = 5) -> list:
    """获取最久未互动的角色"""
    char_gaps = []
    for arc in arcs:
        if arc['id'] == 'A01':  # 跳过主角
            continue
        gap = chapter_num - arc['current_chapter']
        char_gaps.append((gap, arc['name'], arc))
    
    char_gaps.sort(reverse=True)
    return char_gaps[:limit]

def suggest_relationships_to_advance(chapter_num: int, arcs: list) -> str:
    """建议本章应推进的关系线"""
    suggestions = []
    
    for arc in arcs:
        if arc['id'] == 'A01':
            continue
        last_ch = arc['current_chapter']
        gap = chapter_num - last_ch
        
        if gap >= 5:
            suggestions.append(f"  ⚠️ {arc['name']}已{gap}章无互动，建议安排出场")
        elif gap >= 3:
            suggestions.append(f"  💡 {arc['name']}已{gap}章无互动，可考虑出场")
    
    return '\n'.join(suggestions) if suggestions else "  ✅ 主要角色近期都有互动"

def format_active_plots(db_path: str, chapter_num: int) -> str:
    """获取并格式化活跃伏笔"""
    plots = tracking_db.get_active_plots(db_path)
    
    if not plots:
        return "  ✅ 无积压伏笔"
    
    lines = []
    status_icons = {
        'active': '⏳',
        'foreshadow': '🔮',
        'pending': '📌'
    }
    
    for p in plots:
        age = chapter_num - p['chapter_id']
        icon = status_icons.get(p['status'], '📌')
        lines.append(f"  {icon} 第{p['chapter_id']}章起「{p['plot']}」（{age}章未解，ID:{p['id']}）")
    
    return '\n'.join(lines)

def generate_context(book_name: str, chapter_num: int) -> str:
    """生成完整的章节上下文"""
    db_path = tracking_db.get_db_path(book_name)
    
    chapters = tracking_db.get_all_chapters(db_path)
    arcs = tracking_db.get_all_character_arcs(db_path)
    ws = tracking_db.get_all_world_state(db_path)
    
    # 基本信息
    lines = [
        f"📖 章节上下文：第{chapter_num}章",
        "=" * 50,
        "",
        "【上章信息】",
        get_prev_chapter_info(db_path, chapter_num),
        "",
    ]
    
    # 世界状态
    if ws:
        lines.append("【当前世界状态】")
        for k, v in ws.items():
            lines.append(f"  {k}：{v}")
        lines.append("")
    
    # 当前各角色状态（排除主角）
    main_chars = [a for a in arcs if a['id'] != 'A01'][:5]
    if main_chars:
        lines.append("【主要角色当前状态】")
        for arc in main_chars:
            lines.append(format_arc(arc))
        lines.append("")
    
    # 久未互动的角色
    least_recent = get_characters_with_gaps(arcs, chapter_num)
    if least_recent:
        lines.append("【久未互动的角色】（建议安排出场）")
        for gap, name, arc in least_recent:
            if gap >= 3:
                lines.append(f"  ⚠️ {name}：已{gap}章（上次在第{arc['current_chapter']}章）")
        lines.append("")
    
    # 关系推进建议
    lines.append("【关系线推进建议】")
    lines.append(suggest_relationships_to_advance(chapter_num, arcs))
    lines.append("")
    
    # 积压伏笔
    lines.append("【积压伏笔】")
    lines.append(format_active_plots(db_path, chapter_num))
    lines.append("")
    
    # 章节衔接提示
    prev_ch = chapter_num - 1
    if prev_ch >= 1:
        chapter = tracking_db.get_chapter(db_path, prev_ch)
        if chapter:
            lines.append("【衔接提示】")
            lines.append(f"  上章「{chapter['core_event'] or '（无描述）'}」结束")
            lines.append("  本章需要：")
            
            event = chapter.get('core_event', '')
            if '战斗' in event or '击败' in event or '大比' in event:
                lines.append("  → 战斗/比赛结果需要交代")
            if '争吵' in event or '冲突' in event or '互怼' in event:
                lines.append("  → 关系线需要承接")
            if '发现' in event or '揭露' in event:
                lines.append("  → 伏笔需要推进")
            if '决定' in event or '计划' in event:
                lines.append("  → 计划需要执行/受阻")
    
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("用法: python3 get_context.py <书名> <章节号>")
        print("例:   python3 get_context.py \"我的小说\" 5")
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
        print(f"错误: 找不到小说目录")
        print(f"  搜索: ~/novels/{book_name}")
        print(f"  提示: 先运行 python3 init_tracking.py \"{book_name}\" 初始化")
        sys.exit(2)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()