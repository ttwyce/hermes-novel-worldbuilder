#!/usr/bin/env python3
"""
verify_chapter.py — 验证章节字数是否达标
用法: python3 verify_chapter.py <文件路径> <设定字数> [容差]

示例:
  python3 verify_chapter.py 第31章.md 3000        # 容差默认0.8（即±20%）
  python3 verify_chapter.py 第31章.md 3000 0.75  # 自定义容差75%

返回值:
  0 = 合格
  1 = 字数不足
  2 = 文件不存在
  3 = 参数错误
"""
import sys
import os

def verify_chapter(filepath: str, target: int, tolerance: float = 0.8) -> dict:
    """验证章节文件字数是否在 target±(1-tolerance) 范围内"""
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"文件不存在: {filepath}"}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 去除审核报告（如果混入了）
    lines = content.strip().split('\n')
    for i, line in enumerate(lines):
        if '审核报告' in line or '---' == line.strip():
            lines = lines[:i]
            break
    
    clean_content = '\n'.join(lines)
    actual = len(clean_content)
    
    lower = int(target * tolerance)   # 下限
    upper = int(target * (2 - tolerance))  # 上限
    
    pass_ = lower <= actual <= upper
    pct = actual / target * 100
    
    return {
        "status": "pass" if pass_ else "fail",
        "file": filepath,
        "target": target,
        "lower": lower,
        "upper": upper,
        "actual": actual,
        "pct_of_target": round(pct, 1),
        "gap": actual - target
    }

def main():
    if len(sys.argv) < 3:
        print("用法: verify_chapter.py <文件> <设定字数> [容差]")
        print("例:   verify_chapter.py 第31章.md 3000")
        sys.exit(3)
    
    filepath = sys.argv[1]
    try:
        target = int(sys.argv[2])
    except ValueError:
        print(f"错误: 设定字数必须是整数: {sys.argv[2]}")
        sys.exit(3)
    
    tolerance = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.8
    
    result = verify_chapter(filepath, target, tolerance)
    
    if result["status"] == "error":
        print(f"❌ {result['message']}")
        sys.exit(2)
    
    print(f"文件: {result['file']}")
    print(f"字数: {result['actual']} / 目标{result['target']} ({result['pct_of_target']}%)")
    print(f"合格范围: {result['lower']}-{result['upper']} 字")
    
    if result["status"] == "pass":
        print(f"✅ 合格 (gap: {result['gap']:+d})")
        sys.exit(0)
    else:
        if result["actual"] < result["lower"]:
            print(f"❌ 不合格: 少 {abs(result['gap'])} 字 (需补到 {result['lower']} 字以上)")
        else:
            print(f"⚠️ 超出上限 {result['gap']} 字 (建议精简)")
        sys.exit(1)

if __name__ == "__main__":
    main()