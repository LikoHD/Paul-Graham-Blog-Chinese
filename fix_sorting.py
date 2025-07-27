#!/usr/bin/env python3
import json
from datetime import datetime

def fix_article_sorting():
    """修正文章按日期降序排列"""
    
    # 读取现有数据
    with open('data/articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"处理 {len(articles)} 篇文章...")
    
    # 分离有日期和无日期的文章
    valid_articles = []
    unknown_articles = []
    
    for article in articles:
        if article['date'] != 'Unknown':
            try:
                # 验证日期格式并添加到有效列表
                datetime.strptime(article['date'], '%Y-%m-%d')
                valid_articles.append(article)
            except:
                # 如果日期格式有问题，添加到未知列表
                article['date'] = 'Unknown'
                unknown_articles.append(article)
        else:
            unknown_articles.append(article)
    
    # 按日期降序排序（最新的在前）
    valid_articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
    
    # 合并列表：有日期的在前，无日期的在后
    final_articles = valid_articles + unknown_articles
    
    # 重新编号
    for i, article in enumerate(final_articles):
        article['id'] = i + 1
    
    # 保存
    with open('data/articles.json', 'w', encoding='utf-8') as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)
    
    print(f"完成！{len(valid_articles)} 篇文章按日期排序，{len(unknown_articles)} 篇无日期")
    
    # 显示前10篇和后10篇
    print("\n最新10篇文章：")
    for i in range(min(10, len(final_articles))):
        article = final_articles[i]
        print(f"{i+1:3d}. {article['title']} - {article['date']}")
    
    if len(final_articles) > 10:
        print("\n最旧10篇文章：")
        start = max(0, len(final_articles) - 10)
        for i in range(start, len(final_articles)):
            article = final_articles[i]
            print(f"{i+1:3d}. {article['title']} - {article['date']}")

if __name__ == "__main__":
    fix_article_sorting()