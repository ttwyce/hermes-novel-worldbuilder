#!/usr/bin/env python3
"""
post_chapter.py — 子代理章节写完后自动更新追踪文件

用法：
  python3 post_chapter.py <书名> <章节号> <字数> "<核心事件>" [章节文件路径]

示例：
  python3 post_chapter.py "嘴强剑仙：我的吐槽能杀人" 13 2856 "大比32强，陆天击败对手"
  python3 post_chapter.py "嘴强剑仙" 14 3100 "陆天晋级16强" "/path/to/chapter14.md"
"""

import sys
import os
import re
from datetime import datetime

def log(msg):
    print(f"  → {msg}")

def error_exit(msg):
    print(f"❌ 错误: {msg}")
    sys.exit(1)

def warn(msg):
    print(f"⚠️  警告: {msg}")

def find_novel_root(book_name):
    """查找小说根目录"""
    novels_dir = os.path.expanduser("~/hermes/novels/")
    if not os.path.exists(novels_dir):
        error_exit(f"小说目录不存在: {novels_dir}")
    
    for chapter_dir in os.listdir(novels_dir):
        if book_name in chapter_dir:
            return os.path.join(novels_dir, chapter_dir)
    
    # 尝试直接作为目录名
    direct = os.path.join(novels_dir, book_name)
    if os.path.exists(direct):
        return direct
    
    error_exit(f"找不到小说: {book_name}")

def update_progress_board(progress_file, chapter_num, char_count, core_event):
    """
    更新进度看板.md
    用正则匹配 '| 第X章 |' 所在行，不管后面是什么状态
    """
    if not os.path.exists(progress_file):
        warn(f"进度看板.md 不存在，跳过")
        return False
    
    with open(progress_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 正则匹配章节行：整行从 | 第X章 | 到该行结束 | 前面
    # 匹配模式：| 第13章 | 状态 | 字数 | 备注 | (可能有更多列)
    pattern = rf'(\| 第{chapter_num}章 \| )[^\n]+\n?'
    
    match = re.search(pattern, content)
    if not match:
        warn(f"未找到第{chapter_num}章行")
        return False
    
    # 构建新行：4列表格（章节 | 状态 | 字数 | 备注）
    new_line = f"| 第{chapter_num}章 | ✅完成 | {char_count} | {core_event} |\n"
    
    # 完整替换该行
    content = content[:match.start()] + new_line + content[match.end():]
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write(content)
    log(f"进度看板已更新: {new_line.strip()}")
    return True

def update_tracking(tracking_file, chapter_num, char_count, core_event):
    """
    更新剧情线追踪.md
    找到第一个 '---' 后的位置插入新章节块
    如果本章已存在则跳过
    """
    if not os.path.exists(tracking_file):
        warn(f"剧情线追踪.md 不存在，跳过")
        return False
    
    with open(tracking_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查本章是否已存在
    if f"### 第{chapter_num}章（已完成）" in content:
        log(f"剧情线追踪：第{chapter_num}章已存在，跳过")
        return True
    
    new_section = f"""
### 第{chapter_num}章（已完成）

**字数**：{char_count}字 ✅

**核心事件**：{core_event}

"""
    
    # 找到第一个 --- 并在其后插入（这样新章节在前面）
    if '---' in content:
        parts = content.split('---', 1)
        updated = parts[0] + '---\n' + new_section + parts[1]
    else:
        updated = content + new_section
    
    with open(tracking_file, 'w', encoding='utf-8') as f:
        f.write(updated)
    log("剧情线追踪已更新")
    return True

def update_chronicle(chronicle_file, chapter_num, core_event):
    """
    更新编年史.md
    找到最后一个有 '| 时间 | 事件 | 章节 |' 表头的表格，在其最后一行后追加新行
    """
    if not os.path.exists(chronicle_file):
        warn(f"编年史.md 不存在，跳过")
        return False
    
    with open(chronicle_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到所有表头位置
    table_header = '| 时间 | 事件 | 章节 |'
    header_indices = []
    for i, line in enumerate(lines):
        if table_header in line:
            header_indices.append(i)
    
    if not header_indices:
        warn("编年史中未找到表格，跳过")
        return False
    
    # 用最后一个表格
    header_idx = header_indices[-1]
    
    # 找到表格结束位置（下一个不以 | 开头的内容行，或文件结束）
    table_end_idx = len(lines)
    for i in range(header_idx + 2, len(lines)):  # +2 跳过表头和分隔线
        line = lines[i].strip()
        if not line:  # 跳过空行
            continue
        if line.startswith('|'):  # 仍然是数据行
            table_end_idx = i + 1  # 包含这一行
        else:
            # 遇到非表格内容，结束
            table_end_idx = i
            break
    
    # 构建新行
    new_entry = f"| 第{chapter_num}章 | {core_event} | 第{chapter_num}章 |\n"
    
    # 插入到表格末尾（在结束行之后）
    lines.insert(table_end_idx, new_entry)
    
    with open(chronicle_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    log(f"编年史已更新（插入到第{table_end_idx + 1}行后）")
    return True

def extract_characters_from_chapter(chapter_path):
    """
    从章节文件中提取出现的角色名
    返回角色ID列表
    """
    known_chars = {
        '陆天': 'A01',
        '叶琳': 'A02', 
        '苏清雪': 'A03',
        '陈朵朵': 'A04',
        '赵婉清': 'A05',
        '李明辉': 'B01',
        '陈浩': 'C01',
        '周天成': 'B02',
    }
    
    characters = []
    if chapter_path and os.path.exists(chapter_path):
        try:
            with open(chapter_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            for name, char_id in known_chars.items():
                if name in text and char_id not in characters:
                    characters.append(char_id)
                    log(f"检测到角色: {name} ({char_id})")
        except Exception as e:
            warn(f"读取章节文件失败: {e}")
    
    return characters

def update_arc_tracking(arc_file, chapter_num, core_event, characters):
    """
    更新角色弧光追踪.md
    1. 在 '## 本章弧光变化记录' 前插入本章记录（带自动检测的角色）
    2. 如果本章已存在则跳过
    """
    if not os.path.exists(arc_file):
        warn(f"角色弧光追踪.md 不存在，跳过")
        return False
    
    with open(arc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查本章是否已存在
    chapter_marker = f"### 第{chapter_num}章\n"
    marker_count = content.count(chapter_marker)
    if marker_count >= 2:  # 说明已插入过
        log(f"角色弧光追踪：第{chapter_num}章已存在，跳过")
        return True
    elif marker_count == 1:
        # 检查是否在 '## 本章弧光变化记录' 前
        marker_pos = content.find(chapter_marker)
        arc_section_pos = content.find("## 本章弧光变化记录")
        if marker_pos < arc_section_pos:
            log(f"角色弧光追踪：第{chapter_num}章已在正确位置，跳过")
            return True
    
    # 构建角色列表
    char_names = {
        'A01': '陆天', 'A02': '叶琳', 'A03': '苏清雪',
        'A04': '陈朵朵', 'A05': '赵婉清',
        'B01': '李明辉', 'C01': '陈浩', 'B02': '周天成',
    }
    
    if characters:
        char_entries = '\n'.join([f"- {char_names.get(c, c)}：待补充" for c in characters])
    else:
        char_entries = "- 待人工补充（未检测到已知角色）"
    
    new_record = f"""
### 第{chapter_num}章
{char_entries}
- 核心事件：{core_event}

"""
    
    # 在 '## 本章弧光变化记录' 前插入
    marker = "## 本章弧光变化记录"
    if marker in content:
        parts = content.split(marker, 1)
        updated = parts[0] + new_record + marker + parts[1]
    else:
        # 如果没有marker，追加到文件末尾
        updated = content + '\n' + new_record
        warn("未找到'## 本章弧光变化记录'，追加到文件末尾")
    
    with open(arc_file, 'w', encoding='utf-8') as f:
        f.write(updated)
    log("角色弧光追踪已更新")
    return True

def verify_update(novel_root, chapter_num):
    """验证所有追踪文件都包含新章节"""
    print("\n=== 验证追踪文件 ===")
    
    files_to_check = [
        ("剧情线追踪", os.path.join(novel_root, "大纲", "剧情线追踪.md")),
        ("进度看板", os.path.join(novel_root, "大纲", "进度看板.md")),
        ("编年史", os.path.join(novel_root, "大纲", "编年史.md")),
        ("角色弧光", os.path.join(novel_root, "大纲", "角色弧光追踪.md")),
    ]
    
    all_ok = True
    for name, fpath in files_to_check:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"第{chapter_num}章" in content:
                print(f"  ✅ {name}: 已包含第{chapter_num}章")
            else:
                print(f"  ❌ {name}: 未找到第{chapter_num}章！")
                all_ok = False
        else:
            print(f"  ⏭️  {name}: 文件不存在（跳过）")
    
    return all_ok

def main():
    if len(sys.argv) < 5:
        print("用法: python3 post_chapter.py <书名> <章节号> <字数> \"<核心事件>\" [章节文件路径]")
        sys.exit(1)
    
    book_name = sys.argv[1]
    chapter_num = sys.argv[2]
    char_count = sys.argv[3]
    core_event = sys.argv[4]
    chapter_path = sys.argv[5] if len(sys.argv) > 5 else None
    
    print(f"\n📝 更新追踪文件")
    print(f"  书名: {book_name}")
    print(f"  章节: 第{chapter_num}章")
    print(f"  字数: {char_count}")
    print(f"  事件: {core_event}")
    
    # 找小说目录
    novel_root = find_novel_root(book_name)
    log(f"小说目录: {novel_root}")
    
    outline_dir = os.path.join(novel_root, "大纲")
    
    # 更新各追踪文件
    print()
    update_progress_board(
        os.path.join(outline_dir, "进度看板.md"),
        chapter_num, char_count, core_event
    )
    update_tracking(
        os.path.join(outline_dir, "剧情线追踪.md"),
        chapter_num, char_count, core_event
    )
    update_chronicle(
        os.path.join(outline_dir, "编年史.md"),
        chapter_num, core_event
    )
    
    # 从章节文件提取角色
    characters = extract_characters_from_chapter(chapter_path) if chapter_path else []
    if not characters:
        # 如果没提供路径，尝试自动查找
        # 查找正文章节目录
        for root, dirs, files in os.walk(novel_root):
            for f in files:
                if f"第{chapter_num}章" in f and f.endswith('.md'):
                    characters = extract_characters_from_chapter(os.path.join(root, f))
                    break
    
    update_arc_tracking(
        os.path.join(outline_dir, "角色弧光追踪.md"),
        chapter_num, core_event, characters
    )
    
    # 验证
    all_ok = verify_update(novel_root, chapter_num)
    
    print()
    if all_ok:
        print("🎉 追踪文件更新完成！")
    else:
        print("⚠️  部分追踪文件更新失败，请检查")
        sys.exit(1)

if __name__ == "__main__":
    main()