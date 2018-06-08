"""手机概要信息"""
import hashlib
import json
import logging
import re
from datetime import datetime
from time import strftime, strptime

import scrapy
from scrapy.loader import ItemLoader

from vivo_public_modules.spiders.mix_spider import MixSpider

LOGGER = logging.getLogger(__name__)


class GsmarenaInfoSpider(MixSpider):
    """手机概要信息"""
    name = "gsmarena"
    base_url = "http://www.gsmarena.com/"
    quote_url_base = "http://www.gsmarena.com/comment.php3?idType=1&idComment="

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "gsmarena"
        self.website_type = "e-commerce"

    def start_requests(self):
        file = self.get_config_file()
        with open(file, 'r') as f:
            result = json.load(f)
            for item in result:
                url = item["url"]
                del item["url"]
                yield scrapy.Request(url=url, meta=item)

    def parse(self, response):
        """抓取指定型号的概要信息"""
        self.init_update_time_config()
        brand = response.meta["brand"]
        new_append = response.meta["new_append"]
        model_name = response.meta["model_name"]
        item = {}
        item_loader = GsmarenaItemLoader(item=item, selector=response)
        item_loader.add_value("brand", brand)
        item_loader.add_value("model_name", model_name)
        item_loader.add_value("model_url", response.url)

        item_loader.add_xpath("network_mode", ".//*[@id='specs-list']/table[1]/tbody/tr[1]/td[2]/a/text()")
        item_loader.add_xpath("launch_date", ".//*[@id='specs-list']/table[2]/tbody/tr[1]/td[2]/text()")
        item_loader.add_xpath("sell_date", ".//*[@id='specs-list']/table[2]/tbody/tr[2]/td[2]/text()")
        item_loader.add_xpath("dimensions", ".//*[@id='specs-list']/table[3]/tbody/tr[1]/td[2]/text()")
        item_loader.add_xpath("price", ".//*[@id='specs-list']/table[12]/tbody/tr[2]/td[2][@data-spec='price']/text()")
        item_loader.add_xpath("comment_num", ".//*[@id='opinions-total']/b/text()")
        item = item_loader.load_item()
        url = response.xpath(".//a[@class='button']/@href").extract_first()
        yield scrapy.Request(url=self.base_url + url,
                             meta={
                                 "brand": brand,
                                 "model_name": model_name,
                                 "new_append": new_append,
                             },
                             callback=self.parse_comments)
        yield self.padding_item(item, refer_id="")

    def parse_comments(self, response):
        """解析评论页"""
        div_list = response.xpath(".//div[@class='user-thread']")
        brand = response.meta["brand"]
        new_append = response.meta["new_append"]
        model_name = response.meta["model_name"]

        for div_tag in div_list:
            user_name = div_tag.xpath(".//li[@class='uname2']/text()").extract_first()
            if not user_name:
                user_name = div_tag.xpath(".//li[@class='uname']//b/text()").extract_first()
            location = div_tag.xpath(".//span[@title='Encoded location']/text()").extract_first()
            date = div_tag.xpath(".//li[@class='upost']/time/text()").extract_first()
            if "," in date:
                date = str(date.split(",")[1:])
            try:
                date = strftime("%Y-%m-%d", strptime(date, "%d %b %Y"))
            except ValueError as exception:
                LOGGER.error(exception)
                date = self.parse_date(date)

            quote_temp = div_tag.xpath(".//p[@class='uopin']/span")
            quote_partial = quote_temp.xpath("string()").extract_first()
            quote_date = div_tag.xpath(".//*[@class='uinreply']/text()").extract_first()

            content = div_tag.xpath(".//p[@class='uopin']")
            content = content.xpath("string()").extract_first()

            # 如果是对评论的回复，Attention:如果是对评论的回复，则refer_id 指向被回复的内容（content_id）,
            # 如果不是对评论的回复，则refer_id指向model_id

            if quote_temp:  # 对评论的回复
                quote_data_temp = quote_date.split(",") if "," in quote_date else quote_date.split(" ")
                quote_user_name = quote_data_temp[0]
                quote_date = quote_data_temp[1]

                try:
                    content_filter = (quote_user_name + "," + quote_date + quote_partial).strip()
                    content = content.replace(content_filter, "")

                except NameError as exception:
                    LOGGER.error(exception)

                try:
                    quote_date = strftime("%Y-%m-%d", strptime(quote_date.strip(), "%d %b %Y"))
                except ValueError as exception:
                    LOGGER.error(exception)
                    quote_date = self.parse_date(quote_date)

                quote_url = div_tag.xpath(".//span[@class='uinreply-msg']/a/@href").extract_first()
                if not quote_url:
                    quote = div_tag.xpath(".//span[@class='uinreply-msg uinreply-msg-single']/text()") \
                        .extract_first()

                    content_filter = (quote_partial + quote).strip()
                    content = content.replace(content_filter, "")

                    item = {"content_url": response.url, "brand": brand, "model_name": model_name,
                            "user_name": user_name, "location": location,
                            "date": date, "main_body": content}
                    content_id_f = self.get_md5(self.website_id + quote + quote_user_name + quote_date)
                    yield self.padding_item(item, refer_id=content_id_f)

                else:
                    quote_url = self.quote_url_base + quote_url.replace("#", "")
                    yield scrapy.Request(url=quote_url, callback=self.parse_quote,
                                         meta={"brand": brand, "model_name": model_name, "user_name": user_name,
                                               "location": location,
                                               "date": date, "content": content,
                                               "quote_user_name": quote_user_name,
                                               "quote_date": quote_date,
                                               "url": quote_url, "isQuote": True})


            else:  # 不是对评论的回复

                item = {"content_url": response.url, "brand": brand, "model_name": model_name, "user_name": user_name,
                        "location": location,
                        "date": date, "main_body": content}
                model_id = self.get_md5(self.website_id + model_name)
                yield self.padding_item(item, refer_id=model_id)

            # ==================增量更新=============================
            date_to_update = super().get_date_to_update(response, item["date"])
            if date_to_update == -1:
                return
            # ==================增量更新=============================
        next_page = response.xpath(".//a[@title='Next page']/@href").extract_first()

        if next_page:
            url = self.base_url + next_page

            yield scrapy.Request(url=url,
                                 meta={
                                     "brand": brand,
                                     "model_name": model_name,
                                     "date_to_update": date_to_update,
                                     "new_append": new_append,
                                     "first_in": False,
                                 },
                                 callback=self.parse_comments)

    @staticmethod
    def format_date(date):
        """格式化时间"""
        if not date:
            return ""
        try:
            date = date.strip()
            date = date.split(" ")
            date = date[0] + date[1] + ",01"
            date = strptime(date, "%Y,%B,%d")
            date = strftime("%Y-%m-%d", date)
        except ValueError:
            try:
                date = date + ",01" + ",01"
                date = strptime(date, "%Y,%M,%d")
                date = strftime("%Y-%m-%d", date)
            except ValueError as exception:
                LOGGER.error(exception)
                LOGGER.error(date)
                date = ""
        return date

    def parse_quote(self, response):
        """解析评论的回复"""
        model_name = response.meta["model_name"]
        brand = response.meta["brand"]
        user_name = response.meta["user_name"]
        location = response.meta["location"]
        date = response.meta["date"]
        content = response.meta["content"]
        quote_user_name = response.meta["quote_user_name"]
        quote_date = response.meta["quote_date"]
        quote = response.xpath(".//pre/text()").extract_first()

        item = {"content_url": response.url, "brand": brand, "model_name": model_name, "user_name": user_name,
                "location": location, "date": date,
                "main_body": content}
        content_id_f = self.get_md5(self.website_id + quote + quote_user_name + quote_date)
        yield self.padding_item(item, refer_id=content_id_f)

    @staticmethod
    def parse_date(date):
        """解析时间"""
        result_hours = re.search(r"(.*)hours?", date)
        result_minutes = re.search(r"(.*)minutes", date)
        if result_hours:
            hours = int(result_hours.groups()[0].strip())
            minutes = 0
        elif result_minutes:
            minutes = int(result_minutes.groups()[0].strip())
            hours = 0
        else:
            LOGGER.error(u"未知时间格式，该帖子可能被删除", )
            hours = 0
            minutes = 0
        hours = hours
        minutes = minutes
        now = datetime.now()
        delta = datetime.timedelta(hours=hours, minutes=minutes)
        n_days = now - delta
        n_days = n_days.strftime('%Y-%m-%d %H:%M:%S')
        return n_days

    @staticmethod
    def get_md5(string):
        return hashlib.md5(string.encode('utf8')).hexdigest()


class TakeFirst(object):
    """取values中的第一个元素value，然后去掉value中间过多的空格和换行符，然后去掉首尾的空格"""

    def __call__(self, values):
        for value in values:
            if value is not None and value != '':
                return re.sub(r'\s+', ' ', value).strip()


class GsmarenaItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
