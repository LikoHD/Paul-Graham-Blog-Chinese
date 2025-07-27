#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

def scrape_articles_with_dates():
    """分批抓取所有文章的真实发表时间"""
    
    # 首先加载现有的文章列表
    try:
        with open('data/articles.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"加载了 {len(articles)} 篇文章")
    except:
        print("未找到现有文章列表，请先运行 scraper.py")
        return
    
    print("开始抓取真实发表时间...")
    batch_size = 20  # 每批处理20篇文章
    
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        print(f"\n处理第 {i//batch_size + 1} 批 ({i+1}-{min(i+batch_size, len(articles))}/{len(articles)})")
        
        for j, article in enumerate(batch):
            print(f"  {i+j+1}. {article['title']}")
            date = scrape_article_date(article['url'])
            article['date'] = date
            print(f"     -> {date}")
            
            # 延时避免请求过于频繁
            time.sleep(0.3)
        
        # 每批次后保存进度
        print(f"保存进度...")
        save_articles_with_dates(articles)
        
        # 批次间休息
        if i + batch_size < len(articles):
            print("休息5秒...")
            time.sleep(5)
    
    print("\n排序和最终保存...")
    # 按日期排序（最新的在前）
    valid_articles = [a for a in articles if a['date'] != 'Unknown']
    unknown_articles = [a for a in articles if a['date'] == 'Unknown']
    
    valid_articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
    
    # 重新编号
    final_articles = valid_articles + unknown_articles
    for i, article in enumerate(final_articles):
        article['id'] = i + 1
    
    save_articles_with_dates(final_articles)
    print(f"完成！成功处理 {len(valid_articles)} 篇文章的发表时间，{len(unknown_articles)} 篇未找到时间")

def save_articles_with_dates(articles):
    """保存文章数据"""
    with open('data/articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def scrape_article_date(article_url):
    """抓取单篇文章的发表时间"""
    try:
        response = requests.get(article_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 先尝试从页面文本中找到日期
        # Paul Graham的文章通常在开头或结尾有日期
        page_text = soup.get_text()
        
        # 寻找常见的日期模式
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        
        # 在页面前2000字符中查找（通常文章开头有日期）
        header_text = page_text[:2000]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_date_string(match)
                if parsed_date and is_reasonable_date(parsed_date):
                    return parsed_date
        
        # 如果开头没找到，在页面结尾查找
        footer_text = page_text[-1000:]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, footer_text, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_date_string(match)
                if parsed_date and is_reasonable_date(parsed_date):
                    return parsed_date
        
        return "Unknown"
        
    except Exception as e:
        print(f"     错误: {e}")
        return "Unknown"

def is_reasonable_date(date_str):
    """检查日期是否合理（不能是未来时间，不能太早）"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        current_year = datetime.now().year
        
        # Paul Graham从1990年代开始写作，不应该超过当前年份
        return 1995 <= date.year <= current_year
    except:
        return False

def parse_date_string(date_str):
    """解析日期字符串为标准格式"""
    try:
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
        
        date_str = date_str.strip()
        
        # 处理 "July 2023" 或 "Jul 2023" 格式
        month_year_match = re.match(r'^(\w+)\s+(\d{4})$', date_str, re.IGNORECASE)
        if month_year_match:
            month_name = month_year_match.group(1).lower()
            year = month_year_match.group(2)
            if month_name in months:
                return f"{year}-{months[month_name]}-01"
        
        # 处理 "7/15/2023" 格式
        slash_date_match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if slash_date_match:
            month = slash_date_match.group(1).zfill(2)
            day = slash_date_match.group(2).zfill(2)
            year = slash_date_match.group(3)
            return f"{year}-{month}-{day}"
        
        # 处理 "2023-07-15" 格式
        iso_date_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
        if iso_date_match:
            return date_str
        
        return None
        
    except Exception:
        return None

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    scrape_articles_with_dates()