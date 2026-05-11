# 全面检查清单 · novel-worldbuilder

> 每次对技能做"全面检查"时执行此清单。全部通过才能推送。

---

## 必检项（共5类）

### 1. 旧小说名残留（全仓库扫描）

**目标**：所有 .py / .md / .txt 文件中，**除** `migrate_to_sqlite.py`、`bugcase-*.md`、`truncation-disaster.md` 外，不得包含任何旧小说名。

**旧小说名清单**：
```
嘴强剑仙 / 陆天 / 叶琳 / 苏清雪 / 赵婉清 / 陈朵朵 / 摆烂修仙 / 李明辉 / 陈浩 / 周天成 / 林晓 / 时光缓缓 / 陆时晏 / 林诺 / 周窈 / 陈绥
```

**扫描命令**：
```bash
cd ~/.hermes/skills/creative/novel-worldbuilder
grep -rEl "嘴强剑仙|陆天|叶琳|苏清雪|赵婉清|陈朵朵|摆烂修仙|李明辉|陈浩|周天成|林晓|时光缓缓|陆时晏|林诺" \
  --include="*.py" --include="*.md" --include="*.txt" . | \
  grep -v -E "(bugcase-|truncation-|migrate_to_sqlite)" | \
  grep -v ".git"
# 预期：无输出
```

---

### 2. 路径一致性（当前标准：`~/novels/`）

**目标**：代码文件和文档中，小说根目录必须全部引用 `~/novels/`，不得残留 `~/hermes/novels/`。

**扫描命令**：
```bash
grep -rn "hermes/novels\|hermes\\\\novels" --include="*.py" --include="*.md" .
# 预期：无输出（除 SKILL.md 日期行记录变更历史）

# 验证 scripts/ 中 expanduser 路径
grep -n "expanduser" scripts/*.py
# 预期：全部为 "~/novels"
```

**必须检查的代码位置**（易漏）：
- `init_novel.py` — `base_dir`
- `tracking_db.py` — `find_novel_root()` 和 `get_db_path()`
- `init_tracking.py` — 错误提示文字
- `get_context.py` — 错误提示文字

---

### 3. 硬编码书名 / 卷名扫描

**目标**：代码文件中不得硬编码任何具体小说名、卷名。

**扫描命令**：
```bash
# export_md.py 不应有具体书名
grep -n "某旧书名\|嘴强剑仙\|时光缓缓" scripts/export_md.py
# 预期：无输出

# scene_keywords 模板状态
grep -A5 "scene_keywords = {" scripts/check_transition.py
# 预期：全部为注释模板（无具体地名）
```

---

### 4. 功能测试（init → post → export）

```bash
rm -rf ~/novels/审计测试
python3 scripts/init_novel.py "审计测试" 80 3000 --主角 "测试主角"
python3 -c "
import sys; sys.path.insert(0,'scripts')
import tracking_db, export_md
db = tracking_db.get_db_path('审计测试')
tracking_db.insert_or_update_chapter(db, 1, '第1章', 3000, 'done', '测试章节')
export_md.export_all('审计测试')
"
# 验证
grep "## 基本参数" ~/novels/审计测试/大纲/进度看板.md  # 有输出 = 模板保留
grep "审计测试" ~/novels/审计测试/大纲/进度看板.md    # 书名正确
rm -rf ~/novels/审计测试
```

**验收标准**：
- ✅ 目录创建在 `~/novels/` 而非 `~/hermes/novels/`
- ✅ 进度看板含 `## 基本参数`（模板结构保留）
- ✅ 书名为"审计测试"（非硬编码旧名）
- ✅ 总目标 80章/24万字（从 meta 表读取）

---

### 5. 脚本语法验证

```bash
python3 -m py_compile scripts/*.py 2>&1
# 预期：全部通过
```

---

## 常见遗漏点（按优先级）

| 优先级 | 遗漏点 | 检查方式 |
|--------|--------|----------|
| 🔴 高 | `check_transition.py` 示例写死书名 | `grep "时光缓缓\|嘴强剑仙" scripts/check_transition.py` |
| 🔴 高 | `tracking_db.py` 含 CHARACTER_IDS 硬编码 | `grep "陆天\|叶琳" scripts/tracking_db.py` |
| 🔴 高 | `init_tracking.py` 错误提示含旧路径 | `grep "hermes/novels" scripts/init_tracking.py` |
| 🟡 中 | `SKILL.md` 示例命令含具体书名 | `grep "时光缓缓\|嘴强剑仙" SKILL.md` |
| 🟡 中 | `references/` 下 Bug 案例文档未清理旧名 | `grep "嘴强剑仙" references/*.md` |
| 🟡 中 | `writing-style-guide.md` 只有单一风格 | 检查是否覆盖多种风格 |
| 🟢 低 | `SKILL.md` trim_utils 条目格式错误（表格语法滥用） | 检查是否为 `\| ` 开头非表格行 |
| 🟢 低 | `SKILL.md` 参考文件数量与实际不符 | `ls references/*.md \| wc -l` |

---

## Bug 分类模式速查

| 类别 | 典型问题 | 典型信号 |
|------|----------|----------|
| 硬编码 | 书名/卷名/角色名写死代码中 | grep 搜旧小说名有输出 |
| 路径错误 | 引用路径与实际目录不符 | init 后目录不在预期位置 |
| 模板覆盖 | 导出函数覆盖用户自定义模板 | 导出后 `## 基本参数` 区块消失 |
| 残留死代码 | 未使用常量/函数未删除 | grep 搜函数名仅在定义处出现 |
| 引用过时 | 文档示例与实际代码脱节 | 文档命令跑不通 |
| 语义错误 | 函数行为与文档描述不符 | `dry_run=False` 但不修改文件 |

---

*本清单为通用审计标准。审计执行顺序和流程见 `references/skill-audit-procedure.md`*