#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

def extract_article_content(article_url):
    """抓取并提取文章内容"""
    try:
        print(f"  正在抓取: {article_url}")
        response = requests.get(article_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 移除不需要的元素
        for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
            unwanted.decompose()
        
        # 尝试找到主要内容容器
        content_selectors = [
            'table',  # Paul Graham 网站主要使用table布局
            'body',
            'main',
            '.content',
            '#content'
        ]
        
        main_content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                main_content = content
                break
        
        if not main_content:
            main_content = soup
        
        # 提取文本并分段
        full_text = main_content.get_text()
        
        # 清理和分段
        paragraphs = split_into_paragraphs(full_text)
        
        return {
            "success": True,
            "paragraphs": paragraphs,
            "word_count": len(full_text.split()),
            "paragraph_count": len(paragraphs)
        }
        
    except Exception as e:
        print(f"    错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "paragraphs": [],
            "word_count": 0,
            "paragraph_count": 0
        }

def split_into_paragraphs(text):
    """将文本智能分段"""
    # 清理文本
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 按段落分割（双换行或句号后换行）
    paragraphs = []
    
    # 按句号分割，但保留一些连接
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_paragraph = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 如果当前段落为空或者很短，添加句子
        if len(current_paragraph) < 200:
            current_paragraph += sentence + " "
        else:
            # 保存当前段落并开始新段落
            if current_paragraph.strip():
                paragraphs.append(current_paragraph.strip())
            current_paragraph = sentence + " "
    
    # 添加最后一个段落
    if current_paragraph.strip():
        paragraphs.append(current_paragraph.strip())
    
    # 过滤掉太短的段落
    paragraphs = [p for p in paragraphs if len(p.split()) > 5]
    
    return paragraphs

def process_all_articles():
    """处理所有文章"""
    
    # 读取文章列表
    try:
        with open('data/articles.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"加载了 {len(articles)} 篇文章")
    except Exception as e:
        print(f"读取文章列表失败: {e}")
        return
    
    # 检查已处理的文章
    processed_files = set()
    if os.path.exists('data/processed'):
        processed_files = set(os.listdir('data/processed'))
    
    print(f"已处理文件: {len(processed_files)} 个")
    
    # 处理文章
    batch_size = 10  # 每批处理10篇
    success_count = 0
    error_count = 0
    
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        print(f"\n处理第 {i//batch_size + 1} 批 ({i+1}-{min(i+batch_size, len(articles))}/{len(articles)})")
        
        for j, article in enumerate(batch):
            filename = article['filename'].replace('.html', '.json')
            
            # 跳过已处理的文章
            if filename in processed_files:
                print(f"  {i+j+1}. 跳过已处理: {article['title']}")
                success_count += 1
                continue
            
            print(f"  {i+j+1}. 处理: {article['title']}")
            
            # 抓取文章内容
            content_result = extract_article_content(article['url'])
            
            # 准备保存的数据
            processed_article = {
                "title": article['title'],
                "title_zh": article.get('title_zh', f"[待翻译] {article['title']}"),
                "url": article['url'],
                "filename": article['filename'],
                "date": article.get('date', 'Unknown'),
                "id": article['id'],
                "content": content_result,
                "processed_at": datetime.now().isoformat()
            }
            
            # 为内容添加翻译占位符
            if content_result['success']:
                processed_paragraphs = []
                for para in content_result['paragraphs']:
                    processed_paragraphs.append({
                        "original": para,
                        "translated": f"[待翻译] {para[:50]}..." if len(para) > 50 else f"[待翻译] {para}"
                    })
                processed_article['paragraphs'] = processed_paragraphs
            else:
                processed_article['paragraphs'] = []
            
            # 保存处理后的文章
            try:
                output_path = f'data/processed/{filename}'
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_article, f, ensure_ascii=False, indent=2)
                
                if content_result['success']:
                    print(f"    ✓ 成功: {content_result['paragraph_count']} 段, {content_result['word_count']} 词")
                    success_count += 1
                else:
                    print(f"    ✗ 失败: {content_result.get('error', '未知错误')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"    ✗ 保存失败: {e}")
                error_count += 1
            
            # 添加延时避免请求过于频繁
            time.sleep(0.5)
        
        # 批次间休息
        if i + batch_size < len(articles):
            print("休息3秒...")
            time.sleep(3)
    
    print(f"\n处理完成！成功: {success_count}, 失败: {error_count}")
    
    # 生成统计报告
    generate_processing_report()

def generate_processing_report():
    """生成处理报告"""
    try:
        processed_files = [f for f in os.listdir('data/processed') if f.endswith('.json')]
        
        print(f"\n处理报告:")
        print(f"已处理文章数: {len(processed_files)}")
        
        # 统计成功率
        success_count = 0
        total_paragraphs = 0
        total_words = 0
        
        for filename in processed_files[:5]:  # 只检查前5个作为样本
            try:
                with open(f'data/processed/{filename}', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('content', {}).get('success', False):
                    success_count += 1
                    total_paragraphs += data['content'].get('paragraph_count', 0)
                    total_words += data['content'].get('word_count', 0)
            except:
                pass
        
        if success_count > 0:
            print(f"平均段落数: {total_paragraphs // success_count}")
            print(f"平均词数: {total_words // success_count}")
        
    except Exception as e:
        print(f"生成报告失败: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("开始抓取所有文章内容...")
    process_all_articles()