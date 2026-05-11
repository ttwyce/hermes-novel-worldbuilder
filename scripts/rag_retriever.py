#!/usr/bin/env python3
"""
rag_retriever.py — RAG 检索模块

功能：
- 根据角色名/场景/关键词检索相关段落
- 支持多路检索 + 去重
- 返回格式化文本供 get_context 使用

用法：
  python3 rag_retriever.py "书名" "赵婉清" --n 3
  python3 rag_retriever.py "书名" "青云峰,大比" --n 2
"""

import sys
import os


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ chromadb 未安装")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers 未安装")


# ==================== 路径配置 ====================

def get_chroma_path(book_name: str) -> str:
    root = tracking_db.find_novel_root(book_name)
    return os.path.join(root, ".tracking/chroma_db")


def get_collection_name(book_name: str) -> str:
    """collection 名称（哈希处理，支持中文字符书名）"""
    import hashlib
    safe = hashlib.sha256(book_name.encode()).hexdigest()[:16]
    return f"novel_{safe}"


def get_chroma_client(book_name: str):
    if not CHROMADB_AVAILABLE:
        raise RuntimeError("chromaDB 未安装：pip install chromadb")
    db_path = get_chroma_path(book_name)
    if not os.path.exists(db_path):
        return None
    return chromadb.PersistentClient(path=db_path)


# ==================== 检索核心 ====================

def retrieve(
    book_name: str,
    query: str,
    n: int = 3,
    chapter_filter: int = None,
    exclude_chapter: int = None
) -> list:
    """检索与 query 相关的段落
    
    Args:
        book_name: 书名
        query: 检索词（支持逗号分隔多词）
        n: 每个检索词返回的段落数
        chapter_filter: 只在指定章节检索
        exclude_chapter: 排除某章节（如当前章节之前的内容，不需要当前章节自己）
    
    Returns:
        [{"text": "...", "chapter": N, "source": "chN_m"}]
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return []
    
    from sentence_transformers import SentenceTransformer
    
    client = get_chroma_client(book_name)
    if client is None:
        return []
    
    collection_name = get_collection_name(book_name)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []
    
    if collection.count() == 0:
        return []
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 多路检索
    queries = [q.strip() for q in query.split(',') if q.strip()]
    all_results = []
    
    for q in queries:
        q_embed = model.encode([q]).tolist()[0]
        
        where_filter = {}
        if chapter_filter is not None:
            where_filter["chapter"] = chapter_filter
        if exclude_chapter is not None:
            where_filter["chapter"] = {"$ne": exclude_chapter}
        
        results = collection.query(
            query_embeddings=[q_embed],
            n_results=n,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas"]
        )
        
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            item = {
                "text": doc,
                "chapter": meta.get("chapter", 0),
                "source": meta.get("chapter_file", "unknown"),
                "preview": meta.get("text", "")[:50],
            }
            # 去重（按文本内容）
            if not any(r['text'] == item['text'] for r in all_results):
                all_results.append(item)
    
    # 按章节排序（近的在前）
    all_results.sort(key=lambda x: x['chapter'], reverse=True)
    
    return all_results[:n * len(queries)]


# ==================== 格式化输出 ====================

def format_retrieved(results: list, header: str = "相关段落") -> str:
    """格式化检索结果为可读文本"""
    if not results:
        return ""
    
    lines = [f"**{header}**（共{len(results)}段）", ""]
    
    current_chapter = None
    for r in results:
        ch = r['chapter']
        if ch != current_chapter:
            lines.append(f"--- 第{ch}章 ---")
            current_chapter = ch
        
        text = r['text']
        if len(text) > 200:
            text = text[:200] + "..."
        
        lines.append(f"「{text}」")
        lines.append("")
    
    return '\n'.join(lines)


def get_character_history(book_name: str, char_name: str, current_chapter: int = None, n: int = 3) -> str:
    """获取角色在历史章节中的出现段落"""
    results = retrieve(
        book_name=book_name,
        query=char_name,
        n=n,
        exclude_chapter=current_chapter
    )
    return format_retrieved(results, f"角色「{char_name}」相关段落")


def get_scene_reference(book_name: str, scene_name: str, current_chapter: int = None, n: int = 2) -> str:
    """获取场景相关段落"""
    results = retrieve(
        book_name=book_name,
        query=scene_name,
        n=n,
        exclude_chapter=current_chapter
    )
    return format_retrieved(results, f"场景「{scene_name}」参考")


# ==================== 主函数 ====================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法:")
        print("  python3 rag_retriever.py \"书名\" \"角色名\" --n 3")
        print("  python3 rag_retriever.py \"书名\" \"场景名\" --n 2")
        print("  python3 rag_retriever.py \"书名\" \"角色,场景\" --n 2")
        sys.exit(1)
    
    book_name = sys.argv[1]
    query = sys.argv[2]
    n = 3
    
    if '--n' in sys.argv:
        idx = sys.argv.index('--n')
        n = int(sys.argv[idx + 1])
    
    try:
        results = retrieve(book_name, query, n=n)
        
        if not results:
            print(f"未找到与「{query}」相关的段落（索引可能未初始化）")
            print(f"  运行: python3 rag_indexer.py \"{book_name}\" 建立索引")
            sys.exit(0)
        
        print(format_retrieved(results, f"「{query}」相关段落"))
        
        # 同时显示各段落所在章节
        chapters = sorted(set(r['chapter'] for r in results))
        print(f"\n涉及章节：{chapters}")
        
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)