"""概要信息页"""
import hashlib
import json
import re
from time import strptime, strftime

import scrapy
from datetime import datetime
from scrapy import Selector

from vivo_public_modules.spiders.mix_spider import MixSpider


class AmazonSpider(MixSpider):
    """概要信息页 搜索页面的结果被亚马逊封了，要求验证，所以只能用selenium的方式爬取"""

    name = "amazon"
    website_id = "amazon"
    base_url = 'https://www.amazon.in/s/ref=nb_sb_noss_2?url=node%3D1805560031&field-keywords={}' \
               '&rh=n%3A976419031%2Cn%3A1389401031%2Cn%3A1389432031%2Cn%3A1805560031%2Ck%3A{}'
    headers = {"X-Requested-With": "XMLHttpRequest",
               "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
    head_url = "https://www.amazon.in/"
    formdata = {'asin': "",
                'deviceType': "desktop",
                "filterByKeyword": "",
                "filterByStar": "",
                "formatType": "",
                "pageNumber": "1",
                "pageSize": "10",
                "reftag": "cm_cr_getr_d_paging_btm_1",
                'reviewerType': "",
                "scope": "reviewsAjax1",
                "shouldAppend": "undefined",
                "sortBy": "recent"}

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "amazon"
        self.website_type = "e-commerce"

    def start_requests(self):
        config_file = self.get_config_file()
        with open(config_file, 'r') as f:
            result = json.load(f)
            for item in result:
                brand, model_name, new_append = item["brand"], item["model_name"], item["new_append"]
                keyword = "{}+{}".format(brand, model_name)
                url = self.base_url.format(keyword, keyword)
                yield scrapy.Request(url=url,
                                     meta={
                                         "new_append": new_append,
                                         "brand": brand,
                                         "model_name": model_name
                                     })

    def parse(self, response):
        """解析搜索页面"""
        self.init_update_time_config()
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]
        selector = Selector(text=response.body)
        new_append = response.meta["new_append"]
        count = selector.xpath(".//*[@id='s-result-count']/text()").extract_first()
        count = str(count.split(" ")[0]) if count else 0
        if isinstance(count, str) and not count.strip("").isdigit():
            # 此种情况搜索结果过多，且大多为无用结果，所以排除
            count = 10
        print("====count====:", count)
        for i in range(int(count)):
            url = selector.xpath("//*[@id='result_{}']/div/div[3]/div[1]/a/@href".
                                 format(i)).extract_first()
            if url:
                yield scrapy.Request(url=url,
                                     callback=self.parse_model,
                                     meta={
                                         "new_append": new_append,
                                         "brand": brand,
                                         "model_name": model_name
                                     })

    def parse_model(self, response):
        """解析指定型号手机的搜索信息"""
        new_append = response.meta["new_append"]
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]

        selector = Selector(text=response.body)
        url = response.url

        price = selector.xpath(".//*[@id='olp_feature_div']/div/span/span/text()").extract_first()
        comment_num = selector.xpath(".//*[@id='acrCustomerReviewText']/text()").extract_first()

        price = float(price.replace(",", "")) if price else 0

        if not comment_num or (0 < price < 2000):
            print("=====comment_num=====", comment_num)
            return
        else:
            yield from self.parse_model_info(selector, brand, model_name, url, new_append)

    def parse_model_info(self, response, brand, model_name, url, new_append):
        "解析指定手机型号概要信息"
        print("==========parse_model_info=============")
        current_url = url
        dict_temp = {}
        score = response.xpath(".//*[@id='acrPopover']/span[1]/a/i[1]/span/text()").extract_first()
        comment_num = response.xpath(".//*[@id='acrCustomerReviewText']/text()").extract_first()
        sellers_num = response.xpath(".//*[@id='olp_feature_div']/div/span/a/text()").extract_first()
        price = response.xpath(".//*[@id='olp_feature_div']/div/span/span/text()").extract_first()

        total_items = len(response.xpath(".//*[@id='prodDetails']/div/div[1]/div/div[2]"
                                         "/div/div/table//tr"))

        for i in range(total_items - 1):
            item_name = response.xpath(
                ".//*[@id='prodDetails']/div/div[1]/div/div[2]/div/div/table//tr[{}]/"
                "td[1]/text()".format(
                    i + 1)).extract_first().strip()
            item_value = response.xpath(
                ".//*[@id='prodDetails']/div/div[1]/div/div[2]/div/div/table//tr[{}]/"
                "td[2]/text()".format(
                    i + 1)).extract_first().strip()
            dict_temp[item_name] = item_value

        ram = self.get_value_from_dict(dict_temp, "RAM")
        dimensions = self.get_value_from_dict(dict_temp, "Product Dimensions")
        weight = self.get_value_from_dict(dict_temp, "Weight")
        selling_points = self.get_value_from_dict(dict_temp, "Special features")
        colour = self.get_value_from_dict(dict_temp, "Colour")
        battery = self.get_value_from_dict(dict_temp, "Battery Power Rating")

        asin = response.xpath(
            ".//*[@id='prodDetails']/div/div[2]/div[1]/div[2]/div/div/table//"
            "tr[1]/td[2]/text()").extract_first()
        best_sellers_rank = response.xpath(".//*[@id='SalesRank']/td[2]/ul/"
                                           "li/span[1]/text()").extract_first()
        sell_date = response.xpath(
            ".//*[@id='prodDetails']/div/div[2]/div[1]/div[2]/div/div/table//"
            "tr[4]/td[2]/text()").extract_first()
        comment_url = self.head_url + response.xpath('//*[@id="acrCustomerReviewLink"]'
                                                     '/@href').extract_first()
        comment_url = comment_url + "&sortBy=recent"
        score = score.split(" ")[0] if score else 0
        price = float(price.replace(",", "")) if price else 0
        sellers_num = re.search(r'(\d*)', sellers_num).groups()[0] if sellers_num else 0

        comment_num = comment_num.split(" ")[0] if comment_num else 0
        ram = ram.split(" ")[0] if ram else 0
        model_weight = weight.split(" ")[0] if weight else 0
        best_sellers_rank = best_sellers_rank.strip("#") if best_sellers_rank else 0
        try:
            sell_date = strftime("%Y-%m-%d", strptime(sell_date, "%d %B %Y"))
        except ValueError:
            sell_date = ""
        yield scrapy.Request(url=comment_url,
                             meta={
                                 "brand": brand,
                                 "model_name": model_name,
                                 "asin": asin,
                                 "comment_url": comment_url,
                                 "new_append": new_append,
                             },
                             callback=self.parse_comments)

        # 保存model信息
        item = {"brand": brand,
                "model_url": current_url,
                "model_name": model_name,
                "price": price,
                "model_score": score,
                "model_comment_num": comment_num,
                "sellers_num": sellers_num,
                "ram": ram,
                "model_weight": model_weight,
                "dimensions": dimensions,
                "colour": colour,
                "battery": battery,
                "selling_points": selling_points,
                "sell_date": sell_date,
                "best_sellers_rank": best_sellers_rank}
        yield self.padding_item(item, "")

    def parse_comments(self, response):

        current_url = response.url
        brand = response.meta["brand"]
        new_append = response.meta["new_append"]
        model_name = response.meta["model_name"]
        asin = response.meta["asin"]
        comment_url = response.meta["comment_url"]
        try:
            page_number = response.meta["page_number"]
        except KeyError:
            page_number = 1
        page_number += 1
        selector = Selector(text=response.body)
        div_list = selector.xpath("//div[@data-hook='review']")

        for div_tag in div_list:
            title = div_tag.xpath(".//a[contains(@data-hook,'review-title')]/text()").extract_first()
            user_name = div_tag.xpath(".//a[contains(@data-hook,'review-author')]/text()").extract_first()
            main_body_score = div_tag.xpath(".//span[@class='a-icon-alt']/text()").extract_first()
            main_body = div_tag.xpath(".//span[contains(@data-hook,'review-body')]").xpath("string()").extract_first()

            date_or_time = div_tag.xpath(".//span[contains(@data-hook,'review-date')]/text()").extract_first()
            date_or_time = self.format_time(date_or_time)

            # 保存评论（content）信息
            item = {"content_url": current_url,
                    'brand': brand,
                    'model_name': model_name,
                    'main_body_score': main_body_score,
                    'user_name': user_name,
                    'title': title,
                    'date': date_or_time,
                    'main_body': main_body}
            model_id = self.get_md5(self.website_id + model_name)
            yield self.padding_item(item, refer_id=model_id)

        # get nextpage
        if len(div_list) >= 8:
            # ==================增量更新=============================
            date_to_update = super().get_date_to_update(response, date_or_time)
            if date_to_update == -1:
                return
            # ==================增量更新=============================
            next_page = "{}/ref=cm_cr_arp_d_paging_btm_{}?showViewpoints=1&sortBy=recent&pageNumber={}".format(
                comment_url.split("ref")[0], page_number, page_number)

            yield scrapy.Request(next_page,
                                 meta={
                                     "page_number": page_number,
                                     "asin": asin,
                                     'brand': brand,
                                     "model_name": model_name,
                                     "comment_url": comment_url,
                                     "date_to_update": date_to_update,
                                     "new_append": new_append,
                                     "first_in": False,
                                 },
                                 callback=self.parse_comments)
        else:
            print("=====the last url========:", current_url)

    @staticmethod
    def get_value_from_dict(dic, key):
        """从字典中获取指定key的value,如没有这个key,则返回'' """
        if key in dic:
            return dic[key]
        else:
            return ""

    @staticmethod
    def get_md5(str):
        return hashlib.md5(str.encode('utf8')).hexdigest()

    def format_time(self, date_or_time):
        if date_or_time:
            date = strftime("%Y-%m-%d", strptime(date_or_time.replace("on", "").strip(), "%d %B %Y"))
        else:
            date = ""
        return date
