#!/usr/bin/env python3
"""创建小说目录结构并生成初始文件"""
import os
import sys
import argparse

# 同一目录的脚本可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_novel_structure(novel_name: str, base_dir: str = None) -> str:
    """创建单本小说的完整目录结构，返回根目录路径"""
    if base_dir is None:
        base_dir = os.path.expanduser("~/hermes/novels")

    novel_dir = os.path.join(base_dir, novel_name)

    dirs_to_create = [
        "世界观",
        "势力",
        "人物/角色档案",
        "大纲",
        "写作指南",
        "正文/卷一_铺垫与启程",
        "正文/卷二_对抗与成长",
        "正文/卷三_高潮与收官",
    ]

    for sub in dirs_to_create:
        path = os.path.join(novel_dir, sub)
        os.makedirs(path, exist_ok=True)
        print(f"  创建: .../{novel_name}/{sub}/")

    return novel_dir

def create_tracking_files(novel_dir: str, total_chapters: int = 150, chapter_word_count: int = 3000):
    """创建三个新追踪文件"""
    lines = {
        "大纲/剧情线追踪.md": f"""# 剧情线追踪

> 每条线独立记录 | 章节写完后更新

---

## 线条定义

|| 线条ID | 线条名称 | 类型 | 核心内容 | 状态 |
|--------|--------|--------|------|---------|------|
| L01 | （待补充） | 主线 | （待补充） | 进行中 |
| L02 | （待补充） | 副线 | （待补充） | 进行中 |

---

## 线条详细记录

### L01：（线条名称）

- **起点**：第1章
- **当前进展**：待补充
- **下次出现**：待定
- **状态**：进行中
- **关键节点**：第1章（起点事件）
- **待回收伏笔**：Fxxx

---

## 本章线条推进记录（每章写完后追加）

### 第1章
- L01：（✓/×）（推进/未推进）
""",
        "大纲/进度看板.md": f"""# 进度看板

> 追踪整体创作进度 | 每写完一章或发生变更时更新

---

## 基本参数

| 参数 | 值 |
|------|---|
| 目标总章节 | {total_chapters} 章 |
| 目标每章字数 | {chapter_word_count} 字 |
| 目标总字数 | {total_chapters * chapter_word_count // 10000} 万字 |
| 当前卷数 | 卷一（铺垫与启程） |
| 当前卷章节 | 0/50 章 |

---

## 总体进度

| 指标 | 已完成 | 剩余 | 完成率 |
|------|--------|------|--------|
| 章节数 | 0 章 | {total_chapters} 章 | 0% |
| 总字数 | 0 字 | {total_chapters * chapter_word_count // 10000} 万字 | 0% |
| 伏笔回收 | 0 个 | F001-Fxxx | 0% |

---

## 分卷进度

### 卷一：铺垫与启程（50章）

| 指标 | 值 |
|------|---|
| 目标字数 | 15 万字 |
| 已写字数 | 0 字 |
| 已完成章节 | 0/50 章 |
| 完成率 | 0% |
| 主要推进线条 | L01、L02 |

### 卷二：对抗与成长（50章）

| 指标 | 值 |
|------|---|
| 目标字数 | 15 万字 |
| 已写字数 | 0 字 |
| 已完成章节 | 0/50 章 |
| 完成率 | 0% |

### 卷三：高潮与收官（50章）

| 指标 | 值 |
|------|---|
| 目标字数 | 15 万字 |
| 已写字数 | 0 字 |
| 已完成章节 | 0/50 章 |
| 完成率 | 0% |

---

## 待处理问题（BLOCKERS）

| 问题 | 影响 | 提出时间 | 状态 |
|------|------|---------|------|
| （暂无） | — | — | — |

---

## 本月目标

| 月份 | 目标章节 | 实际完成 | 备注 |
|------|---------|---------|------|
| 第1月 | 0章 | 0章 | — |
""",
        "大纲/角色弧光追踪.md": """# 角色弧光追踪

> 追踪每个核心角色在故事中的成长/堕落轨迹 | 每章写完后更新

---

## 弧光定义表

|| 角色ID | 角色名 | 弧光类型 | 起点状态 | 终点状态 | 当前阶段 |
|--------|--------|--------|---------|---------|---------|---------|
| A01 | （待补充） | 堕落→觉醒 | （待补充） | （待补充） | 起点 |

---

## 弧光详细记录

### A01：（角色名）

- **弧光类型**：觉醒型 / 堕落型 / 深化型 / 转化型
- **起点**（第1章）：待补充
- **当前阶段**：起点
- **关键转折点**：第1章（起点事件）
- **当前心理状态**：待补充
- **下次出现章节**：待定

---

## 本章弧光变化记录（每章写完后追加）

### 第1章
- A01（角色名）：无变化 / ✓ 变化描述
"""
    }

    for file_path, content in lines.items():
        full_path = os.path.join(novel_dir, file_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  生成: .../{os.path.basename(novel_dir)}/{file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python init_novel.py 「书名」 [总章节数] [每章字数] [--主角 主角名]")
        sys.exit(1)

    novel_name = sys.argv[1]
    total_chapters = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    chapter_word_count = int(sys.argv[3]) if len(sys.argv) > 3 else 3000

    # 解析可选参数
    protagonist = None
    if "--主角" in sys.argv:
        idx = sys.argv.index("--主角")
        protagonist = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    print(f"\n📚 开始创建小说目录: {novel_name}\n")
    root = create_novel_structure(novel_name)
    create_tracking_files(root, total_chapters, chapter_word_count)
    print(f"\n✅ 目录结构创建完成: {root}")

    # 自动初始化追踪数据库
    print(f"\n🔄 初始化追踪数据库...\n")
    import init_tracking
    try:
        db_path = init_tracking.init_tracking(novel_name, protagonist)
        print(f"\n🎉 全部完成！")
        print(f"\n  小说目录: {root}")
        print(f"  追踪数据库: {db_path}")
        print(f"\n下一步: 生成设定集 → 开始写第1章")
    except FileNotFoundError as e:
        print(f"\n⚠️ 追踪数据库初始化跳过: {e}")
        print(f"  （需先创建目录，再次运行 init_novel.py 即可）")
        print(f"\n✅ 目录已就绪，可开始生成设定集")