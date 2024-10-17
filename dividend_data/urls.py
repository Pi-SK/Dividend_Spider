from django.urls import path
from . import views

app_name = "dividend_data"
urlpatterns = [
    path('eastmoney/', views.DividendListView.as_view(), name='eastmoney'),
    path('to_csv/', views.export_dividends_to_csv, name='csv'),
    path('run_crawler/', views.run_crawler, name='run_crawler'),
    path('crawler/', views.to_spider, name='crawler'),
    path('crawler_status/', views.to_result, name='crawler_status'),
    path('delete_all/', views.delete_all, name='delete_all'),
    path('to_delete_all/', views.to_delete, name='to_delete_all'),
    path('charts/<str:stock_code>/', views.dividend_charts, name='dividend_charts'),
]