#!/usr/bin/env python3
"""
post_chapter.py — 子代理章节写完后自动更新追踪文件（SQLite 版）

用法：
  python3 post_chapter.py <书名> <章节号> <字数> "<核心事件>" [章节文件路径]

示例：
  python3 post_chapter.py "嘴强剑仙" 13 2856 "大比32强，陆天击败对手"
  python3 post_chapter.py "嘴强剑仙" 14 3100 "陆天晋级16强" "/path/to/chapter14.md"

流程：
  1. 写入 SQLite 数据库
  2. 自动导出所有 Markdown 追踪文件
  3. 验证导出结果
"""

import sys
import os

# 导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db
import export_md

# 已知角色名
KNOWN_CHARS = tracking_db.CHARACTER_IDS  # {'陆天': 'A01', ...}

def log(msg):
    print(f"  → {msg}")

def error_exit(msg):
    print(f"❌ 错误: {msg}")
    sys.exit(1)

def detect_characters(chapter_path: str = None) -> list:
    """从章节文件检测出现的角色"""
    if not chapter_path or not os.path.exists(chapter_path):
        return []
    
    with open(chapter_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    found = []
    for name, char_id in KNOWN_CHARS.items():
        if name in text and char_id not in found:
            found.append(char_id)
            log(f"检测到角色: {name} ({char_id})")
    return found

def find_chapter_file(novel_root: str, chapter_num: int) -> str:
    """在正文章节目录中查找章节文件"""
    for root, dirs, files in os.walk(novel_root):
        for f in files:
            if f"第{chapter_num}章" in f and f.endswith('.md'):
                return os.path.join(root, f)
    return None

def main():
    if len(sys.argv) < 5:
        print("用法: python3 post_chapter.py <书名> <章节号> <字数> \"<核心事件>\" [章节文件路径]")
        sys.exit(1)
    
    book_name = sys.argv[1]
    chapter_num = int(sys.argv[2])
    char_count = int(sys.argv[3])
    core_event = sys.argv[4]
    chapter_path = sys.argv[5] if len(sys.argv) > 5 else None
    
    print(f"\n📝 更新追踪文件")
    print(f"  书名: {book_name}")
    print(f"  章节: 第{chapter_num}章")
    print(f"  字数: {char_count}")
    print(f"  事件: {core_event}")
    
    # 获取数据库路径
    try:
        db_path = tracking_db.get_db_path(book_name)
        novel_root = tracking_db.find_novel_root(book_name)
    except FileNotFoundError as e:
        error_exit(str(e))
    
    log(f"数据库: {db_path}")
    
    # 确保数据库已初始化
    if not os.path.exists(db_path):
        print("  数据库不存在，初始化中...")
        tracking_db.init_db(db_path)
    
    # 1. 插入/更新章节
    log(f"写入章节 {chapter_num} 到数据库...")
    tracking_db.insert_or_update_chapter(
        db_path, chapter_num,
        title=f"第{chapter_num}章",
        words=char_count,
        status="done",
        core_event=core_event
    )
    
    # 2. 自动查找章节文件并检测角色
    if not chapter_path:
        chapter_path = find_chapter_file(novel_root, chapter_num)
    
    characters = detect_characters(chapter_path)
    
    # 3. 追加编年史
    log("追加编年史...")
    # 根据章节号估算时间（简化：每章一天）
    time_label = f"入学第{chapter_num}天"
    tracking_db.append_chronicle(db_path, chapter_num, time_label, core_event)
    
    # 4. 导出全部 Markdown
    log("导出 Markdown 文件...")
    export_md.export_all(book_name)
    
    # 5. 验证导出结果
    print("\n=== 验证追踪文件 ===")
    outline_dir = os.path.join(novel_root, "大纲")
    for fname in ["进度看板.md", "剧情线追踪.md", "编年史.md"]:
        fpath = os.path.join(outline_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"第{chapter_num}章" in content:
                print(f"  ✅ {fname}")
            else:
                print(f"  ❌ {fname}: 未找到第{chapter_num}章！")
        else:
            print(f"  ⏭️  {fname}: 文件不存在")
    # 角色弧光追踪不按章节逐章记录，无需验证章节号
    
    print("\n🎉 追踪文件更新完成！")

if __name__ == "__main__":
    main()