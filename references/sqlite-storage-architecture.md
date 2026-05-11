# SQLite 存储架构详解

## 背景

纯 MD 文本存储有三大问题：
1. **格式脆弱**：进度看板多列残留、编年史插入位置错误
2. **难以查询**：依赖字符串解析，无法做条件过滤
3. **重复插入**：同一章节多次调用会重复

SQLite + auto-export MD 解决了所有问题。

---

## 数据流

```
子代理章节完成
    ↓
verify_chapter.py 验证
    ↓
post_chapter.py
    ↓
┌─────────────────────────────┐
│  tracking_db.py             │
│  写入 SQLite（原子操作）     │
│  - chapters 表               │
│  - character_arcs 表         │
│  - chronicle 表              │
│  - world_state 表            │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  export_md.py               │
│  自动导出所有 MD 文件        │
│  - 进度看板.md               │
│  - 剧情线追踪.md              │
│  - 编年史.md                  │
│  - 角色弧光追踪.md            │
└─────────────────────────────┘
    ↓
大纲/*.md（格式永远正确）
```

---

## 数据库 Schema

```sql
-- 章节表
CREATE TABLE chapters (
    id              INTEGER PRIMARY KEY,
    title           TEXT,
    words           INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'pending',
    core_event      TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色弧光表
CREATE TABLE character_arcs (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    arc_type        TEXT,
    start_state     TEXT,
    current_state   TEXT,
    current_chapter INTEGER DEFAULT 0,
    key_moments     TEXT DEFAULT '[]'  -- JSON 数组
);

-- 编年史表
CREATE TABLE chronicle (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER,
    time_label      TEXT,
    event           TEXT,
    chapter         INTEGER
);

-- 世界状态表
CREATE TABLE world_state (
    key             TEXT PRIMARY KEY,
    value           TEXT
);

-- 元数据表
CREATE TABLE meta (
    key             TEXT PRIMARY KEY,
    value           TEXT
);
```

---

## 脚本职责

| 脚本 | 职责 | 使用场景 |
|------|------|---------|
| `tracking_db.py` | SQLite CRUD 模块 | 被其他脚本调用 |
| `export_md.py` | 导出 MD 文件 | 被 post_chapter 调用 |
| `post_chapter.py` | 主入口 | **子代理必须调用** |
| `migrate_to_sqlite.py` | 迁移现有数据 | 一次性使用 |
| `verify_chapter.py` | 章节验证 | 子代理写完调用 |

### post_chapter.py 用法

```bash
python3 post_chapter.py <书名> <章节号> <字数> "<核心事件>" [章节文件路径]

# 示例
python3 post_chapter.py "某小说" 13 2956 "大比32强，主角击败对手"
```

### migrate_to_sqlite.py 用法

```bash
# 仅需执行一次（首次迁移或重建数据库）
python3 migrate_to_sqlite.py "某小说"
```

---

## 防重复机制

所有写入函数都有防重复检查：

```python
# chapters 表：ON CONFLICT(id) DO UPDATE
# chronicle 表：SELECT + INSERT（防重复）
# character_arcs 表：INSERT OR IGNORE
```

---

## 备份与恢复

```bash
# 备份数据库
cp .tracking/tracking.db .tracking/tracking.db.bak

# 恢复
cp .tracking/tracking.db.bak .tracking/tracking.db

# 重新导出 MD（从数据库重建）
python3 export_md.py "某小说"
```

---

## 验证命令

```bash
# 检查数据库
python3 -c "
import sys; sys.path.insert(0, 'scripts')
import tracking_db
db = tracking_db.get_db_path('某小说')
chs = tracking_db.get_all_chapters(db)
print(f'章节: {len([c for c in chs if c[\"status\"]==\"done\"])} 完成')
print(f'总字数: {sum(c[\"words\"] for c in chs)}')
print(f'角色弧光: {len(tracking_db.get_all_character_arcs(db))} 个')
print(f'编年史: {len(tracking_db.get_chronicle(db))} 条')
"

# 检查 MD 文件
grep "第X章" 大纲/进度看板.md
grep "第X章" 大纲/剧情线追踪.md
grep "第X章" 大纲/编年史.md
```

---

## 角色管理（易错点）

⚠️ **`tracking_db.py` 没有 `add_character()` 函数**。尝试导入会得到：
```
ImportError: cannot import name 'add_character' from 'scripts.tracking_db'
```

正确做法：用 `init_character_arcs()` 添加新角色到已有数据库。

**正确调用示例**：
```python
import sys; sys.path.insert(0, 'scripts')
from tracking_db import get_db_path, init_character_arcs

db = get_db_path('某小说')
arcs = [
    {'id': 'C002', 'name': '女主1', 'arc_type': '深化型',
     'start_state': '起点状态', 'current_state': '起点状态'},
    {'id': 'C004', 'name': '配角1', 'arc_type': '深化型',
     'start_state': '起点状态', 'current_state': '起点状态'},
]
init_character_arcs(db, arcs)
```

⚠️ **字段名是 `id`，不是 `char_id`**。用 `char_id` 会得到 `KeyError: 'id'`。

### 更新单角色状态（章节互动后）

```python
from tracking_db import touch_character, get_db_path
db = get_db_path('书名')
touch_character(db, 'C002', 15)  # C002这个角色在第15章有互动
```

---

## 迁移记录

| 日期 | 操作 |
|------|------|
| 2026-05-10 | 首次迁移：MD → SQLite |
| | 创建 tracking_db.py, export_md.py, migrate_to_sqlite.py |
| | 重写 post_chapter.py（基于 SQLite） |
| | SKILL.md 新增存储架构章节 |
| 2026-05-10 | 补充角色管理易错点（`add_character` 不存在，字段名是 `id` 不是 `char_id`） |