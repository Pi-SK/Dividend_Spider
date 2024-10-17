from django.db import models

class Dividend(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    series_num = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="序号")
    stock_code = models.CharField(max_length=20, verbose_name="股票代码")
    company_name = models.CharField(max_length=100, verbose_name="公司名称")
    dividend_year = models.DateField(max_length=10, null=True, blank=True, verbose_name="分红年份")
    announcement_date = models.DateField(max_length=10, verbose_name="公告日期")
    total_stock_bonus_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="送转股总比例")
    bonus_stock_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="送股比例")
    convert_stock_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="转股比例")
    cash_dividend_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="现金分红比例")
    dividend_yield = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="股息率")
    earnings_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="每股收益")
    net_asset_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="每股净资产")
    reserve_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="每股公积金")
    undistributed_profit_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="每股未分配利润")
    net_profit_growth_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="净利润同比增长率")

    class Meta:
        verbose_name = "股票分红信息"
        verbose_name_plural = "股票分红信息"
        unique_together = ('stock_code', 'announcement_date')

    def __str__(self):
        return f'{self.stock_code} - {self.company_name} - {self.announcement_date}'