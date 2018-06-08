"""概要信息页"""

import datetime
import hashlib
import json
import re
from time import localtime
from time import strftime
from time import strptime

import os
import scrapy
from scrapy.loader import ItemLoader

from vivo_public_modules.spiders.mix_spider import MixSpider


class MobilescoutSpider(MixSpider):
    name = 'mobilescout'
    page = 1

    base_url = "https://www.mobilescout.com"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "mobilescout"
        self.website_type = "complaint"

    def start_requests(self):
        file = self.get_config_file()
        with open(file, 'r') as f:
            result = json.load(f)
            for item in result:
                url = item["url"]
                del item["url"]
                yield scrapy.Request(url=url, meta=item)

    def parse(self, response):
        """解析首页"""
        current_url = response.url
        brand = response.meta["brand"]
        new_append = response.meta["new_append"]
        li_list = response.xpath(".//li[contains(@class,'threadbit')]")
        last_page = response.xpath(".//a[contains(@title,'Last Page')]")
        if not last_page:
            # the last page
            return
        self.page += 1
        for tag_li in li_list:
            # 保存概要信息（content）
            item = {}
            item_loader = MobileScoutItemLoader(item=item, selector=tag_li)
            item_loader.add_xpath('main_body', ".//a[@class='title']/text()")
            item_loader.add_xpath('comment_url', ".//a[@class='title']/@href")
            item_loader.add_xpath('user_name', ".//a[@class='username understate']/text()")
            item_loader.nested_xpath(".//span[@class='label']").add_xpath('time', "string()")

            item_loader.add_xpath('comment_num', ".//a[@class='understate']/text()")
            item_loader.add_xpath('view_num', ".//div/ul/li[2]/text()")
            item_loader.add_value("brand", brand)
            item_loader.add_value("content_url", current_url)
            item = self.format_item(item_loader.load_item())

            yield self.padding_item(item, refer_id=-1)

            comment_url = item["comment_url"]
            yield scrapy.Request(url=self.base_url + comment_url, callback=self.parse_comment,
                                 meta={
                                     "brand": brand,
                                     "main_body": item["main_body"],
                                     "user_name": item["user_name"],
                                     "time": item["time"],
                                     "new_append": new_append,

                                 })

        # next  page
        yield scrapy.Request(url=current_url + "page{}/".format(self.page),
                             meta={
                                 "brand": brand,
                                 "new_append": new_append,
                             })

    def format_item(self, item):
        """格式化item"""
        for key, value in item.items():
            item[key] = value.strip() if value else ""
        item["time"] = item["time"].split(",")[1].strip() if item["time"] else ""
        item["time"] = self.format_date(item["time"])
        item["view_num"] = item["view_num"].replace("Views:", "").strip() if item["view_num"] else ""

        return item

    def parse_comment(self, response):
        """解析评论页 评论数较少，不做翻页和增量更新了"""
        current_url = response.url
        brand = response.meta["brand"]
        main_body = response.meta["main_body"]
        user_name = response.meta["user_name"]
        time = response.meta["time"]

        li_list = response.xpath(".//li[contains(@id,'post_')]")
        for tag_li in li_list[1:]:
            item = {}
            item_loader = MobileScoutItemLoader(item=item, selector=tag_li)
            item_loader.nested_xpath(".//span[@class='date']").add_xpath("time", "string()")
            item_loader.nested_xpath(".//a[@class='username offline popupctrl']").add_xpath("user_name", "string()")
            item_loader.nested_xpath(".//div[contains(@id,'post_message')]").add_xpath("main_body", "string()")
            item_loader.nested_xpath(".//div[contains(@class,'quote_container')]").add_xpath("main_body_extra",
                                                                                             "string()")

            item_loader.nested_xpath(".//span[@class='usertitle']").add_xpath("user_level", "string()")
            item_loader.add_xpath("registration_date", ".//dl[@class='userinfo_extra']/dd/text()")
            item_loader.add_xpath("user_comment_num", ".//dl[@class='userinfo_extra']/dd[2]/text()")
            item_loader.add_value("brand", brand)
            item_loader.add_value("content_url", current_url)
            item_loader.add_value("user_url", current_url)
            item = self.format_item_comments(item_loader.load_item())
            refer_id = self.get_md5(self.website_id + main_body + user_name + time)
            # print("time:", item["time"])
            yield self.padding_item(item, refer_id=refer_id)

    def format_item_comments(self, item):
        """格式化评论页的item"""
        item["time"] = self.format_date(item["time"])
        item["registration_date"] = strftime("%Y-%m-%d",
                                             strptime(item["registration_date"], "%b %Y")) \
            if item["registration_date"] else ""
        item["user_comment_num"] = item["user_comment_num"].replace(",", "") if item["user_comment_num"] else ""
        if "main_body_extra" in item:
            item["main_body"] = item["main_body"].replace(item["main_body_extra"], "")
        return item

    def format_date(self, date):
        """格式化时间"""
        # "03-20-2018 05:13 PM"
        # "Today 08:16 dM"
        # "Yesterday 06:52 PM"
        try:
            if "Today" in date:
                date = strftime("%m-%d-%Y", localtime()) + date.replace("Today", "")

            elif "Yesterday" in date:
                now = datetime.datetime.today()
                delta = datetime.timedelta(days=-1)
                n_days = now + delta
                date = n_days.strftime('%m-%d-%Y') + date.replace("Yesterday", "")
            date = strftime("%Y-%m-%d %H:%M", strptime(date, "%m-%d-%Y, %I:%M %p")) \
                if date else ""
        except ValueError:
            date = ""
        return date

    @staticmethod
    def get_md5(str):
        return hashlib.md5(str.encode('utf8')).hexdigest()


class TakeFirst(object):
    """取values中的第一个元素value，然后去掉value中间过多的空格和换行符，然后去掉首尾的空格"""

    def __call__(self, values):
        for value in values:
            if value is not None and value != '':
                return re.sub(r'\s+', ' ', value).strip()


class MobileScoutItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
