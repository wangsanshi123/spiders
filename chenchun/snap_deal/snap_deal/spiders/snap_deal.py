# -*- coding: utf-8 -*-
"""
实现站点 sanpdeal 的爬虫逻辑
"""
import re
from scrapy.http import Request
from scrapy.item import Item
from scrapy.item import Field
from scrapy.loader import ItemLoader
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class SnapDealSpider(ItemPaddingSpider):
    """
    SnapDeal网站爬取
    """
    name = 'SnapDeal'
    allowed_domains = ['www.snapdeal.com']

    start_urls = 'https://www.snapdeal.com/acors/json/product/get/search/175/%s/20?q=Form_s:Sm' \
                'artphones|Brand:Samsung^Lenovo^Vivo^Oppo^Redmi^Xiaomi Mi|&sort=plrty&&searc' \
                'hState=k3=true|k4=null|k5=0|k6=0&webpageName=categoryPage&isMC=false&clickS' \
                'rc=unknown&showAds=true&page=cp'

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param name:
        :param kwargs:
        """
        super().__init__(name, **kwargs)
        self.website_id = 'snapdeal'
        self.website_type = 'commerce'

        self.model_xpath = dict()
        self.model_xpath['model_name'] = './/div[@class="row"]/div[@class="col-xs-22"]/h1/text()'
        self.model_xpath['price'] = './/div[@class="disp-table"]/div/span[1]/span/text()|.//div[@class="col-xs-12 pdp-e-i-PAY-r reset-padding"]/span/span/text()'
        self.model_xpath['colour'] = './/div[@class="pull-left"]/div/div[2]/text()'
        self.model_xpath['model_score'] = './/div[@class="pdp-e-i-ratings"]/div/span[@class="avrg-rating"]/text()'
        self.model_xpath['score_num'] = './/div[@class="pdp-e-i-ratings"]/div/span[@class="total-rating showRatingTooltip"]/text()'
        self.model_xpath['score_grade'] = './/div[@class="pdp-e-i-ratings"]/div/span[@class="numbr-review"]/a/text()'
        self.model_xpath['brand'] = './/table[@cellspacing="2"]/tr/td[text()="Brand"]/following-sibling::td/text()'
        self.model_xpath['screen_size'] = './/table[@cellspacing="2"]/tr/td[text()="Screen Size (in cm)"]/following-sibling::td/text()'
        self.model_xpath['display_resolution'] = './/table[@cellspacing="2"]/tr/td[text()="Display Resolution"]/following-sibling::td/text()'
        self.model_xpath['operating_system'] = './/table[@cellspacing="2"]/tr/td[text()="Operating System"]/following-sibling::td/text()'
        self.model_xpath['rear_camera'] = './/table[@cellspacing="2"]/tr/td[text()="Rear Camera"]/following-sibling::td/text()'
        self.model_xpath['front_camera'] = './/table[@cellspacing="2"]/tr/td[text()="Front Camera"]/following-sibling::td/text()'
        self.model_xpath['cpu'] = './/table[@cellspacing="2"]/tr/td[text()="Processor Cores"]/following-sibling::td/text()'
        self.model_xpath['ram'] = './/table[@cellspacing="2"]/tr/td[text()="RAM"]/following-sibling::td/text()'
        self.model_xpath['rom'] = './/table[@cellspacing="2"]/tr/td[text()="Internal Memory"]/following-sibling::td/text()'
        self.model_xpath['battery'] = './/table[@cellspacing="2"]/tr/td[text()="Battery Capacity"]/following-sibling::td/text()'
        self.model_xpath['model_weight'] = './/table[@cellspacing="2"]/tr/td[text()="Weight"]/following-sibling::td/text()'
        self.model_xpath['model_url'] = ''

        self.comment_list_xpath = '//div[@class="commentlist first jsUserAction"]'
        self.comment_next_page = './/div[@class="pagination"]/ul/li[@class="last"]/a/@href'
        self.comment_xpath = dict()
        self.comment_xpath['main_body_score'] = './/div[@class="text"]/div/div[1]/i[@class="sd-icon sd-icon-star active"]'
        self.comment_xpath['title'] = './/div[@class="head"]/text()'
        self.comment_xpath['user_name'] = './/div[@class="hidden _reviewUserName"]/text()'
        self.comment_xpath['date'] = './/div[@class="_reviewUserName"]/text()'
        self.comment_xpath['main_body'] = './/p/text()'
        self.comment_xpath['thumb_up_num'] = './/div/a/span/text()'
        self.comment_xpath['content_url'] = ''

    def start_requests(self):
        """
        访问初始网址进行爬取
        """
        for num in range(0, 141, 20):
            yield Request(self.start_urls % num, self.shop_url_parse)

    def shop_url_parse(self, response):
        """
        获取每个页面的商品链接
        :param response:响应的内容，解析出商品的url
        """
        shop_urls = response.xpath('.//div[@class="product-desc-rating "]/a/@href').extract()
        for url in shop_urls:
            # 访问商品详情板块
            yield Request(url, self.parse)
            # 拼接评论链接
            yield Request(url + '/reviews?page=1', self.review_parse)

    def parse(self, response):
        """
        根据返回的 response 进行数据解析
        :param response: scrapy 框架返回的响应
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

    def review_parse(self, response):
        """
        解析商品下方用户评论信息
        """
        for comment in response.xpath(self.comment_list_xpath):
            item = Item()
            item_loader = ItemLoader(item=item, selector=comment)
            for field in self.comment_xpath:
                item.fields[field] = Field()
                if 'content_url' in field:
                    item_loader.add_value(field, response.url)
                else:
                    item_loader.add_xpath(field, self.comment_xpath[field])

            item = self.format_item(item_loader.load_item())

            yield item

        # 下一页
        next_page = response.xpath(self.comment_next_page).extract_first()
        if next_page:
            yield Request(next_page, self.review_parse)

    def format_item(self, item):
        """
        针对采集到的信息进行格式化
        :param item: 解析得到的原始数据
        :return : 经过清洗解析的 item
        """
        if 'main_body_score' in item:
            item['main_body_score'] = [len(item['main_body_score'])]
            item['date'] = [''.join(item['date']).split('on')[1]]
            item['main_body'] = [re.sub('\n', '', ''.join(item['main_body']))]

        item = {key: item[key][0] for key in item}

        if 'model_name' in item:
            item['model_name'] = re.sub('[\n,\t]', '', item['model_name']).strip()

        return self.padding_item(item, -1)
