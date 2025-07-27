#!/usr/bin/env python3
import requests
import json
import os
import time
from datetime import datetime
import sys

class SimpleTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.rate_limit = 0.5  # 每500ms一个请求
        self.last_request_time = 0
    
    def wait_for_rate_limit(self):
        """确保请求频率控制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def translate_text(self, text):
        """翻译单段文本"""
        self.wait_for_rate_limit()
        
        prompt = f"""请将以下英文文本翻译成中文。要求：
1. 保持原文的语义和风格
2. 使用自然流畅的中文表达
3. 对于专业术语，请使用准确的中文对应词汇
4. 只返回翻译结果，不要添加任何解释

英文原文：
{text}"""
        
        try:
            payload = {
                "model": "Qwen/Qwen2.5-72B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                return {
                    "success": True,
                    "translated": translated_text,
                    "original": text
                }
            else:
                error_details = ""
                try:
                    error_json = response.json()
                    error_details = str(error_json)
                except:
                    error_details = response.text
                print(f"    API错误: {response.status_code} - {error_details}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_details}",
                    "original": text,
                    "translated": f"[翻译失败] {text[:50]}..."
                }
                
        except Exception as e:
            print(f"    翻译异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "original": text,
                "translated": f"[翻译失败] {text[:50]}..."
            }

def translate_article(article_file, translator):
    """翻译单篇文章"""
    print(f"\n处理文章: {os.path.basename(article_file)}")
    
    # 读取文章数据
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    # 检查是否已经翻译过
    if 'paragraphs' in article_data and article_data['paragraphs']:
        # 检查是否有段落需要翻译
        needs_translation = False
        for para in article_data['paragraphs']:
            if para.get('translated', '').startswith('[待翻译]') or para.get('translated', '') == '':
                needs_translation = True
                break
        
        if not needs_translation:
            print("  文章已翻译完成，跳过")
            return True
    
    # 获取段落内容
    if 'content' in article_data and 'paragraphs' in article_data['content']:
        # 新格式
        paragraphs = article_data['content']['paragraphs']
        if 'paragraphs' not in article_data:
            article_data['paragraphs'] = []
    elif 'paragraphs' in article_data:
        # 检查是否为旧格式
        if article_data['paragraphs'] and 'original' in article_data['paragraphs'][0]:
            paragraphs = [para['original'] for para in article_data['paragraphs']]
        else:
            paragraphs = article_data['paragraphs']
    else:
        print("  未找到段落内容")
        return False
    
    print(f"  找到 {len(paragraphs)} 个段落待翻译")
    
    # 翻译每个段落
    translated_paragraphs = []
    success_count = 0
    
    for i, paragraph in enumerate(paragraphs):
        print(f"  翻译段落 {i+1}/{len(paragraphs)}")
        
        # 跳过太短的段落
        if len(paragraph.strip().split()) < 3:
            translated_paragraphs.append({
                "original": paragraph,
                "translated": paragraph  # 短段落直接保留原文
            })
            continue
        
        # 翻译段落
        result = translator.translate_text(paragraph)
        
        if result['success']:
            translated_paragraphs.append({
                "original": paragraph,
                "translated": result['translated']
            })
            success_count += 1
            print(f"    ✓ 翻译成功")
        else:
            translated_paragraphs.append({
                "original": paragraph,
                "translated": f"[翻译失败] {paragraph[:50]}..."
            })
            print(f"    ✗ 翻译失败: {result.get('error', '未知错误')}")
    
    # 更新文章数据
    article_data['paragraphs'] = translated_paragraphs
    article_data['translation_completed'] = datetime.now().isoformat()
    article_data['translation_stats'] = {
        "total_paragraphs": len(paragraphs),
        "success_count": success_count,
        "success_rate": f"{success_count/len(paragraphs)*100:.1f}%"
    }
    
    # 保存翻译结果
    try:
        with open(article_file, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        print(f"  保存成功: {success_count}/{len(paragraphs)} 段落翻译成功")
        return True
    except Exception as e:
        print(f"  保存失败: {e}")
        return False

def check_article_needs_translation(article_file):
    """检查文章是否需要翻译"""
    try:
        with open(article_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否已经翻译过
        if 'paragraphs' in data and data['paragraphs']:
            # 检查是否有段落需要翻译
            for para in data['paragraphs']:
                translated = para.get('translated', '')
                if translated.startswith('[待翻译]') or translated.startswith('[翻译失败]') or translated == '':
                    return True
            return False
        else:
            # 没有paragraphs字段，需要翻译
            return True
    except:
        return True

def translate_batch(data_dir, api_key):
    """批量翻译所有未完成的文章"""
    translator = SimpleTranslator(api_key)
    processed_dir = os.path.join(data_dir, 'processed')
    
    # 获取所有需要翻译的文章
    articles_to_translate = []
    
    for filename in sorted(os.listdir(processed_dir)):
        if filename.endswith('.json'):
            article_file = os.path.join(processed_dir, filename)
            if check_article_needs_translation(article_file):
                articles_to_translate.append(article_file)
    
    print(f"找到 {len(articles_to_translate)} 篇文章需要翻译")
    
    if not articles_to_translate:
        print("所有文章已完成翻译！")
        return True
    
    # 批量翻译
    success_count = 0
    failed_count = 0
    
    for i, article_file in enumerate(articles_to_translate):
        print(f"\n进度: {i+1}/{len(articles_to_translate)}")
        
        try:
            if translate_article(article_file, translator):
                success_count += 1
                print(f"✓ 成功翻译: {os.path.basename(article_file)}")
            else:
                failed_count += 1
                print(f"✗ 翻译失败: {os.path.basename(article_file)}")
        except Exception as e:
            failed_count += 1
            print(f"✗ 翻译异常: {os.path.basename(article_file)} - {e}")
    
    print(f"\n批量翻译完成:")
    print(f"  成功: {success_count} 篇")
    print(f"  失败: {failed_count} 篇")
    print(f"  总计: {success_count + failed_count} 篇")
    
    return failed_count == 0

def translate_single_article(article_id, data_dir, api_key):
    """翻译单篇文章"""
    translator = SimpleTranslator(api_key)
    
    # 查找文章文件
    processed_dir = os.path.join(data_dir, 'processed')
    article_file = None
    
    # 先按ID查找
    for filename in os.listdir(processed_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(processed_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('id') == int(article_id):
                        article_file = os.path.join(processed_dir, filename)
                        break
            except:
                continue
    
    # 如果没找到，按文件名查找
    if not article_file:
        filename = f"{article_id}.json"
        potential_path = os.path.join(processed_dir, filename)
        if os.path.exists(potential_path):
            article_file = potential_path
    
    if not article_file:
        print(f"错误: 未找到文章ID {article_id}")
        return False
    
    return translate_article(article_file, translator)

if __name__ == "__main__":
    # API密钥
    API_KEY = "sk-eldyazgvnveplwgemudldehsftzrcwiiyufyijefpmntmqud"
    
    # 数据目录
    DATA_DIR = "data"
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "single" and len(sys.argv) > 2:
            # 翻译单篇文章
            article_id = sys.argv[2]
            translate_single_article(article_id, DATA_DIR, API_KEY)
        
        elif command == "batch":
            # 批量翻译所有未完成的文章
            translate_batch(DATA_DIR, API_KEY)
        
        else:
            print("用法:")
            print("  python translate_simple.py single <article_id>  # 翻译单篇文章")
            print("  python translate_simple.py batch               # 批量翻译所有未完成的文章")
            print("示例:")
            print("  python translate_simple.py single field")
            print("  python translate_simple.py batch")
    
    else:
        print("用法:")
        print("  python translate_simple.py single <article_id>  # 翻译单篇文章")
        print("  python translate_simple.py batch               # 批量翻译所有未完成的文章")
        print("示例:")
        print("  python translate_simple.py single field")
        print("  python translate_simple.py batch")