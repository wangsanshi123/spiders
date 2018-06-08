"""bgr概要信息页"""
import re
from time import localtime
from time import strftime
from time import strptime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose

from vivo_public_modules.spiders.mix_spider import MixSpider


class BgrSpider(MixSpider):
    """bgr概要信息页    由于首页的格式不一样，且内容 不是很多，所以不专门爬取"""
    name = 'bgr'
    page = 2
    base_url = "http://www.bgr.in/category/news/page/{}/"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "bgr"
        self.website_type = "news"

    def start_requests(self):
        yield scrapy.Request(url=self.base_url.format(self.page))

    def parse(self, response):
        self.init_update_time_config()  # 获取增量更新的时间配置
        div_list = response.xpath(".//div[contains(@class,'widget-list news_sec')]")
        for div_tag in div_list:
            item = {}
            item_loader = BgrItemLoader(item=item, selector=div_tag)
            item_loader.add_xpath("title", ".//h3[@class='media-heading']/a/@title")
            item_loader.add_xpath("content_url", ".//h3[@class='media-heading']/a/@href")
            item_loader.add_xpath("user_name", ".//span[@class='name']/a/@title")
            item_loader.nested_xpath(".//div[@class='time-date']").add_xpath("time", "string()")

            item = item_loader.load_item()
            # ==================增量更新=============================
            date_to_update = super().get_date_to_update(response,
                                                        strftime("%Y-%m-%d", strptime(item["time"], "%Y-%m-%d %H:%M")))
            if date_to_update == -1:
                return
            # ==================增量更新=============================

            yield scrapy.Request(url=item["content_url"],
                                 meta={
                                     "title": item["title"],
                                     "user_name": item["user_name"],
                                     "time": item["time"],
                                 },
                                 callback=self.parse_content)
        # nextpage
        next_page = response.xpath(".//span[@class='btn btn-default']")
        if next_page:
            self.page += 1
            yield scrapy.Request(url=self.base_url.format(self.page),
                                 meta={
                                     "first_in": False,
                                     "date_to_update": date_to_update
                                 })

    def parse_content(self, response):
        """解析新闻内容页"""
        user_name = response.meta["user_name"]
        time = response.meta["time"]
        url = response.url
        title = response.xpath(".//h1[@class='title_name']/text()").extract_first()
        main_body = response.xpath(".//div[@class='article-content']"). \
            xpath("string()").extract_first()
        ##################去除script中的内容################################### #####
        for script in response.xpath(".//div[@class='article-main_body']/script"):
            main_body_extra = script.xpath("string()").extract_first()
            main_body = main_body.replace(main_body_extra, "")
        ############################################################

        # 去除文章末尾的广告部分
        main_body = main_body.split("Published Date") if main_body else ""
        main_body = main_body[0].replace("\n", "").strip() if main_body else ""
        # 去除换行，空格
        main_body = re.sub("[\n\r]", "", main_body) if main_body else ""
        item = {"content_url": url, "title": title, "main_body": main_body, "user_name": user_name, "time": time}

        item = self.padding_item(item, refer_id=-1)
        yield item

    @staticmethod
    def get_current_time():
        return strftime("%Y-%m-%d %H:%M:%S", localtime())


class TakeFirst(object):
    """取values中的第一个元素value，然后去掉value中间过多的空格和换行符，然后去掉首尾的空格"""

    def __call__(self, values):
        for value in values:
            if value is not None and value != '':
                return re.sub(r'\s+', ' ', value).strip()


class BgrItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

    def format_time(time_str):
        time_str = re.sub(r"\s", "", time_str)
        time = strftime("%Y-%m-%d %H:%M", strptime(time_str, "%I:%M%p%b%d,%Y")) \
            if time_str else ""
        return time

    time_out = Compose(TakeFirst(), format_time)
