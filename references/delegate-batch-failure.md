# 子代理批量生成失败：根因分析

## 事件回顾

2025-05-09，创建《修仙从无系统开始》时，用 `delegate_task` 启动 3 个子代理同时生成全部设定文件，全部超时失败：
- Subagent 0: timeout (600s)
- Subagent 1: timeout (600s)
- Subagent 2: interrupted

## 根因

novel-worldbuilder 技能要求一次性生成的文件总量约 5-8 万字（设定集 2 万字 + 12 个人物档案 × 500 字 + 大纲/世界观/势力等）。API 生成这么多内容本身没问题，但：

1. **多子代理并行**：每个子代理独立调用 API，共同竞争上下文
2. **内容互相引用**：角色档案依赖角色注册表，势力依赖世界观设定
3. **生成时间不确定**：单次 API 调用生成数千字需要几十秒，总量大时必然超时
4. **无断点续传**：超时后没有任何文件被写入，全部白费

## 绝对禁止的做法

```python
# 错误示范 —— 不要这样用 delegate_task
delegate_task(tasks=[
    {"goal": "生成设定集", ...},
    {"goal": "生成势力和人物", ...},
    {"goal": "生成大纲", ...},
])
```

## 正确的做法：主 Agent 逐文件生成

```
用户确认书名
    ↓
init_novel.py：秒建目录骨架（纯 Python，无 AI 调用）
    ↓
主 Agent 生成文件①（设定集.md）
    ↓ write_file
主 Agent 生成文件②（世界观/世界观设定.md）
    ↓ write_file
主 Agent 生成文件③（世界观/时代背景.md）
    ↓ write_file
… 重复，逐文件进行，每个文件一次 AI 调用
    ↓
所有 19 个文件生成完毕，向用户报告
```

**关键点：**
- 主 Agent 在同一上下文中逐文件生成，已生成内容可被引用
- 每个文件单独一次 AI 调用，不会超时（单文件通常 1-5 秒）
- init 脚本只建骨架 + 追踪文件，不涉及内容生成，零超时

---

## 环境注意事项

### `python` vs `python3`

**当前环境只有 `python3`，没有 `python` 别名。**

调用 `init_novel.py` 时必须用：
```bash
python3 /path/to/scripts/init_novel.py "书名"
# ❌ python /path/to/... 会报错：command not found
```

### 工作目录路径

**正确路径：** `/home/admin/hermes/novels`

常见错误：
```bash
# ❌ 错误：把 admin 和 hermes 之间的 / 漏掉了
cd /home/admin.hermes/novels

# ✅ 正确
cd /home/admin/hermes/novels
python3 /home/admin/.hermes/skills/creative/novel-worldbuilder/scripts/init_novel.py "书名"
```