# Bug Case: 导出函数硬编码小说名（已修复）

## 发现时间
2026-05-11 | 检查 novel-worldbuilder 技能完整性时发现

## 问题描述
`export_md.py` 中两个导出函数硬编码了"嘴强剑仙"的小说特定内容：

```python
# export_progress_board() 原始代码
f"## 嘴强剑仙：我的吐槽能杀人"   # ← 硬编码书名
"**总目标**：150章 / 45万字"      # ← 硬编码目标

# export_chronicle() 原始代码  
"## 嘴强剑仙：我的吐槽能杀人"
"### 入学前"
"| 陆天3岁 | 父亲陆大山散修..."   # ← 硬编码示例编年史
```

## 影响
- 任何新小说（如"时光缓缓"）运行 `export_md.export_all()` 后
- 进度看板显示书名为"嘴强剑仙"、目标为150章45万字
- 编年史混入陆天3岁/13岁等旧小说数据
- **新小说追踪文件被污染**

## 根因
这是典型的"快速原型污染"：旧小说数据先写好做占位符，后来忘记替换为通用逻辑。

## 修复方式
```python
# export_progress_board() 修复后
def export_progress_board(db_path: str, out_path: str, book_name: str = None) -> None:
    if book_name is None:
        book_name = "小说"
    chapters = tracking_db.get_all_chapters(db_path)
    total = len(chapters) or 150
    # 书名和目标全部动态生成
```

## 铁律（防止重蹈）
**导出函数严禁包含任何小说特定数据的硬编码 fallback。** 所有内容必须：
1. 从数据库读取（chapters、character_arcs 等）
2. 或通过函数参数传入
3. 无默认值时用占位符字符串（"小说"），不能写死具体内容

## 检查清单
修复导出函数后，用另一个小说名做完整流程测试：
```bash
python3 init_tracking.py "测试新小说" --主角 "测试主角"
# 模拟写章节
python3 post_chapter.py "测试新小说" 1 3000 "测试事件"
# 检查导出结果 - 书名必须是"测试新小说"，不能是"嘴强剑仙"
head -5 大纲/进度看板.md
```