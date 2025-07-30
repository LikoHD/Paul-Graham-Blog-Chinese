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

def fix_goodwriting():
    """重新抓取Good Writing文章"""
    
    # 读取文章列表
    with open('data/articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # 找到ID为2的文章
    article = next((a for a in articles if a['id'] == 2), None)
    
    if not article:
        print("未找到ID为2的文章")
        return
    
    print(f"重新抓取文章: {article['title']}")
    
    # 抓取文章内容
    content_result = extract_article_content(article['url'])
    
    # 准备保存的数据（使用新格式）
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
    output_path = f'data/processed/{article["filename"].replace(".html", ".json")}'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_article, f, ensure_ascii=False, indent=2)
    
    if content_result['success']:
        print(f"✓ 成功: {content_result['paragraph_count']} 段, {content_result['word_count']} 词")
        print(f"文件保存到: {output_path}")
    else:
        print(f"✗ 失败: {content_result.get('error', '未知错误')}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    fix_goodwriting()