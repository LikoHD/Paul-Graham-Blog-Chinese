#!/usr/bin/env python3
import json
from datetime import datetime

# 读取数据
with open('data/articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

# 修正不合理的日期（2025年的日期）
current_year = datetime.now().year
print('修正不合理的日期...')

for article in articles:
    if article['date'] != 'Unknown':
        try:
            date = datetime.strptime(article['date'], '%Y-%m-%d')
            if date.year > current_year:
                print(f'修正: {article["title"]} 从 {article["date"]} 改为 Unknown')
                article['date'] = 'Unknown'
        except:
            article['date'] = 'Unknown'

# 重新排序
valid_articles = [a for a in articles if a['date'] != 'Unknown']
unknown_articles = [a for a in articles if a['date'] == 'Unknown']

valid_articles.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
final_articles = valid_articles + unknown_articles

# 重新编号
for i, article in enumerate(final_articles):
    article['id'] = i + 1

# 保存
with open('data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(final_articles, f, ensure_ascii=False, indent=2)

print(f'完成！{len(valid_articles)} 篇有效日期，{len(unknown_articles)} 篇无日期')
print('\n最新5篇:')
for i in range(min(5, len(final_articles))):
    print(f'{i+1}. {final_articles[i]["title"]} - {final_articles[i]["date"]}')