"""
针对post类型的请求，键的生成方法应该为url + form_data
"""

import hashlib
import datetime


class LogMod(object):
    """日志模块类"""

    def __init__(self):
        # 爬虫开始时间
        self.spider_start_time = None
        # 爬虫结束时间
        self.spider_end_time = None
        # 爬虫的总请求数量
        self.request_count = 0
        # 总共获取了多少条数据
        self.total_data_count = 0
        # 不同的字段总共获取了多少条数据
        self.total_key_data_count = 0
        # 单个请求的信息字典，key为该请求url的MD5值
        self.request_dict = dict()
        # 不同的网页类型的请求数量
        # 不同的网页类型获取的数据量
        # 各个状态码数据量统计

    def save_log_info(self):
        """保存日志信息"""
        # 计算总的请求数量
        self.request_count = len(self.request_dict)

        with open('log.txt', 'w', encoding='utf-8') as f:
            f.write("开始时间：" + str(self.spider_start_time) + '\r\n')
            f.write("结束时间：" + str(self.spider_end_time) + '\r\n')
            f.write("总请求数：" + str(self.request_count) + '\r\n')
            f.write("\r\n一下为单个请求统计\r\n")
            for request in self.request_dict.values():
                f.write(str(request))
                f.write('\r\n')

    def count_data(self, request_id, data_dict):
        """
        对解析后的数据进行统计
        :param request_id: 请求id
        :param data_dict: 解析后的数据
        :return:
        """
        # 解析后的数据列表
        data_list = data_dict['data']
        # 解析后的新请求列表
        new_request_list = data_dict['new_request']
        # 在请求字典中找到单个请求
        single_request = self.request_dict[request_id]
        # 该条请求获取的数据
        single_request['data_count'] = len(data_list)
        # 该条请求产生的新请求
        single_request['new_request_count'] = len(new_request_list)
        # 该条请求各个字段数据量统计
        single_request['key_data_count'] = dict()

        # 循环数据列表
        for data in data_list:
            # 循环单条数据字典
            for key, value in data.items():
                # 如果这个键还没有开始统计，则生成对应的键
                if key not in single_request['key_data_count']:
                    single_request['key_data_count'][key] = 0

                # 如果该键有值，则统计+1
                if value:
                    single_request['key_data_count'][key] += 1
                    # 如果该键为new_url_request， 则该请求产生的新请求统计+1
                    if key == 'new_url_request':
                        single_request['new_request_count'] += 1

class LogDownloaderMiddleware(object):
    """日志模块下载中间件，监控单个请求"""
    def process_request(self, request, spider):
        # 生成请求id

        # 无法获取请求对象中的formdata参数，暂时使用时间来生成
        url = request.url + str(datetime.datetime.now())
        request_id = hashlib.md5(url.encode('utf-8')).hexdigest()
        log_mod.request_dict[request_id] = {
            # 该条请求的开始时间
            'start_request_time': datetime.datetime.now(),
            # 该条请求的url
            'url': request.url,
            # 该条请求的网页的网页类型
            'url_type': request.meta['url_type']
        }
        request.meta['request_id'] = request_id

    def process_response(self, request, response, spider):
        # 根据请求id找到对应的请求统计字典
        log_request = log_mod.request_dict[request.meta['request_id']]
        # 该条请求的结束时间
        log_request['end_request_time'] = datetime.datetime.now()
        # 该条请求返回的状态码
        log_request['status'] = response.status


        return response


class LogModPipeline(object):
    """日志模块管道，监控整个爬虫的运行"""

    def open_spider(self, spider):
        # 爬虫开始时间
        log_mod.spider_start_time = datetime.datetime.now(),

    def process_item(self, item, spider):
        return item

    def close_spider(self, spider):
        # 爬虫结束时间
        log_mod.spider_end_time = datetime.datetime.now(),
        # 调用对应的方法做数据的总结统计以及保存数据
        log_mod.save_log_info()


log_mod = LogMod()