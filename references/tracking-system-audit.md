# SQLite 跟踪系统审计方法论

## 核心原则：每张表必须走过三道关

```
写入路径（谁往表里写数据？）
    ↓
读取路径（谁从表里查数据？）
    ↓
导出路径（表数据是否导出了外部 MD 文件？）
```

**任一环节缺失 = 功能不完整**。表存在 ≠ 功能可用。

---

## 审计检查清单

### 1. 列出所有数据库表

```python
import sys; sys.path.insert(0, 'scripts')
import tracking_db, sqlite3
db = tracking_db.get_db_path('书名')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("表:", tables)
```

### 2. 对每张表追踪三路径

| 表名 | 写入脚本 | 读取脚本 | 导出到MD？ |
|------|---------|---------|-----------|
| chapters | post_chapter.py | get_context.py, export_md.py | ✅ 剧情线追踪.md |
| character_arcs | post_chapter.py, init_tracking.py | get_context.py, export_md.py | ✅ 角色弧光追踪.md |
| chronicle | post_chapter.py | export_md.py | ✅ 编年史.md |
| world_state | **无任何脚本调用** | get_context.py | ❌ → 新增 export_world_state() ✅ |
| plot_hooks | post_chapter.py | get_context.py | ❌ → 新增 export_plot_hooks() ✅ |
| meta | init_tracking.py | export_md.py | ✅（进度看板读取planned_chapters）|

### 3. 验证导出文件实际存在

```bash
ls 大纲/*.md
# 完整列表应为6个：
# 进度看板.md / 剧情线追踪.md / 编年史.md
# 角色弧光追踪.md / 伏笔钩子追踪.md / 世界状态.md
```

### 4. 验证世界状态写入机制

```bash
# 检查 set_world_state 是否被任何脚本调用
grep -rn "set_world_state" scripts/
# 期望：post_chapter.py 有调用（用 --world-state 参数）
# 实际历史：无！这是死代码
```

### 5. 验证伏笔钩子导出

```bash
# 检查 export_md.py 是否有导出 plot_hooks 的函数
grep -n "plot_hook\|export_plot" scripts/export_md.py
# 期望：有 export_plot_hooks() 函数
# 实际历史：无！这是功能缺口
```

---

## 常见缺陷模式

### 死代码表
表定义了但从未被写入。检查方法：
```bash
grep -rn "INSERT.*表名\|set_表名" scripts/
```

### 有去无回（能写不能读）
数据写入了但没有消费方。比如 `plot_hooks` 写入后，`export_md.py` 没有对应导出函数。

### 有读无导（能读不能导出）
数据库里能查到数据，但 `export_md.py` 没有对应的导出函数写入 MD 文件。`get_context.py` 能用不等于 MD 文件里有。

### 导出函数变量 Bug
导出时用 `lines` 生成内容但用 `lines_text` 写入，或 `marker` 在 `else` 分支未定义。运行 `python3 -m py_compile scripts/export_md.py` 无法发现，**必须实际执行集成测试**验证。

---

## 集成测试模板

```python
import sys, os, shutil, tempfile
sys.path.insert(0, 'scripts')

with tempfile.TemporaryDirectory() as tmpdir:
    book_dir = os.path.join(tmpdir, '审计测试')
    os.makedirs(os.path.join(book_dir, '大纲'))
    
    import tracking_db
    db = os.path.join(book_dir, '.tracking/tracking.db')
    tracking_db.init_db(db)
    
    # 写入测试数据
    tracking_db.set_world_state(db, '测试键', '测试值')
    hook_id = tracking_db.add_plot_hook(db, 1, '测试伏笔')
    
    # 执行导出
    import export_md
    os.makedirs(os.path.expanduser('~/novels/审计测试/大纲'), exist_ok=True)
    shutil.copytree(book_dir, os.path.expanduser('~/novels/审计测试'), dirs_exist_ok=True)
    export_md.export_all('审计测试')
    
    # 验证
    for fname in ['世界状态.md', '伏笔钩子追踪.md']:
        fpath = os.path.join(os.path.expanduser('~/novels/审计测试'), '大纲', fname)
        assert os.path.exists(fpath), f"{fname} 未导出！"
    
    shutil.rmtree(os.path.expanduser('~/novels/审计测试'))
    print("✅ 三链路贯通测试通过")
```

---

## 修复优先级

1. **P0**：写入路径缺失 → 功能完全不可用，先修写入
2. **P1**：读取路径缺失 → 数据孤岛，先修读取
3. **P2**：导出路径缺失 → 人工看不到，先修导出（如果人工需要读MD）

*最后更新：2026-05-11*