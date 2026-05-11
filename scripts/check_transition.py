#!/usr/bin/env python3
"""
check_transition.py — 检查章节衔接是否自然

用法：
  python3 check_transition.py <书名> <当前章节号>
  python3 check_transition.py "书名" 7

检查内容：
1. 场景连续性：上一章和本章场景是否衔接
2. 时间合理：时间推进是否合理（不能同一天内发生不合理的事）
3. 情绪衔接：情感氛围是否断裂
4. 钩子回应：上一章的钩子是否得到回应
5. 钩子留下：本章是否留下新钩子

返回值：
  0 = 衔接正常
  1 = 有小问题（可接受）
  2 = 有大问题（建议修正）
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_db

# ==================== 辅助函数 ====================

def read_chapter(novel_root: str, chapter_num: int) -> str:
    """读取章节内容（不含审核报告）"""
    # 查找章节文件
    for root, dirs, files in os.walk(novel_root):
        for f in files:
            if f"第{chapter_num}章" in f and f.endswith('.md'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                # 去除审核报告
                if '---' in content:
                    content = content.split('---')[0]
                return content
    return ""

def get_prev_chapter_end(chapter_content: str) -> str:
    """获取章节最后N个字"""
    # 去掉空行和标题
    lines = [l for l in chapter_content.split('\n') if l.strip() and not l.startswith('#')]
    if not lines:
        return ""
    # 返回最后200字
    text = ''.join(lines[-5:])
    return text[-200:] if len(text) > 200 else text

def get_curr_chapter_start(chapter_content: str) -> str:
    """获取章节开头N个字"""
    lines = [l for l in chapter_content.split('\n') if l.strip() and not l.startswith('#')]
    if not lines:
        return ""
    # 返回前200字
    text = ''.join(lines[:5])
    return text[:200] if len(text) > 200 else text

def extract_hook(chapter_content: str) -> str:
    """提取章节末尾的钩子（最后一段）"""
    lines = [l for l in chapter_content.split('\n') if l.strip() and not l.startswith('#')]
    if len(lines) < 3:
        return ""
    # 最后3行作为钩子区域
    hook_area = '\n'.join(lines[-3:])
    return hook_area[:150]

def check_scene_consistency(prev_end: str, curr_start: str) -> dict:
    """检查场景连续性"""
    issues = []
    
    # 场景关键词（通用，未知小说请保持为空避免误判）
    scene_keywords = {
        # '场景名': ['关键词1', '关键词2'],
        # 示例（适用于校园/修仙类小说，可按需修改）：
        # '教室': ['教室', '上课', '课堂', '黑板'],
        # '食堂': ['食堂', '吃饭', '餐桌'],
        # '宿舍': ['宿舍', '房间', '床', '睡觉'],
    }
    
    # 检测当前章节开头的场景
    curr_scene = None
    for scene, keywords in scene_keywords.items():
        for kw in keywords:
            if kw in curr_start:
                curr_scene = scene
                break
        if curr_scene:
            break
    
    # 检测上一章结尾的场景
    prev_scene = None
    for scene, keywords in scene_keywords.items():
        for kw in keywords:
            if kw in prev_end:
                prev_scene = scene
                break
        if prev_scene:
            break
    
    # 场景变化检测
    if curr_scene and prev_scene and curr_scene != prev_scene:
        issues.append(f"场景突然切换：{prev_scene} → {curr_scene}（需要有过渡或明确说明）")
    
    return {
        "scene": curr_scene or prev_scene or "未检测到明确场景",
        "prev_scene": prev_scene,
        "curr_scene": curr_scene,
        "issues": issues
    }

def check_time_consistency(prev_end: str, curr_start: str) -> dict:
    """检查时间推进是否合理"""
    issues = []
    
    # 时间关键词
    time_keywords = {
        '早上': ['早上', '清晨', '早晨', '天亮', '晨雾'],
        '白天': ['上午', '中午', '下午', '阳光'],
        '傍晚': ['傍晚', '黄昏', '夕阳', '日落'],
        '晚上': ['晚上', '夜里', '深夜', '月亮', '星空'],
    }
    
    prev_time = None
    for time_kw, keywords in time_keywords.items():
        for kw in keywords:
            if kw in prev_end:
                prev_time = time_kw
                break
        if prev_time:
            break
    
    curr_time = None
    for time_kw, keywords in time_keywords.items():
        for kw in keywords:
            if kw in curr_start:
                curr_time = time_kw
                break
        if curr_time:
            break
    
    # 不合理的时间跳跃（比如早上→突然深夜，但没说天数）
    if prev_time and curr_time:
        time_order = ['早上', '白天', '傍晚', '晚上']
        try:
            prev_idx = time_order.index(prev_time)
            curr_idx = time_order.index(curr_time)
            # 跳2个时段以上且没有"第二天"等暗示
            if curr_idx < prev_idx - 1:
                if '第二' not in curr_start and '天亮' not in curr_start and '次日' not in curr_start:
                    issues.append(f"时间倒流：{prev_time} → {curr_time}（需明确时间线）")
            elif curr_idx > prev_idx + 1:
                if '第二天' not in curr_start and '次日' not in curr_start:
                    issues.append(f"时间跳跃过大：{prev_time} → {curr_time}（需说明天数）")
        except ValueError:
            pass
    
    return {
        "prev_time": prev_time,
        "curr_time": curr_time,
        "issues": issues
    }

def check_emotion_continuity(prev_end: str, curr_start: str) -> dict:
    """检查情绪衔接"""
    issues = []
    
    # 情绪关键词
    neg_emotions = ['哭', '悲伤', '难过', '沮丧', '绝望', '愤怒', '紧张', '害怕']
    pos_emotions = ['笑', '开心', '高兴', '兴奋', '愉快', '轻松', '得意']
    neutral_emotions = ['平静', '淡定', '冷静', '思考']
    
    def count_emotions(text, emotion_list):
        return sum(1 for e in emotion_list if e in text)
    
    prev_neg = count_emotions(prev_end, neg_emotions)
    prev_pos = count_emotions(prev_end, pos_emotions)
    
    curr_neg = count_emotions(curr_start, neg_emotions)
    curr_pos = count_emotions(curr_start, pos_emotions)
    
    # 情绪大幅波动检测（上一章还在哭，下一章突然笑）
    if prev_neg >= 2 and curr_pos >= 2:
        issues.append("情绪断裂：上章还在负面情绪，本章开头突然正面情绪（需有过渡）")
    elif prev_pos >= 2 and curr_neg >= 2:
        issues.append("情绪断裂：上章还在正面情绪，本章开头突然负面情绪（需有过渡）")
    
    return {
        "prev_emotion": "偏负面" if prev_neg > prev_pos else ("偏正面" if prev_pos > prev_neg else "中性"),
        "curr_emotion": "偏负面" if curr_neg > curr_pos else ("偏正面" if curr_pos > curr_neg else "中性"),
        "issues": issues
    }

def check_hook_response(novel_root: str, prev_chapter: int, curr_chapter: int, 
                        prev_end: str, curr_start: str) -> dict:
    """检查上一章钩子是否得到回应"""
    issues = []
    responses = []
    
    # 常见钩子模式
    hook_patterns = [
        (r'未完待续', 'TBC标记', False),
        (r'第\d+章', '章节标题', False),
        (r'到底', '疑问句', False),
        (r'怎么办', '疑问句', False),
        (r'难道', '疑问句', False),
        (r'突然', '突发事件', True),
        (r'就在这时', '突发事件', True),
        (r'没想到', '意外事件', True),
        (r'叮', '系统提示', True),
        (r'正在这时', '插入事件', True),
        (r'然而', '转折', True),
    ]
    
    has_hook = any(re.search(p, prev_end) for p, _, _ in hook_patterns if _)
    has_tbc = '未完' in prev_end or '待续' in prev_end or 'TBC' in prev_end
    
    # 检查本章开头是否回应了上一章的突发事件
    abrupt_keywords = ['突然', '就在这', '没想到', '然而', '叮', '忽然']
    prev_has_abrupt = any(kw in prev_end for kw in abrupt_keywords)
    curr_has_abrupt = any(kw in curr_start for kw in abrupt_keywords)
    
    if prev_has_abrupt and not curr_has_abrupt:
        # 上一章有突发事件，本章开头应该继续
        # 检查是否有明显的"接续"说明
        connect_words = ['紧接着', '与此同时', '就在', '此时', '于是', '然后']
        has_continuation = any(w in curr_start for w in connect_words)
        if not has_continuation:
            issues.append("上章有突发事件，本章开头未明确接续（建议加过渡词）")
    
    return {
        "has_prev_hook": has_hook or has_tbc,
        "issues": issues,
        "responses": responses
    }

def check_new_hook(chapter_content: str) -> dict:
    """检查本章是否留下新钩子"""
    issues = []
    
    # 提取最后一段（可能含钩子）
    lines = [l for l in chapter_content.split('\n') if l.strip() and not l.startswith('#')]
    if not lines:
        return {"has_hook": False, "issues": ["章节内容过短，无法判断"]}
    
    last_part = '\n'.join(lines[-3:])
    
    # 检测钩子关键词
    hook_keywords = ['未完', '待续', 'TBC', '到底', '怎么办', '难道', '突然', 
                     '悬念', '疑问', '然而', '就在这时', '没想到']
    
    has_hook = any(kw in last_part for kw in hook_keywords)
    
    # 检测是否"戛然而止"（在对话或事件进行中结束）
    in_middle_patterns = ['说：', '问道：', '问道', '问道', '突然', '就在这时']
    ends_in_middle = any(p in last_part[-100:] for p in in_middle_patterns)
    
    if not has_hook and not ends_in_middle:
        issues.append("本章结尾过于完整，缺乏新钩子（建议留个小悬念）")
    
    return {
        "has_hook": has_hook or ends_in_middle,
        "ends_in_middle": ends_in_middle,
        "issues": issues
    }

def generate_report(chapter_num: int, prev_chapter_end: str, curr_chapter_start: str,
                    curr_chapter_end: str, scene_check: dict, time_check: dict,
                    emotion_check: dict, hook_check: dict, new_hook_check: dict) -> str:
    """生成衔接检查报告"""
    lines = [f"📖 章节衔接检查报告：第{chapter_num-1}章 → 第{chapter_num}章", ""]
    
    all_issues = []
    
    # 1. 场景检查
    lines.append("【场景检查】")
    if scene_check['prev_scene'] and scene_check['curr_scene']:
        lines.append(f"  场景：{scene_check['prev_scene']} → {scene_check['curr_scene']}")
    if scene_check['issues']:
        all_issues.extend(scene_check['issues'])
        for iss in scene_check['issues']:
            lines.append(f"  ⚠️ {iss}")
    else:
        lines.append("  ✅ 场景衔接正常")
    lines.append("")
    
    # 2. 时间检查
    lines.append("【时间检查】")
    if time_check['prev_time'] and time_check['curr_time']:
        lines.append(f"  时间：{time_check['prev_time']} → {time_check['curr_time']}")
    if time_check['issues']:
        all_issues.extend(time_check['issues'])
        for iss in time_check['issues']:
            lines.append(f"  ⚠️ {iss}")
    else:
        lines.append("  ✅ 时间推进合理")
    lines.append("")
    
    # 3. 情绪检查
    lines.append("【情绪检查】")
    lines.append(f"  情绪：{emotion_check['prev_emotion']} → {emotion_check['curr_emotion']}")
    if emotion_check['issues']:
        all_issues.extend(emotion_check['issues'])
        for iss in emotion_check['issues']:
            lines.append(f"  ⚠️ {iss}")
    else:
        lines.append("  ✅ 情绪衔接自然")
    lines.append("")
    
    # 4. 钩子检查
    lines.append("【钩子检查】")
    if hook_check['issues']:
        all_issues.extend(hook_check['issues'])
        for iss in hook_check['issues']:
            lines.append(f"  ⚠️ {iss}")
    else:
        lines.append("  ✅ 钩子衔接正常")
    lines.append("")
    
    # 5. 新钩子检查
    lines.append("【新钩子检查】")
    if new_hook_check['issues']:
        all_issues.extend(new_hook_check['issues'])
        for iss in new_hook_check['issues']:
            lines.append(f"  ⚠️ {iss}")
    else:
        lines.append("  ✅ 本章结尾有钩子")
    lines.append("")
    
    # 总结
    lines.append("=" * 40)
    if not all_issues:
        lines.append("✅ 衔接正常，无明显问题")
    elif len(all_issues) <= 2:
        lines.append(f"⚠️ 有 {len(all_issues)} 个小问题（可接受）")
    else:
        lines.append(f"❌ 有 {len(all_issues)} 个问题（建议修正）")
    
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("用法: python3 check_transition.py <书名> <当前章节号>")
        print("例:   python3 check_transition.py \"书名\" 7")
        sys.exit(3)
    
    book_name = sys.argv[1]
    try:
        curr_ch = int(sys.argv[2])
    except ValueError:
        print("错误: 章节号必须是整数")
        sys.exit(3)
    
    prev_ch = curr_ch - 1
    if prev_ch < 1:
        print("错误: 当前章节号必须 > 1")
        sys.exit(3)
    
    # 获取小说根目录
    try:
        novel_root = tracking_db.find_novel_root(book_name)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(2)
    
    # 读取章节内容
    prev_content = read_chapter(novel_root, prev_ch)
    curr_content = read_chapter(novel_root, curr_ch)
    
    if not prev_content:
        print(f"错误: 找不到第{prev_ch}章内容")
        sys.exit(2)
    
    if not curr_content:
        print(f"错误: 找不到第{curr_ch}章内容")
        sys.exit(2)
    
    # 提取关键段落
    prev_end = get_prev_chapter_end(prev_content)
    curr_start = get_curr_chapter_start(curr_content)
    curr_end = get_chapter_end(curr_content)
    
    # 执行各项检查
    scene_check = check_scene_consistency(prev_end, curr_start)
    time_check = check_time_consistency(prev_end, curr_start)
    emotion_check = check_emotion_continuity(prev_end, curr_start)
    hook_check = check_hook_response(novel_root, prev_ch, curr_ch, prev_end, curr_start)
    new_hook_check = check_new_hook(curr_content)
    
    # 生成报告
    report = generate_report(
        curr_ch, prev_end, curr_start, curr_end,
        scene_check, time_check, emotion_check, hook_check, new_hook_check
    )
    
    print(report)
    
    # 返回状态码
    all_issues = (scene_check['issues'] + time_check['issues'] + 
                  emotion_check['issues'] + hook_check['issues'] + 
                  new_hook_check['issues'])
    if not all_issues:
        sys.exit(0)
    elif len(all_issues) <= 2:
        sys.exit(1)
    else:
        sys.exit(2)

def get_chapter_end(chapter_content: str) -> str:
    """获取章节最后100字"""
    lines = [l for l in chapter_content.split('\n') if l.strip() and not l.startswith('#')]
    if not lines:
        return ""
    text = ''.join(lines[-3:])
    return text[-100:] if len(text) > 100 else text

if __name__ == "__main__":
    main()