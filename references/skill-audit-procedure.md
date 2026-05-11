# 技能审计流程

> 每次对 novel-worldbuilder 做"全面检查"时，按此流程执行。审计发现的问题必须立即修复并推送。

## 审计执行顺序

### 第一轮：语法 + 导入
```bash
cd ~/.hermes/skills/creative/novel-worldbuilder
python3 -m py_compile scripts/*.py 2>&1
```
- 全部通过才进入下一轮
- 任一失败 = 阻断性问题，必须先修复

### 第二轮：路径一致性

路径变更（如 `~/hermes/novels/` → `~/novels/`）后，必须执行以下**全量扫描**，缺一不可：

```bash
# 扫描所有 Python 文件
grep -rn "旧路径" --include="*.py" .

# 扫描所有 Markdown 文件（含 references/、templates/）
grep -rn "旧路径" --include="*.md" .

# 扫描其他文本文件（.txt/.yaml/.json 等）
grep -rn "旧路径" --include="*.txt" --include="*.yaml" --include="*.yml" --include="*.json" .

# 扫描 git 日志（只读，确认无遗漏）
git log --oneline | grep "旧路径关键词"
```

**必须检查的文件类型**（易漏）：
- `references/` 下所有 .md（Bug案例/指南/协作策略）
- `templates/` 下的示例文件
- `.git/` 下的日志（只读，不用改）
- SKILL.md 中的命令示例和目录结构说明

### 第三轮：逻辑验证

| 检查项 | 命令 | 预期 |
|--------|------|------|
| 导出函数硬编码 | `grep -n "某旧书名\|卷一_铺垫\|卷二_对抗\|卷三_高潮" scripts/export_md.py` | 无输出 |
| scene_keywords 清空 | `grep -A5 "scene_keywords = {" scripts/check_transition.py` | 注释模板状态 |
| 模板结构保留 | init 后导出，进度看板含 `## 基本参数` | 有输出 |
| trim_utils 写文件 | `grep -n "open.*'w'" scripts/trim_utils.py` | 仅 auto_trim 中有 |

### 第四轮：功能测试

```bash
# 完整流程（新小说名，测试后删除）
rm -rf ~/novels/审计测试
python3 init_novel.py "审计测试" 80 2500 --主角 "测试主角"
python3 -c "
import sys; sys.path.insert(0,'scripts')
import tracking_db, export_md
db = tracking_db.get_db_path('审计测试')
tracking_db.insert_or_update_chapter(db, 1, '第1章', 300, 'done', '测试')
export_md.export_all('审计测试')
"
grep "## 基本参数" 大纲/进度看板.md
rm -rf ~/novels/审计测试
```

### 第五轮：引用完整性

```bash
# 参考文件数量核查
echo "=== SKILL.md 引用 ===" && grep "^-\|\.md\`" SKILL.md | wc -l
echo "=== 实际 references/ ===" && ls references/*.md | wc -l
echo "=== 实际 scripts/ ===" && ls scripts/*.py | wc -l

# 两者必须一致
```

## 常见遗漏点

1. **Bug案例文档**（`bugcase-*.md`、`truncation-disaster.md`）里的路径示例
2. **协作策略文档**（`collaboration-strategy.md`）里的子代理工作目录
3. **技术陷阱文档**（`technical-pitfalls.md`）里的代码示例
4. SKILL.md 末尾的 `*最后更新：...` 变更日志
5. `init_tracking.py` 错误提示里的路径

## Bug 分类参考

历次全面检查发现的 Bug 分类模式：

| 类别 | 典型问题 | 检查方式 |
|------|----------|----------|
| 硬编码 | 书名/卷名/角色名写死 | grep 搜索旧小说名 |
| 逻辑错误 | 死代码/残留变量/错误判断 | 代码审查 |
| 模板覆盖 | 导出函数覆盖模板结构 | 功能测试 + head 检查 |
| 路径错误 | 引用路径与实际不符 | 全量 grep 扫描 |
| 引用过时 | 参考文档示例与实际代码脱节 | 引用完整性检查 |
| 语义错误 | 函数行为与文档描述不符 | dry_run/dry_run 等参数语义核查 |

## 修复推送标准

每次审计修复后：
```bash
git add -A
git commit -m "审计修复：[一句话描述]"
git push origin main
```

commit message 必须反映**发现问题的方式**（如"全量路径扫描"），而非仅"修复了XXX"。