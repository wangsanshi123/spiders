# -*- coding: utf-8 -*-
"""
91mobiles网站
"""
import re
import json
from scrapy.http import Request
from scrapy import Item
from scrapy import Field
from scrapy.loader import ItemLoader
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class SjSpider(ItemPaddingSpider):
    """
    获取91mobiles站点所有手机相关参数
    start_url：手机参数以及用户评论
    vivo：2199 (品牌对应参数值,可通过传入参值进行抓取)
    Lenovo：156
    Oppo:2050
    Samsung:157
    Xiaomi:1936
    """
    name = 'mobiles'
    allowed_domains = ['91mobiles.com']
    start_url = 'https://www.91mobiles.com/template/category_finder/finder_ajax.php?' \
                'header_source=LP_widget&hidFrmSubFlag=1&page=1&category=mobile&gaCa' \
                'tegory=PhoneFinder-filter&requestType=2&showPagination=1&listType=l' \
                'ist&listType_v3=list&listType_v1=list&listType_v2=list&listType_v4' \
                '=list&listType_v5=list&listType_v6=list&page_type=finder&selMobSort' \
                '=views&hdnCategory=mobile&buygaCat=finder-mob&sCatName=mobile&price_ran' \
                'ge_apply=0&brand%5B%5D={brand}&tr_fl%5B%5D=mob_market_status_filter.' \
                'marketstatus_filter%3Aava_stores'

    brand = ['156', '157', '2199', '2050', '1936']
    url = 'https://www.91mobiles.com'

    forum_url = 'https://hub.91mobiles.com/?s={search}'
    serach = ['vivo', 'oppo', 'samsung', 'lenovo', 'xiaomi']

    def __init__(self, name=None, **kwargs):
        '''
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        '''
        super().__init__(name, **kwargs)

        self.website_id = '91mobiles'
        self.website_type = 'e-commerce'

        self.forum_xpath = dict()
        self.forum_xpath['title'] = './/header[@class="td-post-title"]/h1/text()'
        self.forum_xpath['user_name'] = './/div[@class="td-post-author-name"]/a/text()'
        self.forum_xpath['date'] = './/span[@class="td-post-date"]/time/text()'
        self.forum_xpath['main_body_score'] = './/div[@class="td-post-content"]/div/div/div/span[2]/text()'
        # self.forum_xpath['advantage'] = './/div[@class="td-post-content"]/div/div/ul[1]/li/text()'
        # self.forum_xpath['disadvantage'] = './/div[@class="td-post-content"]/div/div/ul[2]/li/text()'
        self.forum_xpath['main_body'] = ''
        self.forum_xpath['content_url'] = ''

        self.model_xpath = dict()
        self.model_xpath['model_name'] = './/h1[@class="h1_pro_head"]/span/text()'
        self.model_xpath['model_score'] = './/div[@class="top_box"][2]/span[@class="ratpt"]/text()'
        self.model_xpath['score_num'] = './/div[@class="top_box"][2]/span[@class="revs_cnt topScroll"]/text()'
        self.model_xpath['price'] = './/div[@class="price_div"]/span[@class="big_prc"][2]/text()'
        self.model_xpath['cpu'] = './/table[@class="specsTable"]/tr/td[1]/ul/li/label[1]/text()'
        self.model_xpath['ram'] = './/table[@class="specsTable"]/tr/td[1]/ul/li/label[3]/text()'
        self.model_xpath['screen_size'] = './/table[@class="specsTable"]/tr/td[2]/ul/li/label[1]/text()'
        self.model_xpath['display_resolution'] = './/table[@class="specsTable"]/tr/td[2]/ul/li/label[2]/text()'
        self.model_xpath['rear_camera'] = './/table[@class="specsTable"]/tr/td[3]/ul/li/label[1]/text()'
        self.model_xpath['front_camera'] = './/table[@class="specsTable"]/tr/td[3]/ul/li/label[3]/text()'
        self.model_xpath['battery'] = './/table[@class="specsTable"]/tr/td[4]/ul/li/label[1]/text()'
        self.model_xpath['rom'] = './/div[@class="nw_featur_box"]/ul/li/text()'
        self.model_xpath['model_url'] = ''
        self.user_url = './/div[@class="head_titleBox brdr_botNone"]/span/@data-href-url'
        self.user_review_url = 'https://www.91mobiles.com/loadmore_user_review.php?brand={brand}&model={model}&page=1'

        self.content_list = re.compile(r'<div class="review_section">(.*?)</div>\s+</div>\s+</div>', re.S | re.M)
        self.user_level = re.compile(r'<div class="rating-stars_rw" style="float:left;" title="(.*?)">')
        self.date = re.compile(r'<span class="user_info">(.*?),</span>')
        self.user_name = re.compile(
            r'<span class="user_info" style="color: #ADA6A6;text-transform: capitalize;">By\s+(.*?),</span>')
        self.title = re.compile(r'<div class="rw-heading">(.*?)</div>')
        self.main_body = re.compile(r'<div class="rw-area">\s+<p>(.*?)</p>', re.S | re.M)
        self.thumb_up_num = re.compile(r'<span class="fltL" id=".*?">(\d+) users found this review')

    def start_requests(self):
        """
        访问初始网址
        """
        for brand in self.brand:
            yield Request(self.start_url.format(brand=brand), self.parse)

        for search in self.serach:
            yield Request(self.forum_url.format(search=search), self.parse_url)

    def parse_url(self, response):
        """
        解析网址
        """
        parse_url = response.xpath('.//div[@class="td-block-span6"]/div/h3/a/@href').extract()
        for url in parse_url:
            yield Request(url, self.parse_forum)

        # 下一页
        next_page = response.xpath('.//div[@class="page-nav td-pb-padding-side"]/a[last()]/@href').extract()
        yield Request(''.join(next_page), self.parse_url)

    def parse_forum(self, response):
        """
        解析评论内容
        """
        item = Item()
        itemloader = ItemLoader(item=item, selector=response)
        for field in self.forum_xpath:
            item.fields[field] = Field()
            if 'main_body' in field:
                content = re.compile(
                    r'<html><body><.*?>(.*?)</body></html>', re.S | re.M)
                content = content.findall(response.text)
                content = re.sub(r'<script>.*?</script>', '', ''.join(content))
                content = re.sub(r'[\r\n]', '', content)
                content = re.sub(r'<div .*?>.*?</div>', '', content)
                content = re.sub(r'<style .*?>.*?</style>', '', content, re.S | re.M)
                content = re.sub(r'&.*?;', '', content)
                content = re.sub(r'<.*?>', '', content, re.M | re.I)
                content = re.sub('  ', '', content)
                itemloader.add_value(field, content)
            elif 'content_url' in field:
                itemloader.add_value(field, response.url)
            else:
                itemloader.add_xpath(field, self.forum_xpath[field])

        item = self.format_item(itemloader.load_item())

        yield item

    def parse(self, response):
        """
        解析响应内容，提取相关商品链接
        """
        data = json.loads(response.text)["response"]
        url = re.compile(r'<p><a.*?href="(.*?)" title=".*?">.*?</a></p>', re.I | re.M)
        urls = url.findall(data)
        for uid in urls:
            yield Request(self.url + uid, self.parse_shop)

        # 获取下一页的链接
        totalpages = json.loads(response.text)["totalPages"]
        num = int(response.url.split('page=')[1].split('&category=')[0])
        if num < totalpages + 1:
            num += 1
            head_url = response.url.split('page=')[0]
            tail_url = response.url.split('page=')[1].split('&category=')[1]

            yield Request(head_url + 'page=' + str(num) + '&category=' + tail_url, self.parse)

    def parse_shop(self, response):
        """
        解析提取model数据
        :param response:
        """
        item = Item()
        item_loader = ItemLoader(item=item, selector=response)
        for field in self.model_xpath:
            item.fields[field] = Field()
            if 'model_url' in field:
                item_loader.add_value(field, response.url)
            else:
                item_loader.add_xpath(field, self.model_xpath[field])

        item = self.format_item(item_loader.load_item())

        yield item

        # 拼接用户评论链接
        user_url = response.xpath(self.user_url).extract()
        for uid in user_url:
            brand = uid.split('-')[0]
            model = uid.split('-')[1]
            yield Request(self.user_review_url.format(brand=brand, model=model), self.parse_comment)

    def parse_comment(self, response):
        """
        提取用户评论信息
        """
        user_review = json.loads(response.text)["response"]

        for forum in self.content_list.findall(user_review):
            user_level = self.user_level.findall(forum)
            date = self.date.findall(forum)
            user_name = self.user_name.findall(forum)
            title = self.title.findall(forum)
            main_body = self.main_body.findall(forum)
            thumb_up_num = self.thumb_up_num.findall(forum)
            if main_body:
                content_data = {
                    'user_level': user_level,
                    'date': date,
                    'user_name': user_name,
                    'title': title,
                    'main_body': main_body,
                    'thumb_up_num': thumb_up_num,
                    'content_url': [response.url],
                }
                item = self.format_item(content_data)
                yield item

        # 总页数
        totalpages = json.loads(response.text)["totalPages"]

        page = int(response.url.split('page=')[1])
        if page < totalpages + 1:
            page += 1
            url = response.url.split('page=')[0]
            yield Request(url + 'page=' + str(page), self.parse_comment)

    def format_item(self, item):
        """
        针对采集到的信息进行格式化
        """
        if 'advantage' in item:
            item['advantage'] = [','.join(item['advantage'])]
        elif 'disadvantage' in item:
            item['disadvantage'] = [','.join(item['disadvantage'])]

        if 'rom' in item:
            for rom in item['rom']:
                if 'GB' in rom:
                    item['rom'] = [rom]

        item = {key: item[key][0] for key in item}

        if 'main_body' in item:
            content = re.sub('[\r,\n]', '', item['main_body'])
            item["main_body"] = re.sub(r'<.*?>', '', content).strip()

        return self.padding_item(item, -1)
