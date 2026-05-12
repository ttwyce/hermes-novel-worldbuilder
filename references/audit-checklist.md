# 全面检查清单 · novel-worldbuilder

> 每次对技能做"全面检查"时执行此清单。全部通过才能推送。

---

## 必检项（共5类）

### 1. 旧小说名残留（全仓库扫描）

**目标**：所有 .py / .md / .txt 文件中，**除** `migrate_to_sqlite.py`、`bugcase-*.md`、`truncation-disaster.md` 外，不得包含任何旧小说名。

**旧小说名清单**（已删除的书/角色，不含当前项目）：
```
嘴强剑仙 / 陆天 / 叶琳 / 苏清雪 / 赵婉清 / 陈朵朵 / 摆烂修仙 / 李明辉 / 陈浩 / 周天成 / 林晓
```

> ⚠️ **当前项目「时光缓缓」/ 陆时晏 / 林诺 / 周窈 / 陈绥 不是旧书名。**

**扫描命令**：
```bash
cd ~/.hermes/skills/creative/novel-worldbuilder
grep -rEl "嘴强剑仙|陆天|叶琳|苏清雪|赵婉清|陈朵朵|摆烂修仙|李明辉|陈浩|周天成|林晓" \
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
| 🟡 中 | `SKILL.md` 示例命令含具体书名（如RAG输出示例） | `grep "时光缓缓\|嘴强剑仙\|赵婉清\|陈朵朵\|陆天" SKILL.md` |
| 🟡 中 | `references/` 下 Bug 案例文档未清理旧名 | `grep "嘴强剑仙" references/*.md` |
| 🟡 中 | **两轮审计原则**：第一轮查.py脚本问题，第二轮查.md文档残留 | 文档（.md）常用真实角色名做示例，第一轮扫描.py时可能漏过 |
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

## 全面检查发现的 Bug 模式（2026-05-11 本次新增）

本次全面检查覆盖 12 个脚本，发现以下可复用的 Bug 模式：

### B-1：字段重复（输出格式错误）

**文件**：export_md.py
**问题**：`export_arc_tracking()` 中 `current_state` 字段在循环内出现两次（`当前阶段` 和 `当前心理状态` 都引用同一字段）
**检测方式**：搜索同一函数内是否有重复字段引用
**修复**：删除重复行，保留语义最准确的那个

### B-2：边界条件导致负数索引

**文件**：rag_indexer.py
**问题**：`overlap` 逻辑中若 `len(current) <= overlap`，`current[-overlap:]` 返回空串或错误前缀
**检测方式**：`py_compile` 不报错，需人工逻辑审查；写测试用例验证 overlap 值大于 current 长度的情况
**修复**：`effective_overlap = min(overlap, len(current) // 2)` 确保 overlap 有上限

### B-3：未使用函数定义（死代码）

**文件**：check_transition.py
**问题**：`get_chapter_end()` 定义后从未被调用（`main()` 调用了但后来移除调用处却漏删函数）
**检测方式**：grep 函数名，检查出现次数是否只有定义处一处
**修复**：删除整函数定义；若函数仍有参考价值则保留但修复调用链

### B-4：未使用参数

**文件**：check_transition.py
**问题**：`generate_report()` 接收 `curr_chapter_end` 参数但函数体内从未使用
**检测方式**：检查 `generate_report` 调用处传入的参数数量与签名是否匹配；审查函数体内参数引用
**修复**：从签名和调用处同时移除该参数

### B-5：参数解析逻辑含糊

**文件**：trim_utils.py
**问题**：`--target` 参数位置检测使用 `int(sys.argv[3]) if ... and sys.argv[2] != '--target'`，逻辑容易误判
**检测方式**：读参数解析代码，验证每个 argv 位置组合是否都能被正确处理
**修复**：简化为 `默认值 + if '--target' in argv: idx = argv.index(...); target = int(argv[idx+1])`

### B-6：误导性 API（参数无效）

**文件**：trim_utils.py
**问题**：`trim_to_target(filepath, target, dry_run=True)` 的 `dry_run` 参数在函数体内从无分支行为，无论传什么都只分析不修改
**检测方式**：搜索 `dry_run` 在函数体内的所有引用，确认是否有 `if dry_run` 分支
**修复**：移除无效参数；文档中明确说明"此函数只分析，实际修改在 auto_trim 中"

### B-7：循环内重复 DB 查询（N+1 问题）

**文件**：post_chapter.py
**问题**：自动注册循环内每次调用 `get_all_character_arcs(db_path)`，N 个新角色 = N 次数据库查询
**检测方式**：搜索循环内是否有 SQL 查询或 `get_all_*` 调用
**修复**：循环外预查一次，用本地列表追踪已分配 ID

### B-8：重叠分支条件导致分支无效

**文件**：trim_utils.py
**问题**：`trim` 子命令中 `target = int(sys.argv[3])` 和 `if '--target' in sys.argv` 重叠，后面的 `if` 永远执行不到（前面的赋值总是先运行）
**检测方式**：逐行审查 if 分支，确认每个分支在逻辑上是否可达
**修复**：合并简化逻辑，移除不可达分支

### B-9：参数有默认值但调用处从不使用

**文件**：export_md.py
**问题**：`export_world_state(..., book_name: str = None)` 有默认值，但调用处 `export_all()` 内总显式传值
**影响**：低（不影响功能，仅代码冗余）
**检测方式**：grep 搜函数定义中的默认参数值，检查所有调用处是否都显式传参

### 快速扫描命令（检测上述 B 类问题）

```bash
# B-3: 检测未使用函数（定义处只出现一次）
for f in scripts/*.py; do
  for func in $(grep -Po '^def \K\w+' "$f"); do
    count=$(grep -c "$func" "$f")
    [[ $count -eq 1 ]] && echo "DEAD: $f::$func"
  done
done

# B-4: 检测调用处参数数量与签名是否匹配
# （需人工审查 generate_report 等函数的调用链）

# B-6: 检测 dry_run 参数是否在函数内有分支行为
grep -n "dry_run" scripts/trim_utils.py

# B-7: 检测循环内是否有 get_all_* 调用
awk '/^def detect_and_update/,/^def [a-z]/' scripts/post_chapter.py | grep -n "get_all_"

# B-8: trim 子命令参数解析路径可达性审查
grep -A10 "command == 'trim'" scripts/trim_utils.py
```

*本清单为通用审计标准。审计执行顺序和流程见 `references/skill-audit-procedure.md`*