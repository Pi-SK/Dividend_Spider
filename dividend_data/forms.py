from django import forms
from django_select2.forms import Select2Widget, Select2MultipleWidget
from django.forms.widgets import DateInput
from django.db.models import Min, Max
from datetime import datetime

from .models import Dividend

class QueryForm_Dividend(forms.Form):
    stock_code_choices = [('', '---------')] + list(Dividend.objects.order_by('stock_code').values_list('stock_code','stock_code').distinct())
    stock_code = forms.MultipleChoiceField(
        choices=stock_code_choices,
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'select2', 'data-placeholder': '不限股票代码', 'style': 'width: 8rem;'})
    )
    company_name_choices = [('', '---------')] + list(Dividend.objects.order_by('company_name').values_list('company_name', 'company_name').distinct())
    company_name = forms.MultipleChoiceField(
        choices=company_name_choices,
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'select2', 'data-placeholder': '不限公司名称', 'style': 'width: 9rem;'})
    )

    # 计算Dividend中最小和最大的announcement_date年份
    min_year = Dividend.objects.aggregate(min_year=Min('announcement_date__year'))['min_year']
    max_year = Dividend.objects.aggregate(max_year=Max('announcement_date__year'))['max_year']
    # 如果没有数据，则默认当前年份
    if not min_year:
        min_year = datetime.now().year
    if not max_year:
        max_year = datetime.now().year
    # 创建年份选择列表
    announcement_year_choices = [(str(year), str(year)) for year in range(min_year, max_year + 1)]
    # print(announcement_year_choices)
    announcement_year_start = forms.ChoiceField(
        choices=announcement_year_choices,
        required=False,
        widget=Select2Widget(attrs={'class': 'select2', 'data-placeholder': '开始年份', 'style': 'width: 8rem;'})
    )
    announcement_year_end = forms.ChoiceField(
        choices=announcement_year_choices,
        required=False,
        widget=Select2Widget(attrs={'class': 'select2', 'data-placeholder': '结束年份', 'style': 'width: 8rem;'})
    )

    default_values_choices = [
        ('dividend_year', '分红年份'),
        ('total_stock_bonus_ratio', '送转股总比例'),
        ('bonus_stock_ratio', '送股比例'),
        ('convert_stock_ratio', '转股比例'),
        ('cash_dividend_ratio', '现金分红比例'),
        ('dividend_yield', '股息率'),
        ('earnings_per_share', '每股收益'),
        ('net_asset_per_share', '每股净资产'),
        ('reserve_per_share', '每股公积金'),
        ('undistributed_profit_per_share', '每股未分配利润'),
        ('net_profit_growth_rate', '净利润增长率'),
    ]
    default_values = forms.MultipleChoiceField(
        choices=default_values_choices,
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'select2', 'data-placeholder': '请选择清洗列', 'style': 'width: 9rem;'})
    )
