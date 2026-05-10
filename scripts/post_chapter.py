#!/usr/bin/env python3
"""
post_chapter.py — 子代理章节写完后自动更新追踪文件

用法：
  python3 post_chapter.py <书名> <章节号> <字数> <核心事件>

示例：
  python3 post_chapter.py "嘴强剑仙：我的吐槽能杀人" 13 2856 "大比32强，陆天击败对手"
"""

import sys
import os
from datetime import datetime

if len(sys.argv) < 5:
    print("参数不足，需要：书名 章节号 字数 核心事件")
    sys.exit(1)

book_name = sys.argv[1]
chapter_num = sys.argv[2]
char_count = sys.argv[3]
core_event = sys.argv[4]

# 找小说根目录
novels_dir = os.path.expanduser("~/hermes/novels/")
chapter_match = None

for chapter_dir in os.listdir(novels_dir):
    if book_name in chapter_dir:
        novel_root = os.path.join(novels_dir, chapter_dir)
        chapter_match = novel_root
        break

if not chapter_match:
    # 尝试精确匹配
    novel_root = os.path.join(novels_dir, book_name)
    if not os.path.exists(novel_root):
        print(f"错误：找不到小说目录 {book_root}")
        sys.exit(1)

# 找到卷一目录（通常是第一个正文卷）
outline_dir = os.path.join(novel_root, "大纲")
tracking_file = os.path.join(outline_dir, "剧情线追踪.md")
progress_file = os.path.join(outline_dir, "进度看板.md")
chronicle_file = os.path.join(outline_dir, "编年史.md")
arc_file = os.path.join(outline_dir, "角色弧光追踪.md")

print(f"小说根目录: {novel_root}")
print(f"章节: 第{chapter_num}章, {char_count}字")

# 1. 更新剧情线追踪.md
if os.path.exists(tracking_file):
    with open(tracking_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_section = f"""
### 第{chapter_num}章（已完成）

**字数**：{char_count}字 ✅

**核心事件**：{core_event}

"""

    if '---' in content:
        parts = content.split('---', 1)
        updated = parts[0] + '---\n' + new_section + parts[1]
    else:
        updated = content + new_section
    
    with open(tracking_file, 'w', encoding='utf-8') as f:
        f.write(updated)
    print(f"✅ 已更新剧情线追踪.md")
else:
    print(f"⚠️ 剧情线追踪.md 不存在，跳过")

# 2. 更新进度看板.md（找到对应行更新）
if os.path.exists(progress_file):
    with open(progress_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到待写的那一行，替换为完成
    old_line = f"| 第{chapter_num}章 | 🔲 待写 |"
    new_line = f"| 第{chapter_num}章 | ✅完成 | {char_count} | {core_event} |"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已更新进度看板.md")
    else:
        print(f"⚠️ 未找到待写行: {old_line}")
else:
    print(f"⚠️ 进度看板.md 不存在，跳过")

# 3. 更新编年史.md
if os.path.exists(chronicle_file):
    with open(chronicle_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_entry = f"| 第{chapter_num}章 | {core_event} | 第{chapter_num}章 |\n"
    
    if '| 时间 | 事件 | 章节 |' in content:
        # 插入到表格第一行后面
        content = content.replace(
            '| 时间 | 事件 | 章节 |\n|------|------|------|\n',
            f'| 时间 | 事件 | 章节 |\n|------|------|------|\n{new_entry}'
        )
        with open(chronicle_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已更新编年史.md")
else:
    print(f"⚠️ 编年史.md 不存在，跳过")

# 4. 更新角色弧光追踪.md（追加本章弧光记录）
if os.path.exists(arc_file):
    with open(arc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_record = f"""
### 第{chapter_num}章
- 待补充（子代理章节写入时自动记录）

"""
    
    marker = "## 本章弧光变化记录"
    if marker in content:
        content = content.replace(marker, new_record + marker)
        with open(arc_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已更新角色弧光追踪.md")
else:
    print(f"⚠️ 角色弧光追踪.md 不存在，跳过")

# 5. 验证追踪文件已更新
print("\n=== 验证追踪文件 ===")
for fname, fpath in [
    ("剧情线追踪", tracking_file),
    ("进度看板", progress_file),
    ("编年史", chronicle_file),
    ("角色弧光", arc_file)
]:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if f"第{chapter_num}章" in content:
            print(f"✅ {fname}: 已包含第{chapter_num}章")
        else:
            print(f"❌ {fname}: 未找到第{chapter_num}章！")
    else:
        print(f"⏭️  {fname}: 文件不存在")

print("\n🎉 追踪文件更新完成！")