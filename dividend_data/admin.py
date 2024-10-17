from django.contrib import admin
from .models import Dividend


class DividendAdmin(admin.ModelAdmin):
    # 列表页显示的字段
    list_display = ('stock_code', 'company_name', 'dividend_year', 'dividend_amount')
    
    # 列表页的搜索字段
    search_fields = ['stock_code', 'company_name']
    
    # 列表页的过滤器
    list_filter = ['dividend_year']

# 注册Dividend模型
admin.site.register(Dividend)
