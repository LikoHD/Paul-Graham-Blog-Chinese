#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

def scrape_articles_list():
    """抓取Paul Graham网站的文章列表"""
    url = "https://www.paulgraham.com/articles.html"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        
        # 查找所有文章链接
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            title = link.get_text().strip()
            
            # 过滤出文章链接（.html结尾且不是特殊页面）
            if (href.endswith('.html') and 
                not href.startswith('http') and 
                href not in ['articles.html', 'index.html'] and
                title and len(title) > 1):
                
                # 构建完整URL
                full_url = f"https://www.paulgraham.com/{href}"
                
                articles.append({
                    'title': title,
                    'url': full_url,
                    'filename': href
                })
        
        print(f"发现 {len(articles)} 篇文章，开始抓取发表时间...")
        
        # 为每篇文章抓取发表时间
        for i, article in enumerate(articles):
            print(f"正在处理 {i+1}/{len(articles)}: {article['title']}")
            date = scrape_article_date(article['url'])
            article['date'] = date
            
            # 添加延时避免请求过于频繁
            time.sleep(0.5)
        
        # 按日期排序（最新的在前）
        articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d') if x['date'] != 'Unknown' else datetime.min, reverse=True)
        
        # 添加序号
        for i, article in enumerate(articles):
            article['id'] = i + 1
        
        # 保存到JSON文件
        with open('data/articles.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"成功抓取 {len(articles)} 篇文章及其发表时间")
        return articles
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def scrape_article_date(article_url):
    """抓取单篇文章的发表时间"""
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        
        content = response.text
        
        # 尝试多种日期格式的正则表达式
        date_patterns = [
            r'(\w+ \d{4})',  # "July 2023", "January 2021"
            r'(\w+, \d{4})',  # "July, 2023"
            r'(\d{1,2}/\d{1,2}/\d{4})',  # "7/15/2023"
            r'(\d{4}-\d{2}-\d{2})',  # "2023-07-15"
            r'(\w+ \d{1,2}, \d{4})',  # "July 15, 2023"
        ]
        
        # 在页面开头部分查找日期（通常文章开头会有日期）
        first_part = content[:2000]  # 只查看前2000字符
        
        for pattern in date_patterns:
            matches = re.findall(pattern, first_part, re.IGNORECASE)
            for match in matches:
                # 尝试解析日期
                parsed_date = parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        # 如果找不到，在整个页面搜索
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        print(f"  警告: 无法找到发表时间 - {article_url}")
        return "Unknown"
        
    except Exception as e:
        print(f"  错误: 抓取文章时间失败 {article_url}: {e}")
        return "Unknown"

def parse_date_string(date_str):
    """解析日期字符串为标准格式"""
    try:
        # 月份映射
        months = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05',
            'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09', 'sept': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }
        
        date_str = date_str.strip().lower()
        
        # 处理 "July 2023" 格式
        if re.match(r'^\w+ \d{4}$', date_str):
            parts = date_str.split()
            month_name = parts[0]
            year = parts[1]
            if month_name in months:
                return f"{year}-{months[month_name]}-01"
        
        # 处理 "July 15, 2023" 格式
        if re.match(r'^\w+ \d{1,2}, \d{4}$', date_str):
            parts = date_str.replace(',', '').split()
            month_name = parts[0]
            day = parts[1].zfill(2)
            year = parts[2]
            if month_name in months:
                return f"{year}-{months[month_name]}-{day}"
        
        # 处理其他格式...
        # 如果无法解析，返回None
        return None
        
    except Exception:
        return None

def scrape_article_content(article_url):
    """抓取单篇文章内容"""
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找文章主体内容
        content_selectors = ['table', 'body', 'main', '.content']
        content = None
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                break
        
        if not content:
            content = soup
        
        # 清理不需要的元素
        for unwanted in content.find_all(['script', 'style', 'nav', 'header', 'footer']):
            unwanted.decompose()
        
        return content.get_text().strip()
        
    except Exception as e:
        print(f"抓取文章内容失败 {article_url}: {e}")
        return ""

if __name__ == "__main__":
    # 切换到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("开始抓取Paul Graham文章列表...")
    scrape_articles_list()