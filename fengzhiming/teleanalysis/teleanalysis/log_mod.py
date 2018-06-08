"""基于scrapy扩展的方式写的日志模块"""
import hashlib
from datetime import datetime
from scrapy import signals


class LogMod(object):
    """日志模块类"""
    def __init__(self):
        self.spider_info = dict()
        self.request_info_dict = dict()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        exe = cls()
        crawler.signals.connect(exe.spider_opened, signals.spider_opened)
        crawler.signals.connect(exe.spider_closed, signals.spider_closed)
        crawler.signals.connect(exe.save_spider_info, signals.engine_stopped)
        crawler.signals.connect(exe.count_request, signals.request_received)
        crawler.signals.connect(exe.count_response, signals.response_received)
        crawler.signals.connect(exe.count_item, signals.item_scraped)

        return exe

    def spider_opened(self, spider):
        """爬虫开始时"""
        self.spider_info['spider_start_time'] = datetime.now()

    def spider_closed(self, spider):
        """爬虫关闭时"""
        self.spider_info['spider_close_time'] = datetime.now()

    def count_request(self, request, spider):
        """统计请求信息"""
        request_info = {
            'start_request_time': datetime.now(),
            'url': request.url,
            'method': request.method,
            'item_count': 0,
            'item_key_count': {},
        }
        request_str = request.url + request.body.decode('utf-8')
        request_id = hashlib.md5(request_str.encode('utf-8')).hexdigest()
        self.request_info_dict[request_id] = request_info

    def count_response(self, response, request, spider):
        """统计返回的状态"""
        response_info = {
            'finish_request_time': datetime.now(),
            'status': response.status,
        }
        request_str = request.url + request.body.decode('utf-8')
        request_id = hashlib.md5(request_str.encode('utf-8')).hexdigest()
        self.request_info_dict[request_id].update(response_info)

    def count_item(self, item, response, spider):
        """统计item"""
        request_str = response.request.url + response.request.body.decode('utf-8')
        request_id = hashlib.md5(request_str.encode('utf-8')).hexdigest()
        self.request_info_dict[request_id]['item_count'] += 1
        item = dict(item)
        for key, value in item.items():
            if key not in self.request_info_dict[request_id]['item_key_count']:
                self.request_info_dict[request_id]['item_key_count'][key] = 0
            if value:
                self.request_info_dict[request_id]['item_key_count'][key] += 1

    def save_spider_info(self):
        """保存爬虫信息"""
        with open('spider.log', 'w') as f:

            for key, value in self.spider_info.items():
                f.write(key)
                f.write(':  ')
                f.write(str(value))
                f.write('\n')

            for request in self.request_info_dict.values():
                f.write('**' * 50)
                f.write('\n')
                for key, value in request.items():
                    f.write(key)
                    f.write(':  ')
                    f.write(str(value))
                    f.write('\n')
