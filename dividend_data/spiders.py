from datetime import datetime
import random
import time
import requests
import json
import os

from .utils import set_proxies

# -----------------------------------------------------------

class EastmoneySpider():
    def __init__(self, 
                 url = 'https://datacenter-web.eastmoney.com/api/data/v1/get', 
                 headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br, zstd',
                    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
                    'cache-control': 'no-cache',
                    'connection': 'keep-alive',
                    'host': 'datacenter-web.eastmoney.com',
                    'pragma': 'no-cache',
                    'referer': 'https://data.eastmoney.com/yjfp/',
                    'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'script',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
                }):
        self.url = url
        self.headers = headers


    # 解包
    def read_response_to_json(self, response):
        # 确保response参数被传递
        if response is None:
            print("No response provided.")
            return
        if response.status_code == 200:
            # 获取响应内容
            content = response.text
            content = extract_outer_parentheses(content)
            # 尝试解析JSON
            try:
                response_data = json.loads(content)
                # 处理成功响应
                # print(response_data['result'])
                return response_data
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Response content: {response.text}")
        else:
            print(f'Failed to retrieve data: {response.status_code}')


    # 翻页爬取
    def crawl_with_pager(self, params, file_name='data.json', file_path='./crawled_json_data', delay_range=(2, 5), proxy_list=None):
        # 设置User-Agent列表，随机选择一个进行请求
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
            "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10"
        ]
        self.headers['user-agent'] = random.choice(user_agents)

        # 设置随机延迟时间，由于在访问一个时间戳的时候不需设置延迟，因此只在每次切换时间戳时设置
        time.sleep(random.uniform(*delay_range))

        page = 1
        total_data = {}
        while True:
            params['pageNumber'] = f'{page}'

            # 如果提供了代理列表，则随机选择一个代理
            proxy = random.choice(proxy_list) if proxy_list else None

            response = requests.get(self.url, params=params, headers=self.headers, proxies={"http": proxy, "https": proxy})
            response_data = self.read_response_to_json(response)

            if response_data['result']:
                total_data[f'page_{page}'] = response_data['result']['data']
                print(f'Page {page} crawled successfully.')
                page += 1
            elif page >= 1000:
                print('Pages up to 1000')
                save_json(total_data, file_name=f'total-{file_name}', file_path=file_path)
                break
            else:
                print('No more pages')
                save_json(total_data, file_name=f'total-{file_name}', file_path=file_path)
                break

        return total_data, page


    # 提取时间戳，支持选择时间段，选择只看年报
    def extract_timestamp(self, dict_data: dict, start_date=None, end_date=None, only_yearly=True):
        timestamps = []
        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        for each_page in dict_data.items():
            for item in each_page[1]:
                report_date_str = item["REPORT_DATE"].split(" ")[0]
                report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
                # 如果only_yearly为True，则只添加12月31日的日期
                if only_yearly and report_date.month == 12 and report_date.day == 31:
                    # 如果指定了开始日期和结束日期，则进行过滤
                    if start_date and end_date:
                        if start_date <= report_date <= end_date:
                            timestamps.append(report_date_str)
                    else:
                        timestamps.append(report_date_str)
                elif not only_yearly:
                    if start_date and end_date:
                        if start_date <= report_date <= end_date:
                            timestamps.append(report_date_str)
                    else:
                        timestamps.append(report_date_str)
        return timestamps


    # 爬取东方财富分红数据
    def fetch_eastmoney_data(self, start_date=None, end_date=None, only_yearly=True, file_path='./crawled_json_data', delay_range=(2, 5), proxy_list=None):
        # 首先获取所有的时间筛选条件
        params_time = {
            'callback': 'jQuery112305117127591348687_1728561329461',
            'reportName': 'RPT_DATE_SHAREBONUS_DET',
            'columns': 'ALL',
            'quoteColumns': '',
            'pageNumber': '1',
            'sortColumns': 'REPORT_DATE',
            'sortTypes': '-1',
            'source': 'WEB',
            'client': 'WEB',
            '_': '1728561329462'
        }
        timestamps, _ = self.crawl_with_pager(params_time, file_name='timestamp.json', file_path=file_path, delay_range=delay_range, proxy_list=proxy_list)
        timestamps = self.extract_timestamp(timestamps, start_date=start_date, end_date=end_date, only_yearly=only_yearly)

        # 其次根据时间遍历数据
        # 可以改变pageSize来调节效率
        params_data = {
            'callback': 'jQuery112305117127591348687_1728561329457',
            'sortColumns': 'PLAN_NOTICE_DATE',
            'sortTypes': '-1',
            'pageSize': '50',
            'pageNumber': '1',
            'reportName': 'RPT_SHAREBONUS_DET',
            'columns': 'ALL',
            'quoteColumns': '',
            'source': 'WEB',
            'client': 'WEB',
            'filter': "(REPORT_DATE = '2005-12-31')"  # 默认时间
        } 
        for timestamp in timestamps:
            params_data['filter'] = f"(REPORT_DATE = '{timestamp}')"
            print('\n', params_data['filter'])
            self.crawl_with_pager(params_data, file_name=f'{timestamp}-data.json', file_path=file_path, delay_range=delay_range, proxy_list=proxy_list)

# -----------------------------------------------------------

def extract_outer_parentheses(text):
    stack = []
    result = []
    start_index = None
    for i, char in enumerate(text):
        if char == '(':
            if not stack:
                start_index = i
            stack.append(char)
        elif char == ')':
            stack.pop()
            if not stack:
                result.append(text[start_index:i+1])

    return ''.join(result)[1:-1]


def save_json(response_data, file_name='data.json', file_path='data'):
    # 确保目录存在，如果不存在则创建
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    # 完整的文件路径
    full_file_path = os.path.join(file_path, file_name)
    try:
        # 写入JSON数据
        with open(full_file_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
        # 返回成功信息
        print(f'Save done: {full_file_path}')
    except Exception as e:
        # 异常处理，记录错误信息
        print(f'Error saving file: {e}')

# -----------------------------------------------------------

if __name__ == '__main__':
    spider = EastmoneySpider()
    spider.fetch_eastmoney_data('2014-12-31', '2024-12-31', only_yearly=True, delay_range=(2, 5), proxy_list=None)
    print('\n爬取完成')