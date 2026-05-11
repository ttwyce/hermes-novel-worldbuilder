# SQLite 存储架构详解

## 概述

```
写入路径（post_chapter.py）
    │
    ▼
tracking_db.py → SQLite（唯一真相来源）
    │
    ├── chapters       表    ← 章节数据
    ├── character_arcs 表   ← 角色弧光（支持自动注册）
    ├── chronicle      表   ← 编年史条目
    ├── plot_hooks     表   ← 伏笔（active/resolved）
    ├── world_state   表   ← 世界状态键值对
    └── meta          表   ← 元数据（总章数/每章字数）
    │
    ▼
export_md.py → 6 个 Markdown（人可读）
    ├── 进度看板.md     ← 章节进度表 + 世界状态摘要
    ├── 剧情线追踪.md   ← 每章核心事件
    ├── 编年史.md      ← 时间线事件
    ├── 角色弧光追踪.md ← 角色状态变化+转折点
    ├── 伏笔钩子追踪.md ← 活跃+已解伏笔
    └── 世界状态.md     ← 所有世界状态键值对
```

---

## 数据库 Schema（6张表）

```sql
-- 章节表
CREATE TABLE chapters (
    id              INTEGER PRIMARY KEY,
    title           TEXT,
    words           INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'pending',  -- pending / done
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

-- 伏笔钩子表
CREATE TABLE plot_hooks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id      INTEGER,
    plot            TEXT,
    status          TEXT DEFAULT 'active',   -- active / resolved
    resolved_chapter INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

| 脚本 | 职责 |
|------|------|
| `init_tracking.py` | 初始化新小说数据库，添加默认主角 |
| `tracking_db.py` | SQLite CRUD 模块 |
| `post_chapter.py` | 主入口：章节+角色检测(含自动注册)+伏笔+世界状态+导出+验证 |
| `export_md.py` | 导出全部 6 个 Markdown 文件 |
| `get_context.py` | 从数据库生成章节上下文（含世界状态/伏笔/角色/衔接提示） |
| `verify_chapter.py` | 章节字数验证 |
| `check_transition.py` | 章节衔接检查 |

### post_chapter.py 完整用法

```bash
python3 post_chapter.py <书名> <章节号> <字数> "<核心事件>" [章节文件] [伏笔] --world-state "境界:炼气期,地点:青云峰"

# 示例
python3 post_chapter.py "某小说" 5 3120 "大比32强，主角晋级" --world-state "主角境界:炼气中期,当前地点:天梯"
```

### 伏笔追加

```bash
# 在事件参数后加伏笔参数
python3 post_chapter.py "某小说" 5 3120 "大比结束" "神秘宝物线索"
```

---

## 防重复机制

| 表 | 机制 |
|----|------|
| `chapters` | `ON CONFLICT(id) DO UPDATE` |
| `chronicle` | `SELECT` 检查后 `INSERT`（防重复） |
| `character_arcs` | `INSERT OR IGNORE` |
| `world_state` | `ON CONFLICT(key) DO UPDATE` |
| `meta` | `ON CONFLICT(key) DO UPDATE` |
| `plot_hooks` | 自增 ID，无需去重（同一伏笔可多次添加，状态不同） |

---

## 角色自动注册

**功能**：`post_chapter.py` 的 `detect_and_update_characters()` 会自动检测章节中出现的未注册角色并写入数据库。

**检测方式**：扫描对话引导语（`X道`/`X说`/`X问` 等）前的 2-4 字作为角色名。

**新角色默认值**：
- `arc_type`: `待设定`
- `start_state`: `待设定`
- `current_state`: `待设定`
- `current_chapter`: 首次出场章节

**ID 分配**：自动顺序分配 `A01 → A02 → ... A99 → B01 → ...`

**⚠️ 已知局限**：引导语和名字之间有其他字时会误匹配。例如：
- `陆天笑着说：...` → 注册为 `陆天笑着`（误）
- `旁边一个女孩站起来说道` → 注册为 `孩站起来`（误）

**使用建议**：写完章后检查 `大纲/角色弧光追踪.md` 的弧光定义表，修正误注册角色的名字并补充弧光类型。

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
# 检查数据库内容
python3 -c "
import sys; sys.path.insert(0, 'scripts')
import tracking_db
db = tracking_db.get_db_path('某小说')
chs = tracking_db.get_all_chapters(db)
arcs = tracking_db.get_all_character_arcs(db)
plots = tracking_db.get_active_plots(db)
ws = tracking_db.get_all_world_state(db)
print(f'章节: {len([c for c in chs if c[\"status\"]==\"done\"])} 完成')
print(f'总字数: {sum(c[\"words\"] for c in chs)}')
print(f'角色: {len(arcs)} 个')
print(f'活跃伏笔: {len(plots)} 个')
print(f'世界状态: {ws}')
"
```

---

## 迁移记录

| 日期 | 操作 |
|------|------|
| 2026-05-10 | 首次迁移：MD → SQLite |
| | 创建 tracking_db.py, export_md.py, migrate_to_sqlite.py |
| | 重写 post_chapter.py（基于 SQLite） |
| 2026-05-11 | 新增伏笔钩子表 `plot_hooks` |
| | 新增世界状态表 `world_state` |
| | export_md.py 新增 `伏笔钩子追踪.md` 和 `世界状态.md` |
| | post_chapter.py 新增 `--world-state` 参数 |
| | get_context.py 新增世界状态显示 |
| | 检测逻辑从「需预注册」改为「自动注册+手动修正」 |