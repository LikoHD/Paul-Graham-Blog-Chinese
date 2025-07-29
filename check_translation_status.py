#!/usr/bin/env python3
import json
import os

def check_translation_status(data_dir):
    """检查翻译状态"""
    processed_dir = os.path.join(data_dir, 'processed')
    
    untranslated = []
    partial_failed = []
    completed = []
    
    for filename in sorted(os.listdir(processed_dir)):
        if filename.endswith('.json'):
            article_file = os.path.join(processed_dir, filename)
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查翻译状态
                if 'paragraphs' not in data or not data['paragraphs']:
                    # 没有翻译字段
                    untranslated.append(filename)
                else:
                    # 检查是否有翻译失败的段落
                    failed_count = 0
                    total_count = len(data['paragraphs'])
                    
                    for para in data['paragraphs']:
                        translated = para.get('translated', '')
                        if (translated.startswith('[翻译失败]') or 
                            translated.startswith('[待翻译]') or 
                            translated == '' or
                            '[翻译失败]' in translated or
                            '[待翻译]' in translated):
                            failed_count += 1
                    
                    if failed_count == total_count:
                        # 全部失败
                        untranslated.append(filename)
                    elif failed_count > 0:
                        # 部分失败
                        partial_failed.append((filename, failed_count, total_count))
                    else:
                        # 全部完成
                        completed.append(filename)
                        
            except Exception as e:
                print(f"读取文件 {filename} 失败: {e}")
                continue
    
    print(f"翻译状态汇总:")
    print(f"- 完全未翻译: {len(untranslated)} 篇")
    print(f"- 部分翻译失败: {len(partial_failed)} 篇")
    print(f"- 翻译完成: {len(completed)} 篇")
    print(f"- 总计: {len(untranslated) + len(partial_failed) + len(completed)} 篇")
    
    if untranslated:
        print(f"\n完全未翻译的文章 ({len(untranslated)} 篇):")
        for i, filename in enumerate(untranslated[:10]):  # 只显示前10个
            print(f"  {i+1}. {filename}")
        if len(untranslated) > 10:
            print(f"  ... 还有 {len(untranslated) - 10} 篇")
    
    if partial_failed:
        print(f"\n部分翻译失败的文章 ({len(partial_failed)} 篇):")
        for i, (filename, failed, total) in enumerate(partial_failed[:10]):
            print(f"  {i+1}. {filename} ({failed}/{total} 段落失败)")
        if len(partial_failed) > 10:
            print(f"  ... 还有 {len(partial_failed) - 10} 篇")
    
    return untranslated, partial_failed

if __name__ == "__main__":
    check_translation_status("data")