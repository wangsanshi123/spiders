"""概要信息页"""
import json
from time import strftime
from time import strptime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose

from vivo_public_modules.common_tool.dbbaseutil import get_md5
from vivo_public_modules.spiders.mix_spider import MixSpider


class MysmartpriceSpider(MixSpider):
    """概要信息页"""
    name = 'mysmartprice'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "mysmartprice"
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
        self.init_update_time_config()
        brand = response.meta["brand"]
        model_url = response.url
        model_name = response.meta["model_name"]
        price = response.xpath(".//span[@class='prdct-dtl__prc-val']/text()").extract_first()
        price = price.replace(",", "") if price else ""
        temp = {}
        tr_list = response.xpath(".//tr[@class='tchncl-spcftn__item']")
        for tag_li in tr_list:
            key = tag_li.xpath(".//td[@class='tchncl-spcftn__tag_li-key']/text()").extract_first()
            value = tag_li.xpath(".//td[@class='tchncl-spcftn__item-val']") \
                .xpath("string()").extract_first()
            temp[key] = value

        size = self.get_value_from_dict(temp, "Size (in inches)")

        rom = self.get_value_from_dict(temp, "Internal")
        rom = rom.replace("GB", "") if rom else ""

        ram = self.get_value_from_dict(temp, "RAM")
        ram = ram.replace("GB", "") if ram else ""

        battery = self.get_value_from_dict(temp, "Capacity")
        battery = battery.replace("mAh", "") if battery else ""

        cpu = self.get_value_from_dict(temp, "Variant")

        score = response.xpath(".//div[@class='usr-rvw__scr-cur']/text()").extract_first()
        comment_num = response. \
            xpath(".//div[@class='usr-rvw__rvwstr-rvws text-link js-open-link']/text()").extract_first()

        comment_num = comment_num.replace("reviews ➝", "").strip() if comment_num else ""
        comment_url = response.xpath(
            ".//div[@class='usr-rvw__rvwstr-rvws text-link js-open-link']"
            "/@data-open-link").extract_first()
        if comment_num and int(comment_num) > 0:  # 只有评论数大于零的情况才会进入到评论页

            yield scrapy.Request(url=comment_url,
                                 meta={
                                     "brand": brand,
                                     "model_name": model_name,
                                 },
                                 callback=self.parse_comments)

        # 保存model信息
        item = {"screen_size": size,
                "price": price,
                "ram": ram,
                "rom": rom,
                "battery": battery,
                "cpu": cpu,
                "model_score": score,
                "model_comment_num": comment_num,
                "model_url": model_url,
                "model_name": model_name}
        yield self.padding_item(item, refer_id="")

    def parse_comments(self, response):
        """解析评论页"""
        """由于评论量不足，且只能看到10条评论，且评论不能严格按照时间排序，所以不做增量更新，每次都爬取尽可能多的评论，然后去重保存"""
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]

        div_list = response.xpath(".//div[@class='review_item']")
        for div_tag in div_list:
            # 保存概要信息（content）
            item = {}
            item_loader = MysmartphoneItemLoader(item=item, selector=div_tag)
            item_loader.add_value("brand", brand)
            item_loader.add_value("model_name", model_name)
            item_loader.add_xpath("user_name", ".//div[@class='user_name']/text()")
            item_loader.add_xpath("date", ".//div[@class='review_date']/text()")
            item_loader.nested_xpath(".//span[@class='review-useful-count']").add_xpath("thumb_up_num", "string()")
            item_loader.nested_xpath(".//div[@class='review_heading']").add_xpath("title", "string()")
            item_loader.nested_xpath(".//div[@class='review_details']").add_xpath("main_body", "string()")
            item_loader.add_xpath("score", ".//div[@class='review_user_rating_bar_out']/@data-rating")
            item = item_loader.load_item()
            model_id = get_md5(self.website_id + item["model_name"])
            yield self.padding_item(item, refer_id=model_id)

    @staticmethod
    def get_value_from_dict(dic, key):
        """从字典中获取指定key的value,如没有这个key,则返回'' """
        if key in dic:
            return dic[key]
        else:
            return ""


class MysmartphoneItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
    time_out = Compose(TakeFirst(), lambda x: strftime("%Y-%m-%d", strptime(x, "%B %d, %Y")) if x else "")
