#!/usr/bin/env python3
"""
rag_indexer.py — 章节内容向量化索引

功能：
- 读取已写章节，按段落切分
- 用 sentence-transformers 向量化
- 存入 ChromaDB（每本小说独立 collection）
- 支持按角色名/场景/关键词检索

用法：
  python3 rag_indexer.py "书名" [章节号]
  python3 rag_indexer.py "时光缓缓"      # 索引全书记得
  python3 rag_indexer.py "时光缓缓" 5   # 只索引第5章
"""

import sys
import os
import re
import functools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# 延迟导入，避免未安装时报错
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ chromadb 未安装，运行: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers 未安装，运行: pip install sentence-transformers")


# ==================== 路径配置 ====================

def get_chroma_path(book_name: str) -> str:
    """ChromaDB 持久化路径"""
    root = tracking_db.find_novel_root(book_name)
    return os.path.join(root, ".tracking/chroma_db")


def get_collection_name(book_name: str) -> str:
    """collection 名称（哈希处理，支持中文字符书名）"""
    import hashlib
    safe = hashlib.sha256(book_name.encode()).hexdigest()[:16]
    return f"novel_{safe}"


# ==================== 文本切分 ====================

def split_chapter_into_chunks(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """按段落切分章节，返回 chunk 列表
    
    Args:
        text: 章节纯文本（不含标题和审核报告）
        chunk_size: 每个 chunk 的字符数（默认300，约100中文）
        overlap: 相邻 chunk 重叠字符数（默认50，保持上下文连续性）
    
    Returns:
        [{"text": "...", "start": 0, "end": 300}, ...]
    """
    # 先按自然段落分割
    # 段落分隔符：两个以上换行
    raw_paragraphs = re.split(r'\n{2,}', text.strip())
    
    chunks = []
    current = ""
    current_start = 0
    
    for para in raw_paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果单个段落就超过 chunk_size，切成句子
        if len(para) > chunk_size:
            # 先把累积的 current 推入
            if current:
                chunks.append({"text": current.strip(), "start": current_start, "end": current_start + len(current)})
                current = ""
            
            # 句子级别分割（按中文句号/逗号）
            sentences = re.split(r'(?<=[。！？])', para)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(sent) > chunk_size:
                    # 超长句子，按逗号再切
                    sub = re.split(r'(?<=，)', sent)
                    for s in sub:
                        s = s.strip()
                        if not s:
                            continue
                        chunks.append({"text": s, "start": 0, "end": len(s)})
                else:
                    # 短于 chunk_size，但可能和下一个句子合并
                    if not current:
                        current_start = 0
                    current += sent + "。"
                    if len(current) >= chunk_size:
                        chunks.append({"text": current.strip(), "start": current_start, "end": current_start + len(current)})
                        current = ""
            continue
        
        # 普通段落
        if not current:
            current_start = 0
        
        current += para + "\n\n"
        
        if len(current) >= chunk_size:
            chunks.append({"text": current.strip(), "start": current_start, "end": current_start + len(current)})
            # 保留 overlap 字符作为下个 chunk 的开头
            if overlap > 0 and len(current) > overlap:
                current = current[-overlap:]
                current_start = current_start + len(current) - overlap
            else:
                current = ""
                current_start = 0
    
    # 最后剩余的
    if current.strip():
        chunks.append({"text": current.strip(), "start": current_start, "end": current_start + len(current)})
    
    return chunks


# ==================== 向量化与索引 ====================

@functools.lru_cache(maxsize=1)
def _get_model():
    """全局模型缓存（lru_cache 避免重复加载）"""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    return SentenceTransformer('all-MiniLM-L6-v2')


def init_chroma_client(db_path: str):
    """初始化 ChromaDB 客户端"""
    if not CHROMADB_AVAILABLE:
        raise RuntimeError("chromaDB 未安装：pip install chromadb")
    
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)


def index_chapter(book_name: str, chapter_num: int = None) -> dict:
    """索引指定章节或全书籍节
    
    Returns:
        {"indexed": N, "chunks": M, "errors": []}
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        raise RuntimeError("sentence-transformers 未安装：pip install sentence-transformers")
    
    db_path = get_chroma_path(book_name)
    collection_name = get_collection_name(book_name)
    
    client = init_chroma_client(db_path)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"book_name": book_name}
    )
    
    model = _get_model()
    
    # 读取章节文件
    novel_root = tracking_db.find_novel_root(book_name)
    chapter_files = []
    
    if chapter_num:
        # 只索引指定章节
        import glob
        pattern = os.path.join(novel_root, "正文/**/*.md")
        for f in glob.glob(pattern, recursive=True):
            if f"第{chapter_num}章" in f:
                chapter_files = [f]
                break
    else:
        # 索引全部章节
        import glob
        pattern = os.path.join(novel_root, "正文/**/*.md")
        chapter_files = sorted(glob.glob(pattern, recursive=True),
                               key=lambda x: (len(x), x))
    
    total_indexed = 0
    total_chunks = 0
    
    for ch_file in chapter_files:
        with open(ch_file, 'r', encoding='utf-8') as f:
            raw = f.read()
        
        # 去掉审核报告部分（第一个 --- 之后）
        first_sep = raw.find('---')
        if first_sep > 0:
            body = raw[:first_sep].strip()
        else:
            body = raw.strip()
        
        # 去掉章节标题行
        lines = body.split('\n')
        if lines and lines[0].startswith('#'):
            body = '\n'.join(lines[1:]).strip()
        
        if not body:
            continue
        
        chunks = split_chapter_into_chunks(body)
        
        if not chunks:
            continue
        
        # 提取章节号
        import re as re_module
        ch_match = re_module.search(r'第(\d+)章', os.path.basename(ch_file))
        ch_num = int(ch_match.group(1)) if ch_match else 0
        
        # 向量化
        texts = [c['text'] for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        
        # 生成 chunk ID
        chunk_ids = [f"ch{ch_num}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "chapter": ch_num,
                "chapter_file": os.path.basename(ch_file),
                "chunk_index": i,
            }
            for i, c in enumerate(chunks)
        ]
        
        # 写入 ChromaDB（覆盖已有章节内容）
        # 先删除该章节旧数据
        collection.delete(where={"chapter": ch_num})
        
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        total_indexed += 1
        total_chunks += len(chunks)
        print(f"  ✅ {os.path.basename(ch_file)}: {len(chunks)} chunks")
    
    print(f"\n🎉 索引完成：{total_indexed} 章，{total_chunks} chunks")
    return {"indexed": total_indexed, "chunks": total_chunks}


# ==================== 清理与统计 ====================

def get_stats(book_name: str) -> dict:
    """获取索引统计"""
    db_path = get_chroma_path(book_name)
    if not os.path.exists(db_path):
        return {"exists": False}
    
    client = init_chroma_client(db_path)
    collection_name = get_collection_name(book_name)
    
    try:
        collection = client.get_collection(collection_name)
        return {
            "exists": True,
            "count": collection.count(),
            "chapters": collection.count() // 3  # 估算平均每章3个chunk
        }
    except Exception:
        return {"exists": False}


# ==================== 主函数 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 rag_indexer.py \"书名\"         # 索引全书")
        print("  python3 rag_indexer.py \"书名\" 5       # 只索引第5章")
        print("  python3 rag_indexer.py \"书名\" --stats  # 查看索引状态")
        sys.exit(1)
    
    book_name = sys.argv[1]
    
    if len(sys.argv) >= 3 and sys.argv[2] == '--stats':
        stats = get_stats(book_name)
        print(f"索引状态：{stats}")
        sys.exit(0)
    
    chapter_num = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    
    print(f"\n📚 RAG 索引 {'第' + str(chapter_num) + '章' if chapter_num else '全书'}: {book_name}")
    print(f"   存储路径: {get_chroma_path(book_name)}")
    
    try:
        result = index_chapter(book_name, chapter_num)
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        print(f"   提示：确保小说目录存在于 ~/novels/")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)