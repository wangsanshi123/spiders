import json
import os
import re
from time import strftime, localtime, strptime

import scrapy
from scrapy import Selector

from vivo_public_modules.spiders.mix_spider import MixSpider


class TwitterSearch(MixSpider):
    """通过搜索进入，搜索的是用户的推文"""
    name = 'twitter'
    start_url = "https://twitter.com/search?f=news&vertical=news&q={}"
    base_url = "https://twitter.com/i/search/timeline?vertical=default&q={}&src=typd&include_available_features=1&include_entities=1&max_position={}&reset_error_state=false"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
        "Host": " twitter.com",
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "twitter"
        self.website_type = "social"

    def start_requests(self):
        config_dir = self.settings.get('CONFIG_DIR', None)
        base = os.path.join(config_dir, "website_config/{}.json".format(self.name))
        with open(base, 'r') as f:
            result = json.load(f)
            for item in result:
                brand, model_name, keyword, new_append = item['brand'], item["model_name"], \
                                                         item["keyword"], item["new_append"]
                url = self.start_url.format(keyword)
                yield scrapy.Request(url=url,
                                     meta={
                                         "brand": brand,
                                         "model_name": model_name,
                                         "new_append": new_append,
                                         "keyword": keyword,
                                     })

    def parse(self, response):
        """解析搜索结果，获得翻页id"""
        self.init_update_time_config()
        new_append = response.meta["new_append"]
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]
        keyword = response.meta["keyword"]
        max_position = response.xpath(".//div[contains(@class,'stream-container')]"
                                      "/@data-max-position").extract_first()
        print("max_position:", max_position)
        url = self.base_url.format(keyword, max_position)
        yield scrapy.Request(url=url,
                             callback=self.parse_page,
                             headers=self.headers,
                             meta={
                                 "brand": brand,
                                 "model_name": model_name,
                                 "new_append": new_append,
                                 "keyword": keyword,
                             })

    def parse_page(self, response):
        """解析具体的推文,概要信息"""
        new_append = response.meta["new_append"]
        keyword = response.meta["keyword"]
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]

        data = json.loads(response.body.decode("utf-8"))
        url_current = response.url
        li_list = Selector(text=data['items_html']). \
            xpath(".//li[contains(@id,'stream-item-tweet')]")
        for li_tag in li_list:
            comment_num = li_tag.xpath(".//span[@class='ProfileTweet-action--reply "
                                       "u-hiddenVisually']"). \
                xpath("string(.)").extract_first()

            share_num = li_tag.xpath(".//span[@class='ProfileTweet-action--retweet "
                                     "u-hiddenVisually']"). \
                xpath("string(.)").extract_first()
            thumb_up_num = li_tag.xpath(".//span[@class='ProfileTweet-action--favorite "
                                        "u-hiddenVisually']") \
                .xpath("string(.)").extract_first()

            time = li_tag.xpath(
                ".//span[contains(@class,'_timestamp js-short-timestamp')]/"
                "@data-time").extract_first()
            main_body = li_tag.xpath(".//div[@class='js-tweet-text-container']"). \
                xpath("string(.)").extract_first()

            user_name = li_tag.xpath("//div[contains(@class,'js-stream-tweet')]/@data-name").extract_first()
            main_body = main_body.strip() if main_body else None

            comment_num = self.drop_suffix(comment_num)
            share_num = self.drop_suffix(share_num)
            thumb_up_num = self.drop_suffix(thumb_up_num)
            time = strftime("%Y-%m-%d %H:%M:%S",
                            localtime(float(time))) if time else ""

            # ==================增量更新=============================
            date_to_update = super().get_date_to_update(response, strftime("%Y-%m-%d", strptime(time, "%Y-%m-%d %H:%M:%S")))
            if date_to_update == -1:
                return
            # ==================增量更新=============================

            item = {"main_body": main_body,
                    "share_num": share_num,
                    "content_url": url_current,
                    "content_comment_num": comment_num,
                    "thumb_up_num": thumb_up_num,
                    "user_name": user_name,
                    "time": time
                    }
            yield self.padding_item(item, -1)

            pass
        max_position = data['min_position']
        # get next page
        yield scrapy.Request(url=self.base_url.format(keyword, max_position),
                             callback=self.parse_page,
                             meta={
                                 "first_in": False,
                                 "new_append": new_append,
                                 "keyword": keyword,
                                 "brand": brand,
                                 "model_name": model_name,
                                 "date_to_update": date_to_update,
                             })

        pass

    @staticmethod
    def drop_suffix(item):
        """去掉评论，转发，喜欢后面的单词，eg：25 likes--> 25"""
        if item:
            temp = item.strip().split(" ")[0]
            return re.sub(r"\D", '', temp)
        else:
            return ""
