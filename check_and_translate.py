#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

def find_untranslated_articles(data_dir="data/processed"):
    """查找包含未翻译内容的文章"""
    untranslated_articles = []
    processed_dir = Path(data_dir)
    
    if not processed_dir.exists():
        print(f"错误: 目录 {data_dir} 不存在")
        return []
    
    print(f"正在扫描目录: {data_dir}")
    
    for json_file in sorted(processed_dir.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否有未翻译的段落
            has_untranslated = False
            
            if 'paragraphs' in data and data['paragraphs']:
                for para in data['paragraphs']:
                    translated = para.get('translated', '')
                    if (translated.startswith('[翻译失败]') or 
                        translated.startswith('[待翻译]') or 
                        translated == '' or
                        '[翻译失败]' in translated or
                        '[待翻译]' in translated):
                        has_untranslated = True
                        break
            elif 'content' in data and 'paragraphs' in data['content']:
                # 如果只有原始内容但没有翻译过的paragraphs字段
                has_untranslated = True
            
            if has_untranslated:
                untranslated_articles.append(json_file.name)
                
        except Exception as e:
            print(f"读取文件 {json_file} 时出错: {e}")
            continue
    
    return untranslated_articles

def translate_article(filename):
    """调用翻译脚本翻译单个文章"""
    print(f"\n开始翻译: {filename}")
    try:
        # 运行翻译脚本，只处理指定文件
        result = subprocess.run([
            sys.executable, 
            "retranslate_failed.py", 
            filename
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✓ {filename} 翻译完成")
            return True
        else:
            print(f"✗ {filename} 翻译失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {filename} 翻译超时")
        return False
    except Exception as e:
        print(f"✗ {filename} 翻译出错: {e}")
        return False

def main():
    import sys
    auto_mode = '--auto' in sys.argv
    
    print("=== 查询和翻译未翻译文章 ===\n")
    
    # 查找未翻译的文章
    untranslated = find_untranslated_articles()
    
    if not untranslated:
        print("✓ 所有文章都已翻译完成！")
        return
    
    print(f"\n找到 {len(untranslated)} 篇未翻译的文章:")
    for i, article in enumerate(untranslated, 1):
        print(f"  {i}. {article}")
    
    # 询问是否开始翻译（或自动模式）
    if auto_mode:
        print(f"\n自动模式：开始翻译这 {len(untranslated)} 篇文章...")
    else:
        try:
            response = input(f"\n是否开始翻译这 {len(untranslated)} 篇文章? (y/n): ").strip().lower()
            if response not in ['y', 'yes', '是']:
                print("取消翻译")
                return
        except EOFError:
            print("\n检测到非交互环境，使用自动模式...")
            auto_mode = True
    
    # 逐一翻译
    print(f"\n开始翻译 {len(untranslated)} 篇文章...\n")
    success_count = 0
    
    for i, filename in enumerate(untranslated, 1):
        print(f"进度: {i}/{len(untranslated)}")
        
        if translate_article(filename):
            success_count += 1
        
        # 短暂暂停，避免API限制
        if i < len(untranslated):
            print("暂停2秒...")
            import time
            time.sleep(2)
    
    print(f"\n=== 翻译完成 ===")
    print(f"成功: {success_count}/{len(untranslated)} 篇文章")
    if success_count < len(untranslated):
        print("部分文章翻译失败，您可以重新运行此脚本")

if __name__ == "__main__":
    main()