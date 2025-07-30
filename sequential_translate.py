#!/usr/bin/env python3
import json
import os
import sys
from translate_simple import SimpleTranslator

def get_untranslated_articles(data_dir):
    """获取所有未翻译的文章"""
    processed_dir = os.path.join(data_dir, 'processed')
    untranslated = []
    
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
                    has_failed = False
                    for para in data['paragraphs']:
                        translated = para.get('translated', '')
                        if (translated.startswith('[翻译失败]') or 
                            translated.startswith('[待翻译]') or 
                            translated == '' or
                            '[翻译失败]' in translated or
                            '[待翻译]' in translated):
                            has_failed = True
                            break
                    
                    if has_failed:
                        untranslated.append(filename)
                        
            except Exception as e:
                continue
    
    return untranslated

def retranslate_single_article(data_dir, api_key, filename):
    """重新翻译单篇文章"""
    translator = SimpleTranslator(api_key)
    processed_dir = os.path.join(data_dir, 'processed')
    article_file = os.path.join(processed_dir, filename)
    
    print(f"\n开始翻译: {filename}")
    
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
        
        # 获取原始段落
        if 'content' in article_data and 'paragraphs' in article_data['content']:
            paragraphs = article_data['content']['paragraphs']
        else:
            print(f"  跳过: 找不到原始段落")
            return False
        
        print(f"  开始翻译 {len(paragraphs)} 个段落")
        
        # 翻译每个段落
        translated_paragraphs = []
        success_count = 0
        
        for j, paragraph in enumerate(paragraphs):
            print(f"  翻译段落 {j+1}/{len(paragraphs)}", end=' ')
            
            # 跳过太短的段落
            if len(paragraph.strip().split()) < 3:
                translated_paragraphs.append({
                    "original": paragraph,
                    "translated": paragraph
                })
                print("(太短，跳过)")
                continue
            
            # 翻译段落
            result = translator.translate_text(paragraph)
            
            if result['success']:
                translated_paragraphs.append({
                    "original": paragraph,
                    "translated": result['translated']
                })
                success_count += 1
                print("✓")
            else:
                translated_paragraphs.append({
                    "original": paragraph,
                    "translated": f"[翻译失败] {paragraph[:50]}..."
                })
                print(f"✗ ({result.get('error', '未知错误')})")
        
        # 更新文章数据
        from datetime import datetime
        article_data['paragraphs'] = translated_paragraphs
        article_data['translation_completed'] = datetime.now().isoformat()
        article_data['translation_stats'] = {
            "total_paragraphs": len(paragraphs),
            "success_count": success_count,
            "success_rate": f"{success_count/len(paragraphs)*100:.1f}%"
        }
        
        # 保存翻译结果
        with open(article_file, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        print(f"  保存成功: {success_count}/{len(paragraphs)} 段落翻译成功")
        return True
        
    except Exception as e:
        print(f"  处理失败: {e}")
        return False

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    # API密钥
    API_KEY = os.getenv("TRANSLATE_API_KEY")

    if not API_KEY:
        print("错误: 未找到 API 密钥。请在 .env 文件中设置 TRANSLATE_API_KEY。")
        sys.exit(1)
    
    # 数据目录
    DATA_DIR = "data"
    
    # 获取所有未翻译的文章
    untranslated = get_untranslated_articles(DATA_DIR)
    print(f"找到 {len(untranslated)} 篇文章需要翻译")
    
    if not untranslated:
        print("所有文章都已翻译完成！")
        sys.exit(0)
    
    # 逐一翻译
    success_count = 0
    for i, filename in enumerate(untranslated):
        print(f"\n进度: {i+1}/{len(untranslated)}")
        if retranslate_single_article(DATA_DIR, API_KEY, filename):
            success_count += 1
        
        # 显示当前进度
        print(f"当前完成: {success_count}/{i+1}")
    
    print(f"\n翻译完成! 成功翻译 {success_count}/{len(untranslated)} 篇文章")