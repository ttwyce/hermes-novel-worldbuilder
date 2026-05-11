#!/usr/bin/env python3
"""
post_chapter.py — 子代理章节写完后自动更新追踪文件（通用版）

用法：
  python3 post_chapter.py <书名> <章节号> <字数> "<核心事件>" [章节文件] [伏笔]
  python3 post_chapter.py "我的小说" 5 2800 "主角发现秘密" "/path/ch5.md" "主角身世之谜"
  python3 post_chapter.py "我的小说" 6 3000 "主角击败BOSS"

流程：
  1. 写入 SQLite 数据库（章节 + 角色互动）
  2. 添加伏笔钩子（如果提供了）
  3. 导出所有 Markdown 追踪文件
  4. 验证导出结果
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db
import export_md

def log(msg):
    print(f"  → {msg}")

def error_exit(msg):
    print(f"❌ 错误: {msg}")
    sys.exit(1)

def get_all_char_names(db_path: str) -> dict:
    """从数据库获取所有角色名（name -> id 映射）"""
    arcs = tracking_db.get_all_character_arcs(db_path)
    return {arc['name']: arc['id'] for arc in arcs}

def detect_and_update_characters(db_path: str, chapter_path: str, chapter_num: int) -> list:
    """从章节文件检测出现的角色，并更新它们的最新互动章节"""
    if not chapter_path or not os.path.exists(chapter_path):
        return []
    
    char_names = get_all_char_names(db_path)
    if not char_names:
        return []
    
    with open(chapter_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    found = []
    for name, char_id in char_names.items():
        if name in text and char_id not in found:
            found.append(char_id)
            log(f"检测到角色: {name} ({char_id})")
            tracking_db.touch_character(db_path, char_id, chapter_num)
    return found

def update_world_state(db_path: str, world_state_str: str) -> None:
    """解析并写入世界状态
    
    格式: "主角境界:炼气期,当前地点:青云峰"
    """
    if not world_state_str:
        return
    for item in world_state_str.split(","):
        item = item.strip()
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        tracking_db.set_world_state(db_path, key.strip(), value.strip())
        log(f"世界状态: {key.strip()} = {value.strip()}")

def find_chapter_file(novel_root: str, chapter_num: int) -> str:
    """在正文章节目录中查找章节文件"""
    for root, dirs, files in os.walk(novel_root):
        for f in files:
            if f"第{chapter_num}章" in f and f.endswith('.md'):
                return os.path.join(root, f)
    return None

def main():
    parser = argparse.ArgumentParser(description='更新小说追踪数据库')
    parser.add_argument('book_name', help='小说名称')
    parser.add_argument('chapter_num', type=int, help='章节号')
    parser.add_argument('char_count', type=int, help='字数')
    parser.add_argument('core_event', help='核心事件（引号包裹）')
    parser.add_argument('chapter_path', nargs='?', default=None, help='章节文件路径（可选）')
    parser.add_argument('plot_hook', nargs='?', default=None, help='伏笔钩子（可选）')
    parser.add_argument('--world-state', dest='world_state', default=None,
                        help='世界状态，格式: "境界:炼气期,地点:青云峰"')
    
    args = parser.parse_args()
    
    book_name = args.book_name
    chapter_num = args.chapter_num
    char_count = args.char_count
    core_event = args.core_event
    chapter_path = args.chapter_path
    plot_hook = args.plot_hook
    world_state_str = args.world_state
    
    print(f"\n📝 更新追踪文件")
    print(f"  书名: {book_name}")
    print(f"  章节: 第{chapter_num}章")
    print(f"  字数: {char_count}")
    print(f"  事件: {core_event}")
    if plot_hook:
        print(f"  伏笔: {plot_hook}")
    if world_state_str:
        print(f"  世界状态: {world_state_str}")
    
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
    
    characters = detect_and_update_characters(db_path, chapter_path, chapter_num)
    
    # 3. 追加编年史
    log("追加编年史...")
    tracking_db.append_chronicle(db_path, chapter_num, f"第{chapter_num}章", core_event)
    
    # 4. 添加伏笔（如果提供了）
    if plot_hook:
        hook_id = tracking_db.add_plot_hook(db_path, chapter_num, plot_hook)
        log(f"添加伏笔: 「{plot_hook}」（ID: {hook_id}）")
    
    # 5. 更新世界状态（如果提供了）
    if world_state_str:
        update_world_state(db_path, world_state_str)
    
    # 6. 导出全部 Markdown
    log("导出 Markdown 文件...")
    export_md.export_all(book_name, current_chapter=chapter_num)
    
    # 7. 验证导出结果
    print("\n=== 验证追踪文件 ===")
    outline_dir = os.path.join(novel_root, "大纲")
    for fname in ["进度看板.md", "剧情线追踪.md", "编年史.md", "角色弧光追踪.md", "伏笔钩子追踪.md", "世界状态.md"]:
        fpath = os.path.join(outline_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"第{chapter_num}章" in content or fname in ["伏笔钩子追踪.md", "世界状态.md"]:
                print(f"  ✅ {fname}")
            else:
                print(f"  ❌ {fname}: 未找到第{chapter_num}章！")
        else:
            print(f"  ⏭️  {fname}: 文件不存在（可选）")
    
    print("\n🎉 追踪文件更新完成！")

if __name__ == "__main__":
    main()