# 自动注册 Bug 调查与修复日志

## 2026-05-11 测试发现

### Bug 1：自动注册 false positive（严重）

**现象**：运行 `post_chapter.py` 后，数据库出现 9 个假角色：`他嘀咕`、`主角小声`、`是不是有`、`同学围着`、`我也不知`、`但不知`、`给出正确`、`苏晴没有`、`在老师提`。

**根因**：正则 `[\u4e00-\u9fa5]{2,4}` + 对话引导语匹配的是"紧跟名字后的字"，而非独立的角色名。

**复现案例**：
```
文本："主角小声问苏晴道："
正则匹配：(主角) + 小声 = "主角小声"（假）
          + 问 = 对话引导语

文本："他嘀咕道："
正则匹配：(嘀咕) + 道 = "嘀咕"（假）

文本："苏晴没有回答。"
正则匹配：(没有) + 回答 = "没有"（假）
```

**正则结构解析**：
```python
r'([\u4e00-\u9fa5]{2,4})'  # 捕获2-4个汉字
r'(?:道|说|问|答|...)'       # 紧跟对话引导语
```
问题：正则要求的是"紧跟引导语前的2-4字"，而不是"独立的名字"。"小声问"和"没有回答"都满足这个模式，但"小声"和"没有"都不是人名。

**excluded_words 缓解效果有限**：虽然排除了 `笑着/低声/悄悄` 等模式，但仍无法穷举所有"假名+引导语"组合。

**架构级结论**：纯正则 NER（命名实体识别）有根本性局限。中文角色名检测需要：
- 方案A：接驳专业中文 NER 库（如 `jieba` 的词性标注、`thulac`）
- 方案B：只从预注册角色列表中检测（不自动发现新人名）
- 方案C：极保守策略——要求检测到的"名字"之前有明确的标点/段首/引号边界

**当前最佳缓解**：将 excluded_words 补充到最常见误匹配模式，但无法根除。

---

### Bug 2：find_chapter_file 内部调用返回 None（严重）

**现象**：直接调用 `find_chapter_file(novel_root, 1)` 返回正确路径，但在 `post_chapter.py` 内部调用时返回 `None`，导致角色检测和伏笔保存全部跳过。

**调查过程**：
```python
# 直接调用 → 正常
post_chapter.find_chapter_file(novel_root, 1)
# → /home/admin/novels/测试小说/正文/卷一_铺垫与启程/第1章.md ✅

# 手动模拟 post_chapter 参数 → 正常
post_chapter.find_chapter_file(novel_root, 1)  # novel_root from tracking_db ✅
```

但在 `post_chapter.py main()` 实际运行时（第1次手动传路径前那次）不工作。可能原因：
1. `tracking_db.find_novel_root('测试小说')` 在某些调用路径下返回异常路径
2. `os.walk` 有路径歧义（同名文件/目录）

**临时方案**：始终显式传入章节路径 `--world-state` 和伏笔参数。

**待调查**：`find_novel_root` 的 `"测试小说" in chapter_dir` 模糊匹配可能在目录名包含目标书名时产生歧义。

---

### Bug 3：get_context 用子串检测角色

`name in text` 会在 "苏晴没有" 中检测到"苏晴"，产生 false positive。真实人名需验证词边界（段首/标点/引号/空格）。

**当前状态**：不影响功能（因为误检测成已注册角色不会自动注册新人），但会在 `get_context` 中错误显示角色出场信息。

---

### Bug 4：伏笔重复（低）

同一章运行两次 `post_chapter`，`add_plot_hook` 不检查重复，导致同一条伏笔出现多次。需在 `add_plot_hook` 入口加去重逻辑。

---

## 已验证的 Workaround

1. **手动传章节路径**：确保 `post_chapter.py` 调用时传入完整章节文件路径，避免 `find_chapter_file` 找不到文件
2. **写完章后立即检查**：`大纲/角色弧光追踪.md` 中删除误注册角色（A05-A13）并补充真实角色弧光类型
3. **RAG 依赖缺失**：静默跳过（符合设计）

---

## ✅ P2 已修复（2026-05-11）：add_plot_hook 去重

**文件**：`scripts/tracking_db.py` → `add_plot_hook()` 函数

**修复方式**：写入前检查 `chapter_id + plot` 是否已存在活跃记录，存在则返回已有ID，不重复插入。

**验证**：
```bash
python3 -c "
import sys, os, tempfile, shutil
sys.path.insert(0, 'scripts')
import tracking_db
tmp = tempfile.mkdtemp()
db = os.path.join(tmp, 't.db')
tracking_db.init_db(db)
tracking_db.insert_or_update_chapter(db, 1, '第1章', 3000, 'done', 'evt')
p1 = tracking_db.add_plot_hook(db, 1, '身世之谜')
p2 = tracking_db.add_plot_hook(db, 1, '身世之谜')
assert p1 == p2, f'去重失败！p1={p1}, p2={p2}'
print(f'去重成功：p1=p2={p1}')
shutil.rmtree(tmp)
"
```

---

## 待修复项

| 优先级 | 问题 | 方案 |
|--------|------|------|
| P0 | 自动注册 false positive | 将 regex 改为必须前边界，或改用预注册列表检测 |
| P1 | find_chapter_file 不稳定 | 加日志排查实际返回值 |