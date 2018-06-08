"""Teleanalysis爬虫"""
import re
from scrapy.http import Request
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class Teleanalysis(ItemPaddingSpider):
    """Teleanalysis爬虫类"""
    name = 'teleanalysis'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "teleanalysis"
        self.website_type = "news"

    def start_requests(self):
        url = "https://www.teleanalysis.com/category/devices/smartphones-devices"
        yield Request(url)

    def parse(self, response):
        """解析新闻列表页"""
        article_list_xpath = '//article'
        article_url_xpath = './/h3/a/@href'
        next_page_xpath = '//a[@class="next page-numbers"]/@href'
        for article in response.xpath(article_list_xpath):

            article_url = article.xpath(article_url_xpath).extract_first()
            yield Request(article_url, callback=self.parse_article)

        next_page_url = response.xpath(next_page_xpath).extract_first()
        if next_page_url:
            yield Request(next_page_url)

    def parse_article(self, response):
        """解析新闻详情页"""
        title_xpath = '//h1/text()'
        author_xpath = '//a[@class="vcard author"]/text()'
        time_xpath = '//time/@datetime'
        views_xpath = '//span[@class="meta-info-el meta-info-view"]/a/span/text()'
        article = '//div[@class="entry"]/p'

        item_dict = dict()
        item_dict['title'] = response.xpath(title_xpath).extract_first()
        item_dict['user_name'] = response.xpath(author_xpath).extract_first()
        item_dict['time'] = response.xpath(time_xpath).extract_first()
        item_dict['view_num'] = response.xpath(views_xpath).extract_first()
        article = response.xpath(article)
        item_dict['main_body'] = ''.join([p.xpath('string()').extract_first() for p in article])
        item_dict['content_url'] = response.url

        self.format_item(item_dict)

    def format_item(self, item):
        """格式化数据"""
        item['user_name'] = re.sub(r'[\n\t]', '', item['user_name'])
        item['view_num'] = re.sub(r' views', '', item['view_num'])

        yield self.padding_item(item, -1)
