# Bug Case: 导出函数硬编码小说名（已修复）

> 2026-05-11 第一次检查发现并修复  
> 2026-05-11 第二次检查补充：export_tracking 硬编码 + 进度看板总目标错误

---

## 问题一：export_md.py 多处硬编码（第一次检查）

### export_progress_board()

```python
# 原始代码
f"## 嘴强剑仙：我的吐槽能杀人"   # ← 硬编码书名
"**总目标**：150章 / 45万字"      # ← 硬编码目标（章数和每章字数都写死）
```

### export_chronicle()

```python
# 原始代码
"## 嘴强剑仙：我的吐槽能杀人"
"### 入学前"
"| 陆天3岁 | 父亲陆大山散修，母亲凡人 | - |"   # ← 硬编码示例编年史
```

### export_tracking()（第二次检查发现）

```python
# 原始代码
"## 卷一：铺垫与启程"   # ← 硬编码卷名
```

---

## 影响

任何新小说（如"时光缓缓"）运行 `export_md.export_all()` 后：

- 进度看板显示"嘴强剑仙"而非正确书名
- 总目标永远是"150章/45万字"（无论实际计划）
- 编年史混入陆天/叶琳等旧小说数据
- 剧情线追踪显示"卷一：铺垫与启程"（而非小说名）

---

## 修复方案

### 修复1：book_name 参数穿透

```python
def export_progress_board(db_path, out_path, book_name=None):
    # 从参数或meta表读取
    planned = tracking_db.get_meta(db_path, 'planned_chapters')
    total = int(planned) if planned else len(chapters)

def export_chronicle(db_path, out_path, book_name=None):
    # 移除所有硬编码示例，从数据库读取
```

### 修复2：进度看板总目标从 meta 表读取

根因：数据库只有已完成章节，`len(chapters)` 得到已完成数而非计划数。

```python
# tracking_db.py 新增
def set_meta(db_path, key, value): ...
def get_meta(db_path, key): ...

# init_tracking() 时存储计划参数
tracking_db.set_meta(db_path, 'planned_chapters', str(planned_chapters))
tracking_db.set_meta(db_path, 'chapter_word_count', str(chapter_word_count))

# export_progress_board() 优先读 meta
planned = tracking_db.get_meta(db_path, 'planned_chapters')
total = int(planned) if planned else len(chapters)
```

---

## 铁律

**导出函数严禁包含任何小说特定数据的硬编码 fallback。** 所有内容必须：

1. 从数据库读取（chapters、character_arcs、meta 等）
2. 或通过函数参数传入（book_name 等）
3. 无默认值时用占位符字符串（"小说"/"故事开始"），不能写死具体内容