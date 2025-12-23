#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理CSP课程语音转文字记录，转换为笔记
"""

import os
import re
from pathlib import Path

# 常见误识别词汇的修正字典
CORRECTIONS = {
    'CSECSE': 'CSE',
    'emo': 'MIT',
    'MT': 'MIT',
    'GCG': 'GCC',
    'on deline': 'unsigned',
    'on line': 'unsigned',
    'DP sic': 'DNS',
    'DP 这 c': 'DNS',
    'slogal': 'throughput',
    'suput': 'throughput',
    'fluwput': 'throughput',
    'fluwook': 'throughput',
    'lillilenance': 'latency',
    'latx': 'latency',
    'titilalization': 'utilization',
    'comcomtibility': 'compatibility',
    'comtitiity': 'compatibility',
    'usubility': 'usability',
    'usiability': 'usability',
    'consistcy': 'consistency',
    'consisency': 'consistency',
    'fortorrent': 'fault tolerance',
    'prison priicy': 'privacy',
    'agr': 'API',
    'RDA': 'RDMA',
    'RDV': 'RDMA',
    'RDB': 'RDMA',
    'DCQB': 'DCQP',
    'DCQQ': 'DCQP',
    'VR sleep': 'VMsleep',
    'eleicc': 'elastic',
    'eleicted': 'elastic',
    'obscility': 'mobility',
    'migration': 'migration',
    'NNCC': 'NCCL',
    'mmedia': 'NCCL',
    'mltage cass': 'multi-cast',
    'consistency y': 'consistency',
    'coninicence': 'consistency',
    '短信四 g': 'consistency',
}

# 噪音关键词（用于识别开头和结尾的噪音）
NOISE_KEYWORDS = [
    '对不起', '加油', '嗯嗯', '嘘嘘', '嗯', '啊', '这个这个', '那个那个',
    '等一会儿', '让我重新', '能不能', '听不到', '你让我', '找到吗',
    '不好意思', '没事', '随便', '眼睛', '不是', '没有', '什么',
    '怎么', '为什么', '哪里', '多少', '多少回', '卖这个事情',
    '不想脸', '抖音', '直接问', '到底', '直接捡到', '老师就',
    '欢迎坚持', '几点', '明明白', '中一年', '不行', '走没有',
    '听不是', '不能坚果', '都西好', '做成一家应家', '发展费',
    '不变变了', '不愿意再看', '随便的眼睛',
    # 结尾噪音
    '生活的中要', '如果你不说', '还把拿的手子', '去年秋季的头产',
    '年趋势', '查烧竹', '放的么', '熟猪', '还好吧', '没什么意思',
    '一直所以', '我上回那别来', '北京也好吃的', '都是', '你说可以',
    '反正也没意思', '一年一年给吃', '我饭就不吃了', '你们那不如',
    '我们家努力不服', '亲个么么哒', '一嘘', '刚我们家', '小嗯',
    '有我们你更清了', '提供珍惜', '我写作', '是是嗯嘘', '嗯爱很好',
    '放心', '来亲个', '么么哒',
]

def is_noise_line(line):
    """判断一行是否是噪音"""
    line_lower = line.lower()
    # 检查是否包含噪音关键词
    for keyword in NOISE_KEYWORDS:
        if keyword in line:
            return True
    
    # 检查是否主要是无意义的字符组合
    if len(line) < 10:
        return True
    
    # 检查是否包含大量无意义的重复
    if line.count('嗯') > 3 or line.count('啊') > 3:
        return True
    
    # 检查是否包含明显的噪音模式
    noise_patterns = [
        r'^[0-9:]+[嗯啊这那]*$',  # 只有时间戳和语气词
        r'加油加油',  # 重复的加油
        r'嗯嗯嗯',  # 多个嗯
    ]
    for pattern in noise_patterns:
        if re.match(pattern, line):
            return True
    
    return False

def clean_text(text):
    """清理文本，修正误识别"""
    # 应用修正字典
    for wrong, correct in CORRECTIONS.items():
        text = text.replace(wrong, correct)
    
    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_content(lines):
    """从行列表中提取有效内容，去除开头和结尾的噪音"""
    if not lines:
        return []
    
    # 找到第一个有效内容行
    start_idx = 0
    for i, line in enumerate(lines):
        # 移除时间戳
        content = re.sub(r'^\d+:\d+\s*', '', line).strip()
        if content and not is_noise_line(content):
            # 检查是否包含课程相关关键词
            course_keywords = ['CSP', '课程', '上课', '系统', '计算机', '我们', '大家', '这个', '那个']
            if any(keyword in content for keyword in course_keywords) or len(content) > 20:
                start_idx = i
                break
    
    # 找到最后一个有效内容行
    end_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        content = re.sub(r'^\d+:\d+\s*', '', lines[i]).strip()
        if content and not is_noise_line(content):
            # 检查是否包含课程相关关键词
            if any(keyword in content for keyword in course_keywords) or len(content) > 20:
                end_idx = i + 1
                break
    
    return lines[start_idx:end_idx]

def process_lecture_file(input_file, output_dir):
    """处理单个课程文件"""
    print(f"处理文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取有效内容
    valid_lines = extract_content(lines)
    
    if not valid_lines:
        print(f"  警告: {input_file} 没有找到有效内容")
        return
    
    # 处理每一行
    processed_lines = []
    for line in valid_lines:
        # 移除时间戳
        content = re.sub(r'^\d+:\d+\s*', '', line).strip()
        if content:
            # 清理文本
            cleaned = clean_text(content)
            if cleaned and not is_noise_line(cleaned):
                processed_lines.append(cleaned)
    
    # 生成输出文件名
    input_name = Path(input_file).stem
    # 从文件名中提取节次号
    match = re.search(r'节次(\d+)', input_name)
    if match:
        lecture_num = match.group(1)
        output_file = output_dir / f"节次{lecture_num}_笔记.txt"
    else:
        output_file = output_dir / f"{input_name}_笔记.txt"
    
    # 写入笔记文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# CSP课程第{lecture_num}节笔记\n\n")
        for line in processed_lines:
            f.write(line + '\n\n')
    
    print(f"  已生成笔记: {output_file} ({len(processed_lines)} 条内容)")

def main():
    """主函数"""
    scripts_dir = Path('scripts')
    output_dir = Path('notes')
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    # 获取所有课程文件
    lecture_files = sorted(scripts_dir.glob('节次*_课堂语音转文字记录.txt'))
    
    if not lecture_files:
        print("未找到课程文件")
        return
    
    print(f"找到 {len(lecture_files)} 个课程文件\n")
    
    # 处理每个文件
    for lecture_file in lecture_files:
        try:
            process_lecture_file(lecture_file, output_dir)
        except Exception as e:
            print(f"  错误: 处理 {lecture_file} 时出错: {e}")
    
    print(f"\n处理完成！笔记已保存到 {output_dir} 目录")

if __name__ == '__main__':
    main()


