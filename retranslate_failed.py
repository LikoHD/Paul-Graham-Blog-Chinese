#!/usr/bin/env python3
import json
import os
import sys
from translate_simple import SimpleTranslator

def retranslate_failed_articles(data_dir, api_key, target_filename=None):
    """重新翻译失败的文章"""
    translator = SimpleTranslator(api_key)
    processed_dir = os.path.join(data_dir, 'processed')
    
    
    # 获取所有需要重新翻译的文章
    articles_to_retranslate = []
    
    # 如果指定了文件名，只处理该文件
    if target_filename:
        if not target_filename.endswith('.json'):
            target_filename += '.json'
        filenames_to_check = [target_filename]
    else:
        filenames_to_check = sorted(os.listdir(processed_dir))
    
    for filename in filenames_to_check:
        if filename.endswith('.json'):
            article_file = os.path.join(processed_dir, filename)
            if not os.path.exists(article_file):
                if target_filename:
                    print(f"错误: 文件 {filename} 不存在")
                continue
                
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查是否有翻译失败的段落
                if 'paragraphs' in data and data['paragraphs']:
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
                        articles_to_retranslate.append((article_file, filename))
                elif 'content' in data and 'paragraphs' in data['content']:
                    # 如果只有content.paragraphs但没有翻译过的paragraphs字段
                    articles_to_retranslate.append((article_file, filename))
            except:
                continue
    
    print(f"找到 {len(articles_to_retranslate)} 篇文章需要重新翻译")
    
    if not articles_to_retranslate:
        print("没有需要重新翻译的文章！")
        return True
    
    # 逐一重新翻译
    for i, (article_file, filename) in enumerate(articles_to_retranslate):
        print(f"\n进度: {i+1}/{len(articles_to_retranslate)} - {filename}")
        
        try:
            with open(article_file, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            # 获取原始段落
            if 'content' in article_data and 'paragraphs' in article_data['content']:
                paragraphs = article_data['content']['paragraphs']
            else:
                print(f"  跳过: 找不到原始段落")
                continue
            
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
            
        except Exception as e:
            print(f"  处理失败: {e}")

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
    
    # 检查是否指定了特定文件
    target_filename = None
    if len(sys.argv) > 1:
        target_filename = sys.argv[1]
        print(f"只翻译指定文件: {target_filename}")
    
    # 开始重新翻译
    retranslate_failed_articles(DATA_DIR, API_KEY, target_filename)