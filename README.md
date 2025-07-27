# Paul Graham 文章中文博客

一个简约的博客网站，展示 Paul Graham 文章的中英文对照翻译。

## 功能特点

- 📚 完整的 Paul Graham 文章列表（232篇）
- 🔍 文章搜索功能
- 📖 中英文对照阅读
- 📱 响应式设计，支持移动端
- 🎨 简约美观的界面设计

## 项目结构

```
paul_blog/
├── index.html          # 首页 - 文章列表
├── article.html        # 文章详情页
├── server.py          # 本地开发服务器
├── scraper.py         # 文章列表抓取脚本
├── article_processor.py # 文章内容处理脚本
├── data/
│   ├── articles.json   # 文章列表数据
│   └── processed/     # 处理后的文章数据
└── venv/              # Python虚拟环境
```

## 快速开始

### 1. 启动本地服务器

```bash
cd paul_blog
python3 server.py
```

### 2. 访问网站

打开浏览器访问: http://localhost:8000

## 主要页面

### 首页 (index.html)
- 显示所有文章列表
- 支持实时搜索
- 点击文章标题进入详情页

### 文章详情页 (article.html)
- 支持三种阅读模式：
  - **对照阅读**: 中英文并排显示
  - **仅英文**: 只显示原文
  - **仅中文**: 只显示翻译
- 美观的渐变背景
- 返回首页功能

## 数据处理

### 抓取文章列表
```bash
source venv/bin/activate
python scraper.py
```

### 处理文章内容
```bash
source venv/bin/activate
python article_processor.py
```

## 技术特点

- 纯 HTML/CSS/JavaScript，无框架依赖
- 响应式设计，适配各种屏幕尺寸
- 本地数据存储，快速加载
- 简洁的代码结构，易于维护

## 注意事项

- 翻译功能目前为示例实现，需要集成实际翻译服务
- 文章内容抓取受网站结构影响，可能需要调整
- 建议合理控制抓取频率，避免对原网站造成压力

## 扩展建议

1. 集成专业翻译API（如Google Translate、DeepL等）
2. 添加文章收藏功能
3. 实现全文搜索
4. 添加阅读进度记录
5. 支持暗色主题
6. 添加评论系统

## 许可证

本项目仅供学习和个人使用。Paul Graham 的文章版权归原作者所有。