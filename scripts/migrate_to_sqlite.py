#!/usr/bin/env python3
"""
migrate_to_sqlite.py — 将现有 MD 追踪文件迁移到 SQLite

用法：
  python3 migrate_to_sqlite.py <书名>

示例：
  python3 migrate_to_sqlite.py "嘴强剑仙"
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# 角色弧光初始数据
INIT_ARCS = [
    {
        'id': 'A01', 'name': '陆天', 'arc_type': '觉醒型',
        'start_state': '废物伪灵根，自卑但嘴硬',
        'current_state': '吐槽系统觉醒，初步建立自信',
        'current_chapter': 12,
        'key_moments': [
            {'chapter': 1, 'event': '吐槽系统觉醒'},
            {'chapter': 6, 'event': '欠债1万灵石（压力）'},
            {'chapter': 9, 'event': '用智慧反杀李明辉（自信建立）'},
            {'chapter': 12, 'event': '新生大比首胜（证明自己）'},
        ]
    },
    {
        'id': 'A02', 'name': '叶琳', 'arc_type': '深化型',
        'start_state': '高冷傲娇天才',
        'current_state': '从互怼中发现陆天有趣',
        'current_chapter': 10,
        'key_moments': [
            {'chapter': 4, 'event': '重逢，发现他嘴还是一样贱'},
            {'chapter': 10, 'event': '承认他是唯一让她觉得自己是普通人的人'},
        ]
    },
    {
        'id': 'A03', 'name': '苏清雪', 'arc_type': '深化型',
        'start_state': '高冷无聊',
        'current_state': '开始主动关注陆天',
        'current_chapter': 7,
        'key_moments': [
            {'chapter': 6, 'event': '借钱1万（建立联系）'},
            {'chapter': 7, 'event': '主动要求被吐槽（引起兴趣）'},
        ]
    },
    {
        'id': 'A04', 'name': '陈朵朵', 'arc_type': '悬念型',
        'start_state': '傻白甜？',
        'current_state': '身世之谜浮现',
        'current_chapter': 8,
        'key_moments': [
            {'chapter': 2, 'event': '送灵雾果（反常热情）'},
            {'chapter': 8, 'event': '黑袍人持画像找她（身世暴露）'},
        ]
    },
    {
        'id': 'A05', 'name': '赵婉清', 'arc_type': '深化型',
        'start_state': '嘴毒导员',
        'current_state': '暗中观察陆天',
        'current_chapter': 3,
        'key_moments': [
            {'chapter': 3, 'event': '私下谈话，表明不偏帮也不打压'},
        ]
    },
    {
        'id': 'B01', 'name': '李明辉', 'arc_type': '深化型',
        'start_state': '天灵根，傲慢',
        'current_state': '记恨陆天，伺机报复',
        'current_chapter': 12,
        'key_moments': [
            {'chapter': 1, 'event': '当众羞辱陆天，被反怼'},
            {'chapter': 9, 'event': '陷害计划破产'},
            {'chapter': 12, 'event': '决定亲自关注这个废物'},
        ]
    },
    {
        'id': 'C01', 'name': '陈浩', 'arc_type': '深化型',
        'start_state': '话痨情报通',
        'current_state': '陆天好友',
        'current_chapter': 2,
        'key_moments': [
            {'chapter': 2, 'event': '成为室友和好友'},
        ]
    },
    {
        'id': 'B02', 'name': '周天成', 'arc_type': '深化型',
        'start_state': '周家少爷，嚣张',
        'current_state': '被陆天击败，心态崩溃',
        'current_chapter': 12,
        'key_moments': [
            {'chapter': 5, 'event': '食堂插队被怼'},
            {'chapter': 12, 'event': '大比被击败'},
        ]
    },
]

# 已知的章节数据
EXISTING_CHAPTERS = [
    (1, 3051, "新生测试大典，陆天觉醒吐槽系统，怼李明辉"),
    (2, 3565, "入住通识院302室，室友陈浩相识，陈朵朵送灵雾果"),
    (3, 2789, "赵婉清上课点名叫醒睡觉的陆天，陆天答对问题"),
    (4, 2665, "天食堂偶遇叶琳，两人互怼"),
    (5, 2726, "周家少爷周天成插队被陆天怼走"),
    (6, 2950, "陆天炸了电路板，欠债1万灵石，向苏清雪借钱"),
    (7, 3269, "苏清雪要求看陆天吐槽，被造成12点伤害"),
    (8, 4346, "黑袍人找陈朵朵，警告陆天不要调查"),
    (9, 3627, "李明辉陷害计划破产，陆天用录影玉简反杀"),
    (10, 4496, "叶琳来食堂找陆天互怼，关系升温"),
    (11, 3601, "班级活动迷雾林，陆天队采集夺冠"),
    (12, 2559, "新生大比首轮，陆天击败周天成"),
]

# 已知编年史
EXISTING_CHRONICLE = [
    (1, "入学第一天", "新生测试大典，陆天觉醒吐槽系统，怼李明辉"),
    (2, "入学第一天", "通识院报到，室友陈浩相识"),
    (2, "入学第一天", "陈朵朵送灵雾果（伏笔）"),
    (3, "入学第二天上午", "赵婉清《修仙伦理与校规》课"),
    (4, "入学第二天中午", "天食堂偶遇叶琳，互怼"),
    (5, "入学第三天", "食堂怼周天成"),
    (6, "入学第三天", "雷法维修课炸电路板"),
    (6, "入学第三天", "向苏清雪借1万灵石还债"),
    (7, "入学第四天", "演武场练吐槽，苏清雪观摩"),
    (8, "入学第五天", "黑袍人找陈朵朵，陆天决心等她说秘密"),
    (9, "入学第六天", "图书馆怼李明辉反杀陷害"),
    (10, "入学第七天", "叶琳来通识院食堂，关系升温"),
    (11, "入学第八天", "班级活动迷雾林，采集夺冠"),
    (12, "入学第九天", "新生大比名单公布，陆天vs周天成"),
    (12, "入学第九天", "大比第一轮，陆天击败周天成"),
]

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
    print(f"  章节: {len(completed)}/150 完成")
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