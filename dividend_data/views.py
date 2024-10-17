from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView
from .models import Dividend
from .spiders import EastmoneySpider
from .utils import Eastmoney_json_to_table, export_to_csv
from .forms import QueryForm_Dividend
from datetime import datetime


class DividendListView(ListView):
    model = Dividend
    template_name = 'dividend_data/dividend_index.html'
    context_object_name = 'dividends'
    paginate_by = 30  # 设置每页显示的条目数量
    ordering = 'series_num'

    def get_queryset(self):
        form = QueryForm_Dividend(self.request.GET)

        if form.is_valid():
            stock_codes = form.cleaned_data.get('stock_code')
            company_names = form.cleaned_data.get('company_name')
            default_values = form.cleaned_data.get('default_values')
            announcement_year_start = form.cleaned_data.get('announcement_year_start')
            announcement_year_end = form.cleaned_data.get('announcement_year_end')
        
            default_values_dict = {
                'dividend_year': None,
                'total_stock_bonus_ratio': None, 
                'bonus_stock_ratio': None,
                'convert_stock_ratio': None,
                'cash_dividend_ratio': None,
                'dividend_yield': None,
                'earnings_per_share': None,
                'net_asset_per_share': None,
                'reserve_per_share': None,
                'undistributed_profit_per_share': None,
                'net_profit_growth_rate': None,
            }

            queryset = Dividend.objects.all()
            for stock_code in stock_codes:
                if stock_code:
                    queryset = queryset.filter(stock_code__icontains=stock_code)
            for company_name in company_names:
                if company_name:
                    queryset = queryset.filter(company_name__icontains=company_name)
            if announcement_year_start:
                start_date = datetime(int(announcement_year_start), 1, 1)
                queryset = queryset.filter(announcement_date__gte=start_date)
            if announcement_year_end:
                end_date = datetime(int(announcement_year_end), 12, 31)
                queryset = queryset.filter(announcement_date__lte=end_date)

            for value in default_values:
                if value in default_values_dict:
                    default_value = default_values_dict[value]
                    # 根据字段类型和缺省值进行过滤
                    if default_value is None:
                        queryset = queryset.exclude(**{value.replace(' ', '_').lower(): default_value})
                    else:
                        queryset = queryset.exclude(**{f"{value.replace(' ', '_').lower()}__icontains": default_value})
            
            queryset = queryset.order_by('series_num')
            return queryset
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = QueryForm_Dividend(self.request.GET)
        # 将查询结果暂时储存
        context['queryset'] = self.queryset

        # 获取分页器对象
        paginator = context.get('paginator')
        # 获取当前页对象
        page_obj = context.get('page_obj')
        # 添加分页器对象和当前页对象到上下文中
        context['paginator'] = paginator
        context['page_obj'] = page_obj

        return context
    
def to_spider(request):
    return render(request, 'dividend_data/spider.html')

def to_result(request):
    return render(request, 'dividend_data/sucess.html')

def run_crawler(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        only_yearly = request.POST.get('only_yearly') == 'True'
        time = datetime.now().strftime("%Y%m%d_%H%M%S")
        fold_path = f'crawled_json_data/crawled_json_data-{time}'
        
        spider = EastmoneySpider()
        spider.fetch_eastmoney_data(start_date=start_date, end_date=end_date, only_yearly=only_yearly, file_path=fold_path, delay_range=(2, 5), proxy_list=None)
        _, result = Eastmoney_json_to_table(fold_path, migrate_to_db=True, save_csv=(True, 'CSV'))
        if result:
            return render(request, 'dividend_data/sucess.html')
        else:
            return HttpResponse('爬虫运行失败')
    else:
        return render(request, 'dividend_data/spider.html')


def export_dividends_to_csv(request):
    import datetime
    from urllib.parse import quote

    fields = ['series_num', 'stock_code', 'company_name', 'dividend_year', 'announcement_date', 'total_stock_bonus_ratio', 'bonus_stock_ratio', 'convert_stock_ratio', 'cash_dividend_ratio', 'dividend_yield', 'earnings_per_share', 'net_asset_per_share', 'reserve_per_share', 'undistributed_profit_per_share', 'net_profit_growth_rate']
    fields_names = ['序号', '股票代码', '公司名称', '分红年份', '公告日期', '总股本分红比例', '送股比例', '转增比例', '现金分红比例', '股息率', '每股收益', '每股净资产', '每股公积金', '每股未分配利润', '净利润增长率']

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'东方财富分红数据_{timestamp}.csv'
    filename = quote(filename)

    queryset = Dividend.objects.all().order_by('series_num')

    return export_to_csv(request, queryset, fields, filename, fields_names)

def to_delete(request):
    return render(request, 'dividend_data/delete.html')

def delete_all(request):
    Dividend.objects.all().delete()
    return render(request, 'dividend_data/delete_done.html')


def dividend_charts(request, stock_code):
    from collections import defaultdict
    from decimal import Decimal
    import json

    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    # 查询数据库获取记录
    dividends = Dividend.objects.filter(stock_code=stock_code).order_by('announcement_date')

    # 准备数据用于前端绘图
    chart_data = defaultdict(lambda: defaultdict(list))
    for dividend in dividends:
        chart_data[dividend.announcement_date.year]['cash_dividend_ratio'].append(dividend.cash_dividend_ratio)
        chart_data[dividend.announcement_date.year]['dividend_yield'].append(dividend.dividend_yield)
        chart_data[dividend.announcement_date.year]['earnings_per_share'].append(dividend.earnings_per_share)
        chart_data[dividend.announcement_date.year]['net_asset_per_share'].append(dividend.net_asset_per_share)
        chart_data[dividend.announcement_date.year]['reserve_per_share'].append(dividend.reserve_per_share)
        chart_data[dividend.announcement_date.year]['undistributed_profit_per_share'].append(dividend.undistributed_profit_per_share)
        chart_data[dividend.announcement_date.year]['net_profit_growth_rate'].append(dividend.net_profit_growth_rate)

    # 对每个年份的数据进行平均处理，因为可能有多个记录对应同一个年份
    for year, data in chart_data.items():
        for key in data:
            data[key] = sum(data[key]) / len(data[key])
    
    years = sorted(chart_data.keys())

    chart_data = json.dumps(chart_data, default=decimal_default)
    chart_data = json.loads(chart_data)
    cash_dividend_ratios = list(map(float, [chart_data[str(year)]['cash_dividend_ratio'] for year in years]))
    dividend_yields = list(map(float, [chart_data[str(year)]['dividend_yield'] for year in years]))
    earnings_per_shares = list(map(float, [chart_data[str(year)]['earnings_per_share'] for year in years]))
    net_asset_per_shares = list(map(float, [chart_data[str(year)]['net_asset_per_share'] for year in years]))
    reserve_per_shares = list(map(float, [chart_data[str(year)]['reserve_per_share'] for year in years]))
    undistributed_profit_per_shares = list(map(float, [chart_data[str(year)]['undistributed_profit_per_share'] for year in years]))
    net_profit_growth_rates = list(map(float, [chart_data[str(year)]['net_profit_growth_rate'] for year in years]))

    # 传递数据到模板
    context = {
        'stock_code': stock_code,
        'company_name': dividends.first().company_name,
        'chart_data': json.dumps({
            'cash_dividend_ratio': cash_dividend_ratios,
            'dividend_yield': dividend_yields,
            'earnings_per_share': earnings_per_shares,
            'net_asset_per_share': net_asset_per_shares,
            'reserve_per_share': reserve_per_shares,
            'undistributed_profit_per_share': undistributed_profit_per_shares,
            'net_profit_growth_rate': net_profit_growth_rates,
        }),
        'years': years,
    }
    return render(request, 'dividend_data/dividend_charts.html', context)