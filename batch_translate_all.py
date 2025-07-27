#!/usr/bin/env python3
"""
批量翻译所有文章的脚本
自动以小批次翻译所有还未翻译的文章
"""
import os
import json
import subprocess
import time

def count_translated_articles():
    """统计已翻译的文章数量"""
    processed_dir = "data/processed"
    translated_count = 0
    total_count = 0
    
    for filename in os.listdir(processed_dir):
        if filename.endswith('.json'):
            total_count += 1
            filepath = os.path.join(processed_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'translation_completed' in data:
                        translated_count += 1
            except:
                continue
    
    return translated_count, total_count

def run_translation_batch(start_index, batch_size):
    """运行一个翻译批次"""
    cmd = f"./venv/bin/python translate.py batch {start_index} {batch_size}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"批次 {start_index}-{start_index+batch_size-1} 翻译成功")
            return True
        else:
            print(f"批次 {start_index}-{start_index+batch_size-1} 翻译失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"批次 {start_index}-{start_index+batch_size-1} 超时")
        return False
    except Exception as e:
        print(f"批次 {start_index}-{start_index+batch_size-1} 出错: {e}")
        return False

def main():
    print("开始批量翻译所有文章...")
    
    # 设置参数
    batch_size = 3  # 每批翻译3篇文章
    max_batches = 100  # 最多处理100个批次
    
    start_index = 0
    successful_batches = 0
    
    for batch_num in range(max_batches):
        print(f"\n=== 批次 {batch_num + 1} ===")
        
        # 检查当前进度
        translated, total = count_translated_articles()
        print(f"当前进度: {translated}/{total} 篇文章已翻译")
        
        if translated >= total - 5:  # 如果只剩少于5篇，说明基本完成
            print("翻译工作基本完成！")
            break
        
        # 运行翻译
        if run_translation_batch(start_index, batch_size):
            successful_batches += 1
            print(f"成功完成 {successful_batches} 个批次")
        
        start_index += batch_size
        
        # 短暂等待，避免API限制
        time.sleep(1)
    
    # 最终统计
    final_translated, final_total = count_translated_articles()
    print(f"\n=== 最终结果 ===")
    print(f"已翻译: {final_translated}/{final_total} 篇文章")
    print(f"完成度: {final_translated/final_total*100:.1f}%")
    print(f"成功批次: {successful_batches}")

if __name__ == "__main__":
    main()