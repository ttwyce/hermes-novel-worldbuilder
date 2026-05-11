#!/usr/bin/env python3
"""
trim_utils.py — 章节精简工具

功能：分析章节内容，识别可精简的冗余部分，辅助快速压缩字数。

用法：
  # 分析超长章节（自动找出可精简位置）
  python3 trim_utils.py analyze 第5章.md
  
  # 精简目标（从超长压缩到目标字数）
  python3 trim_utils.py trim 第5章.md --target 3500
  
  # 自动精简（直接修改文件，保留备份）
  python3 trim_utils.py auto 第5章.md --target 3500

原理：
  1. 先 verify_chapter.py 确认字数超限
  2. analyze 显示各段落长度和可精简候选
  3. trim/patch 自动精简超出部分
  4. 验证直至合格
"""

import sys
import os
import re
from pathlib import Path

# ==================== 冗余检测规则 ====================

REDUNDANCY_PATTERNS = [
    # 过长心理独白（连续3行以上的内心描写）
    (r'(\n[「『][^「『」\n]{10,80}[」』]\n){4,}',
     "过长连续对话", "建议合并或删除部分对话"),
    
    # 重复形容词堆砌（>3个形容词连用）
    (r'[的嘛呢啊呀呵~！]{3,}',
     "语气词堆砌", "减少连续语气词"),
    
    # 冗长的场景描写（同一场景>150字）
    # （需要段落分析，见下面 analyze_paragraphs）
]

# ==================== 段落分析 ====================

def split_paragraphs(content: str) -> list:
    """按空行分割成段落"""
    parts = re.split(r'\n\s*\n', content)
    return [p.strip() for p in parts if p.strip() and not p.strip().startswith('#')]

def analyze_chapter(filepath: str) -> dict:
    """分析章节，返回各段落长度和精简候选"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 去除审核报告
    if '---' in content:
        content = content.split('---')[0]
    
    paragraphs = split_paragraphs(content)
    
    result = {
        'file': filepath,
        'total_len': len(content),
        'paragraph_count': len(paragraphs),
        'paragraphs': [],
        'candidates': []
    }
    
    for i, p in enumerate(paragraphs):
        p_len = len(p)
        para_info = {
            'index': i,
            'length': p_len,
            'preview': p[:60] + '...' if len(p) > 60 else p,
            'is_dialogue': bool(re.search(r'[「『].{5,}[」』]', p)),
            'is_inner': bool(re.search(r'[他她]感觉?|[他她]想到?|[他她]觉得?', p)),
            'is_scene': bool(re.search(r'阳光|微风|天空|大地|四周|周围|远处|近处', p)),
        }
        result['paragraphs'].append(para_info)
        
        # 标记精简候选
        if para_info['is_dialogue'] and para_info['length'] > 300:
            result['candidates'].append({
                'index': i,
                'reason': f"对话段落过长（{p_len}字）",
                'savings_est': int(p_len * 0.3),
                'suggestion': "合并或删除部分对话"
            })
        elif para_info['is_inner'] and para_info['length'] > 250:
            result['candidates'].append({
                'index': i,
                'reason': f"内心独白过长（{p_len}字）",
                'savings_est': int(p_len * 0.4),
                'suggestion': "精简内心描写"
            })
        elif para_info['is_scene'] and para_info['length'] > 200:
            result['candidates'].append({
                'index': i,
                'reason': f"场景描写过长（{p_len}字）",
                'savings_est': int(p_len * 0.3),
                'suggestion': "缩减环境描写"
            })
    
    return result

def print_analysis(analysis: dict) -> None:
    """打印分析结果"""
    print(f"\n📊 章节分析：{analysis['file']}")
    print(f"  总字数：{analysis['total_len']} 字")
    print(f"  段落数：{analysis['paragraph_count']}")
    print(f"\n段落长度分布：")
    
    lens = [p['length'] for p in analysis['paragraphs']]
    if lens:
        print(f"  最短：{min(lens)} 字 | 最长：{max(lens)} 字 | 平均：{sum(lens)//len(lens)} 字")
    
    if not analysis['candidates']:
        print(f"\n  ✅ 未发现明显冗余")
        return
    
    print(f"\n精简候选（{len(analysis['candidates'])}处）：")
    total_est = 0
    for c in analysis['candidates']:
        print(f"  [{c['index']}] {c['reason']}，估计可节省 ~{c['savings_est']} 字")
        print(f"       建议：{c['suggestion']}")
        total_est += c['savings_est']
    
    print(f"\n  估计总可精简：~{total_est} 字")

def trim_to_target(filepath: str, target: int, dry_run: bool = True) -> dict:
    """
    分析并估算精简可节省的字数（不修改文件）。
    无论 dry_run 何值，都不修改文件。实际精简在 auto_trim 中执行。
    返回：{'status': 'pass'/'fail', 'saved': N, 'final_len': M}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 去除审核报告
    if '---' in content:
        content = content.split('---')[0]
    
    original_len = len(content)
    
    # 逐段落扫描，估算可删减字数
    paragraphs = split_paragraphs(content)
    surplus = original_len - target
    saved = 0
    
    if surplus <= 0:
        return {'status': 'pass', 'saved': 0, 'final_len': original_len}
    
    for i, p in enumerate(paragraphs):
        if surplus <= 0:
            break
        p_len = len(p)
        
        # 对话段：估计可删40%
        if p_len > 300 and re.search(r'[「『].{5,}[」』]', p):
            delete_amount = int(p_len * 0.3)
            surplus -= delete_amount
            saved += delete_amount
        
        # 内心独白：估计可删35%
        elif p_len > 250 and re.search(r'[他她]感觉?|[他她]想到?', p):
            delete_amount = int(p_len * 0.35)
            surplus -= delete_amount
            saved += delete_amount
        
        # 场景描写：估计可删30%
        elif p_len > 200 and re.search(r'阳光|微风|天空|大地|四周', p):
            delete_amount = int(p_len * 0.3)
            surplus -= delete_amount
            saved += delete_amount
    
    return {
        'status': 'pass' if saved >= original_len - target else 'fail',
        'saved': saved,
        'final_len': original_len - saved
    }

def auto_trim(filepath: str, target: int) -> bool:
    """
    自动精简文件（循环直到合格或无法再精简）
    """
    print(f"\n🔪 自动精简：{filepath}")
    print(f"  目标字数：{target}")
    
    iteration = 0
    max_iterations = 10
    
    while iteration < max_iterations:
        iteration += 1
        
        # 验证当前字数
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from verify_chapter import verify_chapter
        result = verify_chapter(filepath, target)
        
        print(f"\n  第{iteration}轮：{result['actual']} 字（目标 {target}，gap {result['gap']:+d}）")
        
        if result['status'] == 'pass':
            print(f"\n✅ 精简完成！{result['actual']} 字（目标 {target} ±{int(target*0.2)}）")
            return True
        
        # 需要精简
        surplus = result['actual'] - target
        if surplus <= 0:
            break
        
        # 执行精简
        trim_result = trim_to_target(filepath, target, dry_run=False)
        
        if trim_result['saved'] == 0:
            print(f"  ⚠️ 无法继续精简（已是精简版）")
            break
        
        # 写回文件
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if '---' in content:
            content = content.split('---')[0]
        
        # 应用精简：截断超出部分
        paragraphs = split_paragraphs(content)
        total = sum(len(p) for p in paragraphs)
        
        if total > target:
            # 从后往前删，直到达标
            excess = total - target
            for i in range(len(paragraphs)-1, -1, -1):
                if excess <= 0:
                    break
                p_len = len(paragraphs[i])
                # 保留80%
                keep_len = int(p_len * 0.8)
                if keep_len < 50:
                    # 删除整个段落
                    excess -= p_len
                    paragraphs[i] = None
                else:
                    # 截断
                    excess -= (p_len - keep_len)
                    paragraphs[i] = paragraphs[i][:keep_len]
            
            new_content = '\n\n'.join(p for p in paragraphs if p is not None)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  → 精简 {trim_result['saved']} 字，写入文件")
    
    # 最终验证
    from verify_chapter import verify_chapter
    result = verify_chapter(filepath, target)
    if result['status'] == 'pass':
        print(f"\n✅ 精简完成！{result['actual']} 字")
        return True
    else:
        print(f"\n⚠️ 最终字数 {result['actual']} 字，仍超出目标 {target} 字")
        print(f"   建议手动处理，或使用 analyze 子命令查看精简候选")
        return False

# ==================== 主函数 ====================

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    filepath = sys.argv[2]
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(2)
    
    if command == 'analyze':
        analysis = analyze_chapter(filepath)
        print_analysis(analysis)
        
    elif command == 'trim':
        target = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] != '--target' else 3000
        if '--target' in sys.argv:
            idx = sys.argv.index('--target')
            target = int(sys.argv[idx + 1])
        result = trim_to_target(filepath, target, dry_run=True)
        print(f"\n精简分析：")
        print(f"  预计节省：{result['saved']} 字")
        print(f"  预计字数：{result['final_len']} 字")
        print(f"  状态：{'可达标' if result['status']=='pass' else '仍超限'}")
        print(f"\n如需实际执行，使用：trim_utils.py auto {filepath} --target {target}")
        
    elif command == 'auto':
        target = 3000
        if '--target' in sys.argv:
            idx = sys.argv.index('--target')
            target = int(sys.argv[idx + 1])
        success = auto_trim(filepath, target)
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ 未知命令：{command}")
        print(f"可用命令：analyze / trim / auto")
        sys.exit(3)

if __name__ == '__main__':
    main()