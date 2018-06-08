# -*- coding: utf-8 -*-
"""
gizmochina 爬虫
"""

import re
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy import Item
from scrapy import Field
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class GiZmoChinaSpider(ItemPaddingSpider):
    """
    获取GiZmoChina网站信息
    Search:要搜索的关键词
    """
    name = 'GizmoChina'
    allowed_domains = ['gizmochina.com']

    start_url = 'https://forum.gizmochina.com/search?Search={keyword}'
    search = ['vivo', 'oppo', 'lenovo', 'samsung','xiaomi']

    def __init__(self, name=None, **kwargs):
        '''
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        '''
        super().__init__(name, **kwargs)
        self.website_id = 'gizmochina'
        self.website_type = 'complaint'

        self.url = 'https://forum.gizmochina.com'
        self.list_xpath = '//ul[@class="MessageList SearchResults"]/li'
        self.content_xpath = dict()
        self.content_xpath['user_name'] = './/span[@class="Author"]/a/text()'
        self.content_xpath['title'] = './/span[@class="MItem DiscussionName"]/a/text()'
        self.content_xpath['date'] = './/span[@class="MItem DateCreated"]/time/text()'
        self.content_xpath['main_body'] = './/div[@class="Message"]'
        self.content_xpath['brand'] = ''
        self.content_xpath['content_url'] = ''

        self.user_list_xpath = '//div[@class="UserPhoto  Box"]'
        self.user_xpath = dict()
        self.user_xpath['user_name'] = './/div[@class="WhoIs"]/a/text()'
        self.user_xpath['registration_date'] = './/dd[@class="Joined"]/time/text()'
        self.user_xpath['post_view_num'] = './/dd[@class="Visits"]/text()'
        self.user_xpath['last_login_time'] = './/dd[@class="LastActive"]/time/text()'
        self.user_xpath['user_level'] = './/dd[@class="Roles"]/text()'
        self.user_xpath['user_url'] = ''

        self.text_list_xpath = './/ul[@class="MessageList"]/li'
        self.text_xpath = dict()
        self.text_xpath['user_name'] = './/span[@class="AuthorName"]/a/text()'
        self.text_xpath['title'] = './/span[@class="MItem DiscussionName"]/a/text()'
        self.text_xpath['date'] = './/span[@class="MItem DateCreated"]/time/text()'
        self.text_xpath['main_body'] = './/div[@class="Message"]/a/text()'
        self.text_xpath['content_url'] = ''

    def start_requests(self):
        """
        访问初始网址
        """
        for search in self.search:
            yield Request(self.start_url.format(keyword=search), meta={'keyword': search}, callback=self.parse)

    def parse(self, response):
        """
        根据返回的 response 进行数据解析
        :param response: scrapy 框架返回的响应
        """
        keyword = response.meta['keyword']
        for complaint in response.xpath(self.list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=complaint)
            for field in self.content_xpath:
                item.fields[field] = Field()
                if 'content_url' in field:
                    item_loader.add_value(field, response.url)
                elif 'brand' in field:
                    item_loader.add_value(field, keyword)
                else:
                    item_loader.add_xpath(field, self.content_xpath[field])

            # 用户链接
            user_id = complaint.xpath('.//span[@class="Author"]/a/@href').extract()
            for uid in user_id:
                yield Request(self.url + uid, self.parse_user, meta=dict(item_loader.load_item()))

        # 下一页
        next_page = response.xpath('//div[@id="PagerBefore"]/a[last()]/@href').extract()
        if next_page:
            yield Request(self.url + next_page[0], meta={'keyword': keyword}, callback=self.parse)

    def parse_user(self, response):
        """
        根据返回的 response 进行数据解析
        :param response: scrapy 框架返回的响应
        """
        result = {
            'user_name': response.meta['user_name'],
            'title': response.meta['title'],
            'date': response.meta['date'],
            'main_body': response.meta['main_body'],
            'content_url': response.meta['content_url'],
            'brand': response.meta['brand']
        }

        for content in response.xpath(self.user_list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=content)
            for field in self.user_xpath:
                item.fields[field] = Field()
                if 'user_url' in field:
                    item_loader.add_value(field, response.url)
                else:
                    item_loader.add_xpath(field, self.user_xpath[field])

            result.update(item_loader.load_item())
            item = self.format_item(result)
            yield item

        # 用户评论
        user_comment = response.xpath('.//ul/li[@class="Comments"]/a/@href').extract()
        if user_comment:
            yield Request(self.url + user_comment[0], self.parse_comment)

    def parse_comment(self, response):
        """
        根据返回的 response 进行数据解析
        :param response: scrapy 框架返回的响应
        """
        for complaint in response.xpath(self.text_list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=complaint)
            for field in self.text_xpath:
                item.fields[field] = Field()
                if 'content_url' in field:
                    item_loader.add_value(field, response.url)
                else:
                    item_loader.add_xpath(field, self.text_xpath[field])

            item = self.format_item(item_loader.load_item())

            yield item
        # 下一页
        next_page = response.xpath('//div[@id="PagerMore"]/a[last()]/@href').extract()
        if next_page:
            yield Request(self.url + next_page[0], self.parse_comment, dont_filter=True)

    def format_item(self, item):
        """
         针对采集到的信息进行格式化
        :param item: 解析得到的原始数据
        :return : 经过清洗解析的 item
        """
        item = {key: item[key][0] for key in item}
        if 'main_body' in item:
            for trash_str in ["\n", "\r", "\xa0", r'<.*?>']:
                item['main_body'] = re.sub(trash_str, '', item['main_body']).strip()

        return self.padding_item(item, -1)
        # print(item)
