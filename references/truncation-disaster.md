# 截断标记事故 · 完整复盘

> 2025-05-10 | 事故等级：严重 | 影响：第21-30章共10章大量不达标，需重写

---

## 事故经过

1. 写章节时使用了 `...[truncated]` / `...[未完]` 等占位标记
2. 以为 `write_file` 会自动补全完整内容
3. 实际上 `write_file` 只写入给它的确切文本，不做任何处理
4. 结果：写入的章节只有200-300行骨架而非3000字完整内容
5. 文件已保存，无法通过重新写入恢复（无自动恢复手段）

---

## 根因

`write_file` 工具的行为：**只写入你给它的确切文本字符串，不会自动补全、不会处理占位符、不会等待后续内容。**

"先占位后补写"是根本不存在的流程。

---

## 正确流程

```
写章节前
  → 在脑中/草稿中组织好完整内容（≥设定值×80%）
  → 一次性 write_file 写入完整字符串

写章节后（立即执行）
  → python3 scripts/verify_chapter.py <文件> <设定字数>
  → 返回0=合格 → 写下一章
  → 返回1=不合格 → 立即扩充 → 重新验证 → 合格后再写下一章
```

---

## 验证命令参考

```bash
# 验证单个章节（设定3000字/章）
python3 ~/.hermes/skills/creative/novel-worldbuilder/scripts/verify_chapter.py \
  ~/novels/<书名>/正文/卷X/第N章.md 3000

# 批量验证（假设每章3000字，卷二目录）
for f in ~/novels/<书名>/正文/卷二/第*.md; do
  echo "=== $f ==="
  python3 ~/.hermes/skills/creative/novel-worldbuilder/scripts/verify_chapter.py "$f" 3000
done
```

---

## 修复案例

第21章修复：
- 原始：230行骨架版（~8557字节）
- 补写：一次性写入完整4598字版本
- 验证：`python3 verify_chapter.py 第21章.md 3000` → ✅

---

## 预防检查清单

每章写完后立即执行：
- [ ] 无截断标记（`...[truncated]` / `...待续` / `...未完`）
- [ ] `verify_chapter.py` 返回 0
- [ ] wc -m 字符数 ≥ 设定值×80%