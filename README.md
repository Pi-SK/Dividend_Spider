## 项目简介

本项目是一个基于Django框架的股票分红数据爬虫和展示系统。它可以从东方财富网站爬取股票分红数据，并将数据存储到Django数据库中，同时提供数据查询、导出和图表展示功能。

## 功能特点

- 从东方财富网站爬取股票分红数据
- 数据存储到Django数据库
- 提供数据查询、导出和图表展示功能

## 环境要求

- Python 3.7+
- Django 2.2+
- pandas
- matplotlib
- django_select2
- django-crispy-forms
- django-import-export

## 安装与配置

1. 克隆项目到本地

   ```
   git clone https://github.com/your-username/Dividend_Spider.git
   ```
2. 创建虚拟环境并激活

   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```
3. 安装依赖

   ```
   pip install -r requirements.txt
   ```
4. 配置数据库
   在 `dividend_spider/settings.py`文件中配置数据库连接信息。
5. 运行数据库迁移

   ```
   python manage.py migrate
   ```
6. 创建管理员账户

   ```
   python manage.py createsuperuser
   ```
7. 运行开发服务器

   ```
   python manage.py runserver
   ```

## 使用说明

1. 访问 `http://localhost:8000/admin`登录后台管理界面。
2. 在后台管理界面中，可以查看、添加、修改和删除股票分红数据。
3. 访问 `http://localhost:8000/dividend_data/eastmoney/`查看股票分红数据列表。
4. 访问 `http://localhost:8000/dividend_data/to_csv/`导出股票分红数据到CSV文件。
5. 访问 `http://localhost:8000/dividend_data/run_crawler/`运行爬虫程序。
6. 访问 `http://localhost:8000/dividend_data/charts/<stock_code>/`查看指定股票的分红图表。

## 许可证

本项目采用MIT许可证。有关详细信息，请查看LICENSE文件。

## 注意事项

- 请确保在使用本项目时遵守相关法律法规。
- 本项目仅供学习和研究使用，不应用于商业目的。
