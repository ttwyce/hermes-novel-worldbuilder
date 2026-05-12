---
name: novel-worldbuilder
description: 根据用户输入的剧情梗概，自动生成完整详实的小说设定集。自动为每本书创建独立目录，存放设定、人物、大纲、正文等所有文件。支持剧情推进时动态追加角色、更新关系。
---

# novel-worldbuilder

## 🚀 新书创建流程（5步上手）

```
① 用户给剧情梗概（≥50字）
       ↓
② 我生成书名选项 → 用户选书名
       ↓
③ 用户确认创作参数（5项）
       ↓
④ 运行初始化：python3 init_novel.py 「书名」 [章节数] [字数] --主角 主角名
       ↓
⑤ 我生成全套设定集 → 用户确认 → 开始写章节
```

**关键命令速查**：

| 操作 | 命令 |
|------|------|
| 创建小说目录+数据库 | `python3 scripts/init_novel.py 「书名」 150 3000 --主角 主角名` |
| 查看章节上下文 | `python3 scripts/get_context.py 「书名」 5` |
| 验证章节字数 | `python3 scripts/verify_chapter.py 第5章.md 3000` |
|| 更新追踪文件（+伏笔+世界状态） | `python3 scripts/post_chapter.py 「书名」 5 3000 「核心事件」 [「伏笔」] [--world-state "境界:炼气期"] [--chapter-path "文件路径"]` |
| 导出追踪文件 | `python3 scripts/export_md.py 「书名」` |
| 检查章节衔接 | `python3 scripts/check_transition.py 「书名」 6` |

> ⚠️ **角色需预注册**：`init_novel` 只创建主角（A01）。女主/配角需手动注册：
> `python3 -c "import sys; sys.path.insert(0,'scripts'); from init_tracking import add_character; add_character('db路径', 'A02', '角色名', '深化型', '起点状态')"`
> 预注册后 `get_context.py` 才能追踪他们的出场间隔。

---

## 快速入口

- **章节写入**：`references/chapter-writing-workflow.md`
- **写作风格问题**：`references/writing-style-pitfalls.md` ← 重要
- **常见错误**：`references/common-pitfalls.md`
- **审核清单**：`references/chapter-completion-checklist.md`
- **写作速查**：`references/writing-quick-ref.md`

## 职能

接收用户剧情梗概 → 生成书名选项 → 确认后初始化项目 → 逐文件生成设定集 → 写正文时按流程执行追踪文件更新。

**核心原则**：主 Agent 生成设定文件（逐文件），**章节优先使用子代理单章写作（串行）**，主 Agent 负责统筹和追踪文件更新。

**旧小说名清单**（已删除的书/角色，不含当前项目）：
```
嘴强剑仙 / 陆天 / 叶琳 / 苏清雪 / 赵婉清 / 陈朵朵 / 摆烂修仙 / 李明辉 / 陈浩 / 周天成 / 林晓
```

> ⚠️ **当前项目「时光缓缓」/ 陆时晏 / 林诺 / 周窈 / 陈绥 不是旧书名。**

**子代理优势**：每个子代理独立上下文，不受 write_file 截断限制（约1000字），可一次性写完3000+字章节。串行执行确保顺序和验证。

**备选方案**：write_file + patch 分段写入（仅在子代理不可用时使用）。

**用户授权习惯**：用户多次说「你自己看着来吧」「你决定」时，代表授权 Agent 全权做主。此时不应逐项确认，应直接执行，必要时简要说明结果即可。若用户明确要求讨论方向，则先停手确认。

---

**追踪数据存储架构**

**存储方案**：SQLite + 自动导出 Markdown（通用）

```
小说根目录/
└── .tracking/
    └── tracking.db          # SQLite 数据库（所有追踪数据）
大纲/*.md                    # 自动导出的 Markdown（人工阅读）
```

**数据库表结构**：
| 表名 | 用途 |
|------|------|
| `chapters` | 章节信息（id/字数/状态/核心事件） |
| `character_arcs` | 角色弧光（id/名字/类型/状态/当前章节/转折点） |
| `chronicle` | 编年史（时间/事件/章节） |
| `plot_hooks` | 伏笔钩子（章节/描述/状态/已解章节） |
| `world_state` | 世界状态（键值对） |

**⚠️ 场景检查工具适用性**：check_transition.py 的 scene_keywords 仅当小说明确使用修仙/校园常见场景关键词时才有效。如果新小说使用独特场景名，可能无法检测。此功能不阻断使用，但结果需人工核对。

⚠️ **导出函数设计铁律**：所有导出函数的输出内容必须从数据库读取，严禁硬编码任何小说特定内容（书名/角色名/章节数/目标字数等）在函数内部的默认数据里。如果需要默认值，从数据库动态计算或用函数参数传入。
> **导出函数必须保留模板结构**：导出函数（如 `export_progress_board`）在文件已存在时，不能覆盖整个模板文件，而应在模板特定位置插入或替换动态内容，保留模板中的固定结构（如 `## 基本参数`、`## 总体进度`、`## 分卷进度` 等区块）。
> 正确做法：读取现有文件，在 `## 待处理问题（BLOCKERS）` 标记前插入动态生成的章节进度表，保留标记之后的内容（如 `## 待处理问题`、`## 本月目标`）。
> 历史Bug：export_progress_board 曾每次覆盖整个模板，导致 `基本参数`/`总体进度`/`分卷进度` 等精心设计的区块全部丢失。修复方式是在模板标记处做增量插入而非全量覆盖。
> 
> 另一历史Bug（2026-05-11）：`lines_text` 变量在 `if/elif/else` 分支中未被正确赋值导致 `UnboundLocalError`。根因：`existing_text is None` 分支内用 `lines = [...]`（列表）而非 `lines_text`（字符串），且 `elif marker in existing_text` 在 `existing_text is None` 分支之后但 `marker` 变量定义位置不对。修复方式：统一使用 `lines_text` 作为最终字符串变量，确保所有分支都有赋值。
>
> 全面检查修复（2026-05-11）：共9个问题——export_arc_tracking `current_state` 重复字段；rag_indexer overlap 负数风险（`effective_overlap = min(overlap, len(current)//2)`）；get_chapter_end 定义但从未使用（从 check_transition.py 移除）；generate_report 的 unused curr_chapter_end 参数（已移除）；trim_utils.py 的 `--target` 参数位置检测逻辑（含糊已简化）；trim_to_target 的 dry_run 参数从不生效（已移除）；post_chapter.py 自动注册循环内重复调用 get_all_character_arcs（改用预查缓存）；
>
> 测试修复（2026-05-11）：b1 - argparse nargs='?' 位置参数错位（`chapter_path` 误接收第6个位置参数「伏笔」），改为 `--chapter-path` flag；b2 - 正则匹配复合词（`主角小声问` 误捕获 `小声`），加 `is_valid_name` 二次验证；b3 - 词边界检测（`name in text` 太宽泛），改用 `(?:^|[^一-龥])name(?:$|[^a-zA-Z0-9一-龥])` 边界匹配；
>
> ⚠️ **已知架构性缺陷（2026-05-11 测试发现，b1/b2 已修复）**：
> - ~~**自动注册 false positive**~~ → 已缓解（is_valid_name 二次验证 + 词边界正则），架构级限制无法根除
> - ~~**find_chapter_file 内部调用不稳定**~~ → 已修复：argparse chapter_path 改为 `--chapter-path` flag
> - ~~**词边界检测**~~ → 已修复：post_chapter.py 用正则边界匹配 `get_context` 角色检测正常
> - ~~**伏笔重复写入**~~ → 已修复：P2 修复指南见 `references/auto-registration-fix-log.md`

**新小说初始化**：
```bash
python3 scripts/init_tracking.py "新小说名"
# 自动创建数据库 + 添加默认主角
```

**脚本说明**：
| 脚本 | 功能 |
|------|------|
| `init_tracking.py` | 初始化新小说数据库（通用） |
| `tracking_db.py` | SQLite 数据库操作模块（CRUD） |
| `export_md.py` | 从数据库导出 6 个 Markdown 文件（含伏笔钩子追踪、世界状态） |
| `post_chapter.py` | 主入口：写入章节 + 角色检测（自动注册）+ 伏笔 + 世界状态 + 导出全部 MD + 验证 |
> ⚠️ **角色自动注册**：`post_chapter.py` 的 `detect_and_update_characters()` 会自动检测未注册的新角色并写入 `character_arcs` 表（弧光类型=待设定）。写完章后请检查 `大纲/角色弧光追踪.md`，修正误注册角色的名字并补充弧光类型。 |
> ⚠️ **角色检测只更新已知角色**：自动注册只处理新角色，已注册角色的 `current_chapter` 追踪不受影响。 |
| `get_context.py` | 从数据库生成章节上下文（含世界状态/角色状态/伏笔/RAG参考/衔接提示） |
| `verify_chapter.py` | 章节验证脚本（字数） |
| `check_transition.py` | 章节衔接检查（场景/时间/情绪/钩子） |
| `rag_indexer.py` | RAG 向量化索引（每写完章自动调用，也可手动：`python3 rag_indexer.py "书名"`） |
| `rag_retriever.py` | RAG 检索模块（供 get_context 调用，也可单独使用） |

**导出的 MD 文件（6个）**：
- `进度看板.md` — 章节进度 + 当前世界状态摘要
- `剧情线追踪.md` — 每章核心事件
- `编年史.md` — 按时间线排列的事件
- `角色弧光追踪.md` — 角色成长轨迹 + 关键转折点
- `伏笔钩子追踪.md` — 活跃伏笔 + 已解伏笔（**新增**）
- `世界状态.md` — 世界核心状态（**新增**）

---

## RAG 向量检索系统

**安装依赖**：
```bash
# pip 不可用时用 uv
uv pip install chromadb sentence-transformers
```

**数据流**：
```
post_chapter.py → rag_indexer → ChromaDB（向量化存储）
                                ↓
get_context.py → rag_retriever → RAG 写作参考（注入上下文）
```

**工作原理**：
- 每写完一章，`post_chapter.py` 自动调用 `rag_indexer` 将本章内容切成 chunks，向量化存入 ChromaDB（持久化在 `.tracking/chroma_db/`）
- 写新章前，`get_context.py` 自动检索：
  - 久未互动的角色 → 他们在历史章节中的相关段落
  - 上章核心事件关键词 → 类似场景的参考写法
- `get_context` 输出末尾的 `【RAG 写作参考】` 区块包含这些历史片段

**存储路径**：`~/novels/书名/.tracking/chroma_db/`

**手动命令**：
```bash
# 重建全书籍节索引
python3 scripts/rag_indexer.py "书名"

# 只索引第5章
python3 scripts/rag_indexer.py "书名" 5

# 查看索引状态
python3 scripts/rag_indexer.py "书名" --stats

# 单独检索（调试用）
python3 scripts/rag_retriever.py "书名" "角色名" --n 3
```

**注意**：`chromadb` 和 `sentence-transformers` 是可选依赖。未安装时 RAG 功能静默跳过，追踪系统正常工作。

**写入时自动发生的事**：

每运行一次 `post_chapter.py`：
1. 写入 SQLite ✅
2. 导出 MD ✅
3. **自动建立 RAG 向量索引**（静默，出错不影响主流程）

**读取时自动发生的事**（`get_context.py`）：

运行 `get_context.py` 时，在 `【积压伏笔】` 后 / `【衔接提示】` 前注入 `【RAG 写作参考】`：
- 久未互动角色（gap≥3章）→ 先输出 **角色弧光结构化信息**（从 SQLite 读取），再检索正文中的段落
- 上章核心事件关键词 → 检索类似场景的正文参考

**输出格式示例**：
```
【RAG 写作参考】

  【女主A】
  角色名：女主A
  弧光类型：温柔学姐型
  当前状态：与男主同班，关系尚浅
  上次互动：第1章（初次见面）
  历史片段：
    第2章：女主A微微一笑...

  【女主B】
  角色名：女主B
  弧光类型：待设定
  当前状态：不明
  上次互动：尚未出场
```

**架构说明**：
- 角色弧光结构化数据（`arc_type`/`current_state`/`key_moments`）**存 SQLite 不进向量库**。向量库只索引正文文本 chunks。
- `get_context` 输出的角色信息来自 SQLite（精准查询），历史文字段落来自 ChromaDB（语义检索）。两者互补。
- `get_collection_name()` 使用 SHA256 哈希生成 collection name，确保中文字符书名正常工作（ChromaDB collection name 只允许 `[a-zA-Z0-9._-]`）。

---

## 单章写入流程

### 一、章节写前规划（必做）

写之前，先规划本章框架：

```
第X章 章节名
- 核心事件：XXXX
- 主要场景：XXXX
- 出场人物：主角 + XXX/XXX/XXX
- 字数目标：约3000字（±20%，即2400-3600）
```

⚠️ 估算时按3300-3500字标准写，防止实际输出偏低。

---

### 二、写入方法（子代理 + 主Agent分工）

**流程**：子代理负责写 → 主Agent负责验证 → 不合格则重写 → 合格则更新追踪

```
① 主Agent获取上下文：python3 get_context.py "书名" X
② 主Agent启动子代理写第X章（prompt中说明：只写正文，不验证不追踪）
③ 子代理完成（只写章节，不做验证和追踪）
④ 主Agent验证：python3 verify_chapter.py 第X章.md 3000
   - 合格（2400-3600字）→ ⑤
   - 不合格 → 重新启动子代理重写 → 重复④
⑤ 主Agent更新追踪：python3 post_chapter.py "书名" X Y "核心事件" ["伏笔钩子"] [--world-state "境界:炼气期,地点:青云峰"]
⑥ 主Agent验证追踪文件（进度看板/剧情线/编年史/角色弧光/伏笔钩子/世界状态）→ 启动下一章子代理
```

**子代理 prompt 模板**：
```
小说：《书名》
世界观：XXXX
主角：XXXX，身份/能力/系统（若有）
当前剧情（前X章结尾）：XXXX
本章内容：XXXX
写作要求：
- 约3000字
- 用终端cat heredoc一次性写完（不用write_file，会截断）
- 章节内容里不要用---做场景分隔（---是审核报告分隔符）
- 路径：正文/卷X名称/第X章.md

=== 章节上下文（必须获取）===
写作前先运行：python3 scripts/get_context.py "书名" X
根据输出：
- 确认主要角色的当前状态和上次互动时间
- 安排久未互动的角色出场
- 推进积压的伏笔
- 注意衔接上章结尾的情绪和场景

**注意**：
- 只写章节正文，不要写审核报告
- 不要执行验证脚本（主Agent会验证）
- 不要执行追踪更新（主Agent会更新）
- 写完即返回
- 如果字数可能超出上限（>3600字），适当精简后再返回
```

**⚠️ 重要：验证失败时必须重写**

如果主Agent验证字数不合格（<2400或>3600），必须重新启动子代理重写该章节，不能只做局部修改。重写时在prompt中说明：
- 上一版字数是多少
- 目标字数范围（2400-3600）
- 必须保留的关键情节

**收尾脚本**：`scripts/post_chapter.py`（SQLite 版）
- 自动写入 SQLite 数据库
- 自动导出所有 Markdown 追踪文件（格式永远正确，无残留列问题）
- 必须运行且验证通过，才算章节真正完成

**⚠️ 强制规则**：子代理返回前必须确认收尾步骤全部完成。未更新追踪文件就返回=任务失败。

### 子代理超时与字数超限处理

**超时处理**：

子代理报告 `timeout`（600s）不代表失败——文件通常已经写完。超时后：

```bash
# 1. 检查文件是否存在
ls -la 正文/卷X名称/第X章.md
# 2. 验证字数
python3 verify_chapter.py 第X章.md 3000
# 3. 情况A：≥2400字 → 正常运行 post_chapter.py
# 3. 情况B：<2400字 → 工作被中断，需要重写本章
# 3. 情况C：>3600字 → 精简约3000-3600范围内
```

**字数超限处理**（常见！子代理通常写出目标的150-180%）：

当 verify_chapter.py 显示超出3600字时，用 patch 精简约3000-3600：

```bash
# patch(new_string="精简后的承接句", old_string="被删除的冗余段落")
# 常见可精简：冗长内心独白、重复环境描写、过度铺陈的结尾
# 每次精简200-500字，验证通过后继续
```

**避免超限**：在子代理prompt中明确说明「严格控制3000-3500字，禁止超出3600」。

**备选方案：write_file + patch 分段写入**（仅在子代理不可用时）

已知系统限制：write_file 单次写入超过约1000字符会截断。

```
① write_file 第一段（约800-1500字）
② patch(new_string=新段落, old_string=衔接句) 追加下一段
③ 重复直到章节完成
```

⚠️ 章节内部禁止使用 `---` 作为叙事分段符。verify_chapter.py 将第一个 `---` 用作正文/审核报告边界。

### 三、禁止做法

- ❌ 把审核报告写在章节正文同一文件里
- ❌ 用一次`write_file`同时写入正文和审核报告
- ❌ 在章节文件末尾追加审核内容
- ❌ 写完章节后不立即更新追踪文件
- ❌ 写章节时使用`...`/`待续`/`未完`/`[TBC]`等截断标记
- ❌ 字数严重不足（低于设定值80%）就写下一章

### 四、章节内禁止使用 `---` 分隔符

**⚠️ 重要设计约束**：verify_chapter.py 将 `---` 用作章节正文与审核报告的分隔符。

- 章节文件中**只能有一个 `---`**，即结尾审核报告前的那个
- 章节内部（正文中）**禁止使用 `---` 作为叙事分段符**
- 如果需要分段，用空行或 `* * *` 代替

**原因**：verify_chapter.py 第30行的截断逻辑会在第一个 `---` 处截断章节内容，导致后续正文丢失。章节如果包含多个 `---`，只有第一段被计入字数。

**正确写法**：
```markdown
# 第1章 章节名

这是第一段内容。

这是第二段内容，中间无分隔符。

* * *（如需分段用星号）

这是第三段内容。

---

## 第1章审核报告
……
```

**错误写法**（会导致字数统计严重偏低）：
```markdown
# 第1章 章节名

第一段内容。

---

第二段内容。  ← 这里会被截断！

---

第三段内容。  ← 永远不会计入！

---

## 第1章审核报告  ← 只有到这里之前的内容被计入
```

---

### 五、事故修复

当审核报告已混入章节文件时：

```bash
# 1. 定位审核报告起始行
grep -n "第X章审核报告" 正文/卷一_XXX/第X章.md
# 输出示例：177:## 第X章审核报告 → 从第177行开始

# 2. 裁剪文件（保留前N-1行）
head -n 176 正文/卷一_XXX/第X章.md > /tmp/chX_clean.md
mv /tmp/chX_clean.md 正文/卷一_XXX/第X章.md

# 3. 清理残留分隔符
sed -i '/^---$/d' 正文/卷一_XXX/第X章.md

# 4. 验证
wc -l 正文/卷一_XXX/第X章.md
tail -3 正文/卷一_XXX/第X章.md
```

⚠️ **绝对禁止用`tail`裁剪**——tail保留末尾删除开头，是反向操作。

---

## 目录结构

```
~/novels/《书名》/
├── 世界观/（世界设定/时代背景/力量体系/世界状态.md）
├── 势力/（势力分布.md）
├── 人物/
│   ├── 角色注册表.md
│   ├── 人物关系图.md
│   ├── 关系记录.md
│   ├── 伏笔与钩子.md
│   └── 角色档案/（主角.md / 后宫角色.md / 其他角色.md）
├── 大纲/
│   ├── 剧情大纲.md
│   ├── 分卷大纲.md
│   ├── 章节大纲.md
│   ├── 编年史.md
│   ├── 剧情线追踪.md
│   ├── 角色弧光追踪.md
│   └── 进度看板.md
├── 写作指南/（文风指南/写作规范.md）
└── 正文/（卷一/卷二/卷三/）
```

---

## 子代理章节写后的追踪文件更新

子代理写完每章后，主Agent立即执行追踪文件更新：

1. 读取章节文件，确认字数合格
2. 更新 `大纲/剧情线追踪.md`（记录本章事件）
3. 更新 `大纲/进度看板.md`（标记章节完成）
4. 更新 `大纲/编年史.md`（追加时间线）
5. 批量patch其他追踪文件

---

## 新书创建流程

### 步骤一：理解需求

接收用户剧情梗概，判断信息量：
- **≥50字且有完整情节点** → 进入步骤一补充
- **信息不足** → 先向用户询问关键信息

**必须确认5个参数**：

```
📋 创作参数确认清单

1️⃣ 人称/视角
   - A. 第三人称限定（紧跟主角）← 推荐
   - B. 第三人称全知
   - C. 第一人称

2️⃣ 每章字数
   - A. 1500-2000 字（快节奏）
   - B. 2500-3500 字（主流标准）← 推荐
   - C. 4000-6000 字（长篇）
   ※ 实际允许±20%浮动

3️⃣ 章节总数
   - A. 30-50章（短篇，10-15万字）
   - B. 80-120章（中篇，24-36万字）← 推荐
   - C. 150章+（长篇，45万字+）← 推荐

4️⃣ 作品基调
   - A. 搞笑/沙雕
   - B. 热血/燃
   - C. 黑暗/压抑
   - D. 其他

5️⃣ 发布平台
   - A. 起点
   - B. 晋江
   - C. 番茄
   - D. 飞卢
```

### 步骤二：生成书名（至少5个选项）

```markdown
📖 候选书名：

1. 「书名A」← 推荐（理由）
2. 「书名B」
3. 「书名C」
4. 「书名D」
5. 「书名E」

以上都不满意？可输入自定义书名。
```

**规则**：书名与剧情核心元素相关，用「」包裹。

### 步骤三：创建目录骨架 + 初始化追踪数据库

用户选好书名后（**一条命令搞定目录+数据库**）：

```bash
python3 ~/.hermes/skills/creative/novel-worldbuilder/scripts/init_novel.py <书名> [总章节数] [每章字数] --主角 <主角名>
# 示例：python3 init_novel.py 「书名」 80 3000 --主角 主角名
```

此命令自动完成：
1. 创建小说目录结构（世界观/人物/大纲/正文等）
2. 生成3个追踪文件（剧情线追踪/进度看板/角色弧光追踪）
3. 初始化SQLite追踪数据库
4. 导出全部Markdown追踪文件

### 步骤四：预览确认（新增）

生成正文前，**先输出预览摘要供用户确认**：

```markdown
## 📋 小说设定预览 —《[书名]》

### 🌍 世界观概要
[2-3段世界观描述]

### ⚔️ 势力分布
[主要势力列表，每方1-2句]

### 👤 主要角色设定
- **[主角]**：[名字/身份/性格/核心冲突]
- **[女主群像]**：[每个女主1句话]
- **[关键配角]**：[2-3个]

### 📖 剧情主线预览
[时间线/章节阶段，3-5个关键转折]

### 🎯 伏笔与悬念
[2-4个主要伏笔]

---
请确认：
- ✅ 满意，开始生成
- 📝 修改：[具体内容]
- ❌ 放弃
```

⚠️ 这一步**不生成任何文件**，只输出预览。确认后才开始生成。

### 步骤五：逐文件生成内容

按顺序逐文件生成，每个文件写入后才生成下一个：

```
第1批（核心设定）
① 设定集.md
② 世界观/世界观设定.md
③ 世界观/时代背景.md
④ 世界观/力量体系.md

第2批（世界状态）
⑤ 世界观/世界状态.md

第3批（势力与人物）
⑥ 势力/势力分布.md
⑦ 人物/角色注册表.md
⑧ 人物/人物关系图.md
⑨ 人物/关系记录.md
⑩ 人物/伏笔与钩子.md

第4批（人物详情）
⑪ 人物/角色档案/主角.md
⑫ ~ 人物/角色档案/后宫角色.md（N个）

第5批（大纲与指南）
⑬ 大纲/剧情大纲.md
⑭ 大纲/分卷大纲.md
⑮ 大纲/章节大纲.md
⑯ 大纲/编年史.md
⑰ 写作指南/文风指南.md
⑱ 写作指南/写作规范.md
```

⚠️ 设定文件（世界观/势力/人物/大纲）必须主Agent逐文件生成。章节使用子代理单章串行写入。

---

## 正文写作规范

### 每章内容模板

```markdown
# 第X章：章节名

[正文内容]
```

### 正文规范

1. **开头**：直接切入场景，第一句点名时间/地点/人物状态
2. **节奏**：事件→冲突→解决，每章至少一个核心冲突
3. **结尾**：必须有钩子（悬念/意外/笑点），不能平淡收尾
4. **对话**：用「」包裹，口语化
5. **心理**：用吐槽代替"他感到…"
6. **笑点密度**：每章至少2-3个有效笑点，不能重复同一个梗
7. **禁用词**：赫然/陡然/突然

### 防止重复写作

**五大常见重复问题**：
- 同一借口说太多遍（最多用两次）
- 场景原地打转不推进
- 反应模式单一（主角不是只会躺和怼）
- 对话全是同一套路
- 笑点重复

**实操口诀**：
1. 拒绝一件事最多说两遍，第三遍必须变
2. 场景拉扯不超过五行，必须有事件打断
3. 主角反应要有变化
4. 对话要有节奏变化
5. 每章必须有新信息进入

---

## 动态更新机制

### 步骤五：剧情推进中——更新关系

1. 追加到`关系记录.md`
2. 更新双方角色档案
3. 重新绘制关系图

### 步骤六：剧情推进中——角色状态变化

1. 更新`角色注册表`
2. 更新角色档案结局字段
3. 追加到`关系记录.md`

### 追踪文件更新清单

每章写完后**立即自动执行**：

| 操作 | 更新文件 |
|------|---------|
| 章节摘要 | `大纲/章节大纲.md` |
| 时间线 | `大纲/编年史.md` |
| 世界状态 | `世界观/世界状态.md` |
| 伏笔埋设 | `人物/伏笔与钩子.md` |
| 剧情线追踪 | `大纲/剧情线追踪.md` |
| 进度看板 | `大纲/进度看板.md` |
| 角色弧光 | `大纲/角色弧光追踪.md` |
| 关系变化 | `人物/关系记录.md` |
| 角色档案 | `人物/角色档案/[角色名].md` |

---

## 章节审核

### 审核输出格式

```
## 第X章审核报告
### 一、基础合规（4项）
✅/❌ 1. 字数：XXX字（设定值±20%合格）
✅/❌ 2. POV：仅跟主角
✅/❌ 3. 对话格式：全部「」
✅/❌ 4. 禁用词：无赫然/陡然/突然

### 二、剧情质量（5项）
✅/❌ 5. 有核心事件
✅/❌ 6. 推进线条
✅/❌ 7. 无重复
✅/❌ 8. 章末钩子
✅/❌ 9. 新信息

### 三、伏笔检查（3项）
✅/❌ 10. 伏笔登记
✅/❌ 11. 伏笔一致性
✅/❌ 12. 伏笔密度

### 四、场景一致性（3项）
✅/❌ 13. 场景衔接
✅/❌ 14. 人物位置
✅/❌ 15. 时间线

### 五、追踪文件更新（5项）
✅/❌ 16-20. [各文件状态]
```

→ ✅ 全部通过，标记完成
→ ⚠️ 有可改进项，确认后标记完成
→ ❌ 有硬性未通过项，必须先修复

---

## 质量审计清单

每次技能完整性检查，按以下步骤执行 → 详见 `references/skill-audit-procedure.md`（含执行顺序/命令/常见遗漏点）

> 💡 **SQLite跟踪系统专项审计**：数据库的表级三链路审计（写入→读取→导出）→ 详见 `references/tracking-system-audit.md`

### 快速审计命令（5步）

### 1. 硬编码扫描（导出函数）

```bash
# export_md.py 和 check_transition.py 中不应有硬编码书名/角色名
grep -n "某旧书名\|卷一_铺垫\|卷二_对抗\|卷三_高潮" scripts/export_md.py
# 预期：无输出

grep -A5 "scene_keywords = {" scripts/check_transition.py
# 预期：已清空为注释模板
```

### 2. 模板结构保留验证

```bash
# init 后验证模板存在，导出后验证基本参数区块未丢失
python3 init_novel.py "模板测试" 80 2500 --主角 "测试主角" 2>&1 | tail -2
python3 -c "import sys; sys.path.insert(0,'scripts'); import tracking_db, export_md; db = tracking_db.get_db_path('模板测试'); tracking_db.insert_or_update_chapter(db, 1, '第1章', 300, 'done', '测试'); export_md.export_all('模板测试')"
grep "## 基本参数" 大纲/进度看板.md
# 预期：有输出（模板结构保留）
rm -rf ~/novels/模板测试
```

### 3. 角色预注册机制

```bash
# 新角色注册后才能被 get_context 识别
# 检查 post_chapter.py 是否只更新不注册（已知角色）
grep -n "detect_and_update_characters\|character_arcs.*WHERE" scripts/post_chapter.py
# 预期：只更新，不 INSERT 新角色
```

### 4. trim_utils.py dry_run 语义

```bash
# trim_to_target(dry_run=True/False) 都只是分析，从不修改文件
# 实际修改在 auto_trim 中执行（需手动确认）
grep -n "open.*'w'" scripts/trim_utils.py
# 预期：只有 auto_trim 中有写文件操作
```

### 5. 完整流程测试（新小说名）

```bash
rm -rf ~/novels/审计测试
python3 init_novel.py "审计测试" 80 2500 --主角 "测试主角"
# 模拟写1章后导出
python3 post_chapter.py "审计测试" 1 300 "测试事件"
head -5 大纲/进度看板.md
# 验证书名=审计测试，总目标=80章/20万字（不是150/45万字）
rm -rf ~/novels/审计测试
```

### 3. SKILL.md 引用完整性

参考文件列表（13个）与实际文件（14个）必须一致，scripts（10个）与实际一致。

---

### 参考文件

#### 核心流程
- `references/chapter-writing-workflow.md` — 章节写入完整流程（子代理方案）
- `references/writing-style-pitfalls.md` — 写作风格常见问题（节奏/吐槽/人物线/衔接）
- `references/chapter-completion-checklist.md` — 20项审核标准
- `references/writing-quick-ref.md` — 写作速查

### 避坑与案例
- `references/common-pitfalls.md` — 常见错误与事故
- `references/truncation-disaster.md` — 截断标记事故案例
- `references/delegate-batch-failure.md` — 子代理批量失败分析（历史参考）
- `references/bugcase-export-hardcoded-novelname.md` — 导出硬编码Bug案例（已修复）
- `references/technical-pitfalls.md` — 技术陷阱与避坑指南

### 设计文档
- `references/sqlite-storage-architecture.md` — SQLite存储架构详解
- `references/collaboration-strategy.md` — 协作与生成策略
- `references/structure-guide.md` — 目录结构参考

### 写作风格
- `references/writing-style-guide.md` — 五种风格指南（搞笑/热血/治愈/刀子/悬疑）

### 脚本
- `scripts/init_tracking.py` — 初始化新小说数据库（通用）
- `scripts/init_novel.py` — 初始化小说项目
- `scripts/verify_chapter.py` — 章节验证脚本（字数）
- `scripts/check_transition.py` — 章节衔接检查（场景/时间/情绪/钩子）
- `scripts/get_context.py` — 章节上下文生成（角色状态/伏笔/关系线）
- `scripts/tracking_db.py` — SQLite 数据库操作模块
- `scripts/export_md.py` — Markdown 导出模块
- `scripts/post_chapter.py` — 子代理收尾脚本（通用版：数据库+角色检测+导出MD）
- `scripts/trim_utils.py` — 章节精简工具（分析/精简/自动压缩超长章节）
  > ⚠️ `trim_to_target()` 只分析不修改；`auto_trim()` 才实际修改文件
- `scripts/migrate_to_sqlite.py` — 通用迁移脚本（历史数据）
- `templates/chapter-template.md` — 章节模板

### 审计与规范
- `references/audit-checklist.md` — 全面检查清单（5类必检项 + 常见遗漏表）
- `references/skill-audit-procedure.md` — 审计执行流程（顺序 + 每轮检查内容）
- `references/tracking-system-audit.md` — **SQLite跟踪系统审计方法论**（三链路检查：写入→读取→导出）← 重要
- `references/auto-registration-fix-log.md` — 自动注册 false positive 调查与修复记录（含架构性缺陷说明）

---

*最后更新：2026-05-12（审计规范化：migrate_to_sqlite.py旧书数据清理+路径占位符+新增audit-checklist）*