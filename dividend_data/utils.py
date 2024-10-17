from datetime import datetime
import pandas as pd
import json
import os

# -----------------------------------------------------------

def set_proxies():
    pass

# -----------------------------------------------------------

def set_cookies():
    pass

# -----------------------------------------------------------

def Eastmoney_json_to_table(fold_path, migrate_to_db=False, save_csv=(True, './crawled_csv_data')):
    '''
    将原始json文件转换为DataFrame格式
    '''

    # 遍历指定文件夹的所有文件
    timestamps = []
    mapped_data = []
    for file_path in os.listdir(fold_path):
        if file_path.endswith('-data.json'):
            file_name = os.path.basename(file_path)
            timestamp = file_name[6:16]
            timestamps.append(timestamp)
            full_file_path = os.path.join(fold_path, file_name)

            with open(full_file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                for _, each_page_item in data.items():
                    for item in each_page_item:
                        mapped_item = {
                            "序号": 0,
                            "股票代码": item["SECURITY_CODE"],
                            "公司名称": item["SECURITY_NAME_ABBR"],
                            "分红年份": item["EX_DIVIDEND_DATE"].split(" ")[0] if item["EX_DIVIDEND_DATE"] else None,
                            "公告日期": item["PLAN_NOTICE_DATE"].split(" ")[0] if item["PLAN_NOTICE_DATE"] else None,
                            "送转股总比例": item["BONUS_IT_RATIO"]/10 if item["BONUS_IT_RATIO"] else None,
                            "送股比例": item["BONUS_RATIO"]/10 if item["BONUS_RATIO"] else None,
                            "转股比例": item["IT_RATIO"]/10 if item["IT_RATIO"] else None,
                            "现金分红比例": item["PRETAX_BONUS_RMB"]/10 if item["PRETAX_BONUS_RMB"] else None,
                            "股息率": item["DIVIDENT_RATIO"],
                            "每股收益": item["BASIC_EPS"],
                            "每股净资产": item["BVPS"],
                            "每股公积金": item["PER_CAPITAL_RESERVE"],
                            "每股未分配利润": item["PER_UNASSIGN_PROFIT"],
                            "净利润同比增长率": item["PNP_YOY_RATIO"]
                        }
                        mapped_data.append(mapped_item)
            print(f'{timestamp}已处理')
        else:
            continue
    
    # 按照股票代码和公告日期排序
    mapped_data.sort(key=lambda x: (x['股票代码'], datetime.strptime(x['公告日期'], '%Y-%m-%d')))

    # 迁移到数据库
    if migrate_to_db:
        from .models import Dividend

        for i, mapped_item in enumerate(mapped_data, start=1):
            defaults = {
                'series_num': i,
                'stock_code': mapped_item['股票代码'],
                'company_name': mapped_item['公司名称'],
                'dividend_year': datetime.strptime(mapped_item['分红年份'], '%Y-%m-%d').date() if mapped_item['分红年份'] else None,
                'announcement_date': datetime.strptime(mapped_item['公告日期'], '%Y-%m-%d').date(),
                'total_stock_bonus_ratio': mapped_item['送转股总比例'],
                'bonus_stock_ratio': mapped_item['送股比例'],
                'convert_stock_ratio': mapped_item['转股比例'],
                'cash_dividend_ratio': mapped_item['现金分红比例'],
                'dividend_yield': mapped_item['股息率'],
                'earnings_per_share': mapped_item['每股收益'],
                'net_asset_per_share': mapped_item['每股净资产'],
                'reserve_per_share': mapped_item['每股公积金'],
                'undistributed_profit_per_share': mapped_item['每股未分配利润'],
                'net_profit_growth_rate': mapped_item['净利润同比增长率'],
            }
            # 使用update_or_create来批量创建或更新记录
            obj, created = Dividend.objects.update_or_create(
                stock_code=mapped_item['股票代码'],
                announcement_date=datetime.strptime(mapped_item['公告日期'], '%Y-%m-%d').date(),
                defaults=defaults)
            if i % 1000 == 0:
                print(f'{i}条数据已迁移')
        print('\n数据迁移完成')

    # 保存数据
    if save_csv[0]:
        df = pd.DataFrame(mapped_data)
        # 数据清洗
        # data_cleaning(df)
        timestamps.sort()
        time = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_name = f'{timestamps[0]}_to_{timestamps[-1]}-{time}.csv'
        save_path = save_csv[1] if save_csv[1] else '.'
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        full_path = os.path.join(save_path, save_name)
        df.to_csv(full_path, index=False, encoding='utf-8-sig')
        print(f'数据已保存至{full_path}')

    flag = True
    return mapped_data, flag

# -----------------------------------------------------------

def data_cleaning(df: pd.DataFrame):
    '''
    数据清洗：删除空值，删除重复值，删除异常值
    '''
    original_row_count = df.shape[0]

    # 删除空值
    # 删除"股票代码"、"公司名称"、"每股收益"三列中只要有一列为空的行
    df.dropna(subset=['股票代码', '公司名称', '每股收益'], inplace=True)

    # 删除重复值
    df.drop_duplicates(inplace=True)

    # 删除异常值
    # 删除每股收益为负数的行
    df = df[df['每股收益'] > 0]
    # 删除每股净资产为负数的行
    df = df[df['每股净资产'] > 0]
    # 删除每股公积金为负数的行
    df = df[df['每股公积金'] > 0]
    # 删除每股未分配利润为负数的行
    df = df[df['每股未分配利润'] > 0]

    print('数据清洗完成')

    print(original_row_count - df.shape[0])

# -----------------------------------------------------------

def export_to_csv(request, queryset, fields, filename, custom_field_names=None):
    import csv
    from django.http import HttpResponse

    # 如果提供了自定义列名，则使用它们；否则使用 fields 列表
    field_names = custom_field_names if custom_field_names else fields

    # 创建 HttpResponse 对象，并指定编码格式为 UTF-8
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(filename)

    writer = csv.writer(response, quoting=csv.QUOTE_MINIMAL)  # 使用 QUOTE_MINIMAL 来避免不必要的引号
    writer.writerow(field_names)  # 写入自定义列名

    for obj in queryset:
        row = []
        for field in fields:
            # 如果字段包含 '__'，表示是跨关联模型的字段，需要特殊处理
            if '__' in field:
                related_fields = field.split('__')
                value = getattr(obj, related_fields[0])
                for related_field in related_fields[1:]:
                    value = getattr(value, related_field)
            else:
                value = getattr(obj, field)

            if isinstance(value, int):
                value = str(value).zfill(6)
            else:
                value = str(value)
            row.append(str(value))
        writer.writerow(row)

    return response

# -----------------------------------------------------------

if __name__ == '__main__':
    import django

    fold_path = 'crawled_json_data/crawled_json_data-20241017_120909'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dividend_spider.settings')
    django.setup()
    Eastmoney_json_to_table(fold_path, migrate_to_db=True, save_csv=(False, None))


# -----------------------------------------------------------

# 进行了性能优化

# def Eastmoney_json_to_table(fold_path, migrate_to_db=False, save_csv=(True, './crawled_csv_data')):
#     mapped_data = []
#     timestamps = []

#     def parse_date(date_str):
#         return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

#     for file_path in os.listdir(fold_path):
#         if file_path.endswith('-data.json'):
#             full_file_path = os.path.join(fold_path, file_path)
#             timestamp = file_path[6:16]
#             timestamps.append(timestamp)

#             with open(full_file_path, 'r', encoding='utf-8-sig') as f:
#                 data = json.load(f)
#                 for _, each_page_item in data.items():
#                     for item in each_page_item:
#                         mapped_item = {
#                             "序号": 0,
#                             "股票代码": item["SECURITY_CODE"],
#                             "公司名称": item["SECURITY_NAME_ABBR"],
#                             "分红年份": item["EX_DIVIDEND_DATE"].split(" ")[0] if item["EX_DIVIDEND_DATE"] else None,
#                             "公告日期": item["PLAN_NOTICE_DATE"].split(" ")[0] if item["PLAN_NOTICE_DATE"] else None,
#                             "送转股总比例": item["BONUS_IT_RATIO"]/10 if item["BONUS_IT_RATIO"] else None,
#                             "送股比例": item["BONUS_RATIO"]/10 if item["BONUS_RATIO"] else None,
#                             "转股比例": item["IT_RATIO"]/10 if item["IT_RATIO"] else None,
#                             "现金分红比例": item["PRETAX_BONUS_RMB"]/10 if item["PRETAX_BONUS_RMB"] else None,
#                             "股息率": item["DIVIDENT_RATIO"],
#                             "每股收益": item["BASIC_EPS"],
#                             "每股净资产": item["BVPS"],
#                             "每股公积金": item["PER_CAPITAL_RESERVE"],
#                             "每股未分配利润": item["PER_UNASSIGN_PROFIT"],
#                             "净利润同比增长率": item["PNP_YOY_RATIO"]
#                         }
#                         mapped_data.append(mapped_item)
#             print(f'{timestamp}已处理')

#     # 重新排序和编号
#     mapped_data.sort(key=lambda x: (x['股票代码'], x['公告日期']))
#     for i, mapped_item in enumerate(mapped_data, start=1):
#         mapped_item['序号'] = i
    
#     print(mapped_data[:5])

#     # 数据库迁移
#     if migrate_to_db:
#         from .models import Dividend

#         # 创建和更新操作的分离
#         to_create = []
#         to_update = []
#         existing_records = {f"{item.stock_code}_{item.announcement_date.isoformat()}": item for item in Dividend.objects.all()}

#         for mapped_item in mapped_data:
#             key = f"{mapped_item['股票代码']}_{parse_date(mapped_item['公告日期']).isoformat()}"
#             if key in existing_records:
#                 obj = existing_records[key]
#                 # 更新对象属性
#                 for field, value in mapped_item.items():
#                     setattr(obj, field, value)
#                 to_update.append(obj)
#             else:
#                 # 创建新对象
#                 # to_create.append(Dividend(
#                 #     series_num=mapped_item['序号'],
#                 #     stock_code=mapped_item['股票代码'],
#                 #     company_name=mapped_item['公司名称'],
#                 #     dividend_year=parse_date(mapped_item['分红年份']) if mapped_item['分红年份'] else None,
#                 #     announcement_date=parse_date(mapped_item['公告日期']),
#                 #     total_stock_bonus_ratio=mapped_item['送转股总比例'],
#                 #     bonus_stock_ratio=mapped_item['送股比例'],
#                 #     convert_stock_ratio=mapped_item['转股比例'],
#                 #     cash_dividend_ratio=mapped_item['现金分红比例'],
#                 #     dividend_yield=mapped_item['股息率'],
#                 #     earnings_per_share=mapped_item['每股收益'],
#                 #     net_asset_per_share=mapped_item['每股净资产'],
#                 #     reserve_per_share=mapped_item['每股公积金'],
#                 #     undistributed_profit_per_share=mapped_item['每股未分配利润'],
#                 #     net_profit_growth_rate=mapped_item['净利润同比增长率']
#                 # ))
#                 instance = Dividend(
#                     series_num=mapped_item['序号'],
#                     stock_code=mapped_item['股票代码'],
#                     company_name=mapped_item['公司名称'],
#                     dividend_year=parse_date(mapped_item['分红年份']) if mapped_item['分红年份'] else None,
#                     announcement_date=parse_date(mapped_item['公告日期']),
#                     total_stock_bonus_ratio=mapped_item['送转股总比例'],
#                     bonus_stock_ratio=mapped_item['送股比例'],
#                     convert_stock_ratio=mapped_item['转股比例'],
#                     cash_dividend_ratio=mapped_item['现金分红比例'],
#                     dividend_yield=mapped_item['股息率'],
#                     earnings_per_share=mapped_item['每股收益'],
#                     net_asset_per_share=mapped_item['每股净资产'],
#                     reserve_per_share=mapped_item['每股公积金'],
#                     undistributed_profit_per_share=mapped_item['每股未分配利润'],
#                     net_profit_growth_rate=mapped_item['净利润同比增长率']
#                 )
#                 instance.save()
#                 if i % 1000 == 0:
#                     print(f'{i}条新增数据已迁移')
        
#         print(to_create)
#         print('\n', to_update)
#         print('开始数据库迁移...')

#         # 批量创建新记录
#         # Dividend.objects.bulk_create(to_create)
#         # 批量更新现有记录
#         Dividend.objects.bulk_update(to_update, ['series_num', 'stock_code', 'company_name', 'dividend_year', 'announcement_date', 'total_stock_bonus_ratio', 'bonus_stock_ratio', 'convert_stock_ratio', 'cash_dividend_ratio', 'dividend_yield', 'earnings_per_share', 'net_asset_per_share', 'reserve_per_share', 'undistributed_profit_per_share', 'net_profit_growth_rate'])

#         print('数据库迁移完成')

#     # 保存到CSV
#     if save_csv[0]:
#         df = pd.DataFrame(mapped_data)
#         timestamps.sort()
#         time = datetime.now().strftime("%Y%m%d_%H%M%S")
#         save_name = f'{timestamps[0]}_to_{timestamps[-1]}-{time}.csv'
#         save_path = save_csv[1] if save_csv[1] else '.'
#         os.makedirs(save_path, exist_ok=True)
#         full_path = os.path.join(save_path, save_name)
#         df.to_csv(full_path, index=False, encoding='utf-8-sig')
#         print(f'数据已保存至{full_path}')

#     return mapped_data, True
