# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.05.23
版本: 1.0
完成该网站的爬虫程序
该网站为投诉类网站
需要采集的字段有
投诉信息 title user_name date comment_num main_body
评论信息 user_name time main_body
'''
from scrapy import Request
from vivo_public_modules.spiders.vivo_base_spider import VivoBaseSpider


class IndiaConsumerForumSpider(VivoBaseSpider):
    '''
    india_consumer_forum 的爬虫类
    尝试使用VivoBaseSpider减少代码的开发量
    '''
    name = 'india_consumer_forum'
    allowed_domains = ['indiaconsumerforum.org']

    def __init__(self, name=None, **kwargs):
        '''
        只是完成基类的初始化,以及基本属性的配置
        '''
        super().__init__(name, **kwargs)
        self.website_id = 'india_consumer_forum'
        self.website_type = 'complaint'

    def start_requests(self):
        '''
        生成初始request
        '''
        seed_url = 'http://www.indiaconsumerforum.org/category/products/mobile-phones/page/{page_index}/'
        for page_index in range(5, 6):
            url = seed_url.format(page_index=page_index)
            request = Request(url)
            # 需要设置页面类型并与config.xml一直
            request.meta['page_type'] = 'complaint_list'
            yield request

    def format_data(self, page_data, page_type):
        '''
        数据的格式化方法,VivoBaseSpider
        '''
        complaint = page_data.get('item', None)
        complaint = self.padding_item(complaint, -1)
        yield complaint
        comment_list = page_data.get('comment')
        for comment in comment_list:
            comment['content_url'] = complaint['content_url']
            comment = self.padding_item(comment, complaint['content_id'])
            yield comment
