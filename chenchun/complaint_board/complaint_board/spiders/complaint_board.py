# -*- coding: utf-8 -*-
"""
complaintboard网站爬虫
"""
import re
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy import Item
from scrapy import Field
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class ComplaintBoardSpider(ItemPaddingSpider):
    """
    抓取complaintBoard网站评论信息
    search: 搜索关键字
    """
    name = 'ComplaintBoard'
    allowed_domains = ['www.complaintboard.in']
    start_url = 'https://www.complaintboard.in/?search={search}&page=1'
    search = ['vivo', 'oppo', 'samsung', 'lenovo', 'xiaomi']

    def __init__(self, name=None, **kwargs):
        '''
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        '''
        super().__init__(name, **kwargs)
        self.website_id = 'complaintboard'
        self.website_type = 'complaint'

        self.urls = 'https://www.complaintboard.in'
        self.first_page_url = 'https://www.complaintboard.in/complaints-reviews/{tid}/page/1'

        self.list_xpath = '//table[@id="body"]/tr/td/table/tr[5]/td/div'
        self.content_xpath = dict()
        self.content_xpath['user_name'] = './/tr/td[@class="small"]/a/text()'
        self.content_xpath['date'] = './/table[@width="100%"]/tr/td[@class="small"][last()]/text()'
        self.content_xpath['title'] = './/tr/td[@class="complaint"]/div/h4/text()'
        self.content_xpath['main_body'] = './/tr/td[@class="complaint"]/div/div/text()'
        self.content_xpath['content_url'] = ''
        self.content_xpath['brand'] = ''

        self.user_list_xpath = './/table[@id="body"]/tr/td/table[@class="profile"][1]'
        self.user_xpath = dict()
        self.user_xpath['user_name'] = './/tr/td/span[@class="displname"]/text()'
        self.user_xpath['registration_date'] = './/tr/td/span[@class="grey-normal"]/text()'
        self.user_xpath['region'] = './/tr/td/span[@class="grey-normal"]/div[last()]/text()'
        self.user_xpath['user_url'] = ''

    def start_requests(self):
        """
        访问初始网址
        """
        for search in self.search:
            yield Request(self.start_url.format(search=search), meta={'keyword': search},
                          callback=self.start_parse)

    def start_parse(self, response):
        """
        获取每一页所有标题的url链接，并
        使标题的url链接访问都从第一页开始
        """
        keyword = response.meta['keyword']
        title_url = re.compile(r'<h4><a href="(.*?)">')
        urls = title_url.findall(response.text)
        for url in urls:
            url = url.split('/')[2].split('#')[0].split('.html')[0]

            yield Request(self.first_page_url.format(tid=url), meta={'keyword': keyword},
                          callback=self.parse)

        # 列表下一页
        list_down_page = response.xpath('//div[@class="pagelinks"]/a[last()]/@href').extract()
        for down_page in list_down_page:
            yield Request(self.urls + down_page, self.start_parse, meta={'keyword': keyword})

    def parse(self, response):
        """
        解析网页获取评论
        :param response:响应内容
        """
        search = response.meta['keyword']
        # 评论页
        for complaint in response.xpath(self.list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=complaint)
            for field in self.content_xpath:
                item.fields[field] = Field()
                if 'content_url' in field:
                    item_loader.add_value(field, response.url)
                elif 'brand' in field:
                    item_loader.add_value(field, search)
                else:
                    item_loader.add_xpath(field, self.content_xpath[field])
            # 拼接user_url链接
            uid = complaint.xpath('.//tr/td[@class="small"]/a/@href').extract()
            yield Request(self.urls + uid[0], self.parse_user, meta=dict(item_loader.load_item()), dont_filter=True)

        # 内容下一页
        next_page = response.xpath('//div[@class="pagelinks"]/a[last()]/@href').extract()
        for page in next_page:
            yield Request(self.urls + page, self.parse, meta={'keyword': search})

    def parse_user(self, response):
        """
        接收内容部分，并对用户界面解析
        """
        result = {}
        for user_info in response.xpath(self.user_list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=user_info)
            for field in self.user_xpath:
                item.fields[field] = Field()
                if 'user_url' in field:
                    item_loader.add_value(field, response.url)
                else:
                    item_loader.add_xpath(field, self.user_xpath[field])
            # 内容页数据及用户数据进行合并
            result.update(response.meta)
            result.update(item_loader.load_item())

            item = self.format_item(result)
            yield item

    def format_item(self, item):
        """
        对采集到的信息进行整理
        """
        item['user_name'] = ''.join(item['user_name'])
        item['content_url'] = ''.join(item['content_url'])
        item['title'] = ''.join(item['title'])
        item['registration_date'] = item['registration_date'][0]
        item['user_url'] = ''.join(item['user_url'])
        item['date'] = re.sub(r'[\r,\t,\n]', '', ''.join(item['date'])).strip()
        content = re.sub(r'[\r,\n]', '', ''.join(item['main_body']))
        content = re.sub(r'  ', '', content).strip()
        item['main_body'] = re.sub(r'<.*?>', '', content, re.I | re.M)
        item['brand'] = ''.join(item['brand'])
        item['refer_id'] = '-1'
        if 'region' in item:
            item['region'] = ''.join(item['region'])

        # 填写数据库必备字段
        return self.padding_item(item, -1)
