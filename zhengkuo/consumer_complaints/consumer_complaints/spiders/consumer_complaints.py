# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.4.13
版本: 1.0 目前已经完成列表页的解析工作
问题: 目前尚未实现增量更新,以及进一步抓取具体的投诉详情页的相关工作
      并且用户的个人信息页,还有用户在网站上的注册时间等,但是依然尚未采集

实现站点 consumer_complaints 的爬虫逻辑,生成的信息如下:
    user: user_id, user_name, website_id, website_type, region, crawl_time
    content: content_id, user_id, refer_id, url, website_id, website_type,
             title, main_body, company, date, crawl_time
'''
import re
from scrapy.http import Request

from vivo_public_modules.spiders.vivo_base_spider import VivoBaseSpider


class ConsumerComplaints(VivoBaseSpider):
    '''
    爬虫类
    爬虫类名与 website_id 一致,不过遵循类名的首字母大写命名格式
    '''
    # 无特殊情况,选择统一将 name = website_id
    name = 'consumer_complaints'

    def __init__(self, name=None, **kwargs):
        '''
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        '''
        super(ConsumerComplaints, self).__init__(name, **kwargs)
        self.website_id = 'consumer_complaints'
        self.website_type = 'complaint'

    def start_requests(self):
        '''
        爬虫任务的起点,由于网站数据量有限,这里 url 为不变的
        :warning: 增量更新
        '''
        base_url = 'https://www.consumercomplaints.in/bysubcategory/mobile-handsets/page/%d'
        for page_index in range(1, 2):
            request_url = base_url % page_index
            request = Request(request_url)
            request.meta['page_type'] = 'complaint_list'
            yield request

    def format_data(self, page_data, page_type):
        '''
        针对采集到的信息进行格式化
        :param page_data: 解析得到的原始数据
        :return : 经过清洗解析的 page_data
        '''
        page_data = page_data['item']
        page_data = {key: page_data[key] for key in page_data}
        # company, title 在相同的网页元素当中
        # 需要将 company, title 分离开
        company_title = page_data.pop('company_title')
        if len(company_title) == 2:
            page_data['title'] = re.sub('—', ' ', company_title[1]).strip()
            page_data['company'] = company_title[0]

        # user_name, date 在相同的网页元素当中
        # 需要将两者分离开, 并进行适当的格式化
        user_name_date = page_data.pop('user_name')
        if len(user_name_date) == 4:
            page_data['user_name'] = user_name_date[2]

        # region, complaint_type 在相同的网页元素当中
        # 需要将两者分离开, 并进行适当的格式化
        region = page_data.pop('region')
        region = [part.strip() for part in region]
        region = [part for part in region if part]
        region = [part for part in region if part not in ['\xa0', 'Read comments']]
        if len(region) == 2:
            region = region[0].split(' ')
            region.reverse()
            region = ''.join(region)
            page_data['region'] = region

        # 填写数据库必备字段
        return [self.padding_item(page_data, -1)]
