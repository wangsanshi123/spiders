"""twitter文章页（概要信息）"""
import hashlib
import json
import re
from time import localtime, strftime

import scrapy
from scrapy import Selector

from vivo_public_modules.spiders.mix_spider import MixSpider


class TwitterSpider(MixSpider):
    """twitter文章页（概要信息）"""
    # name = 'twitter'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "twitter"
        self.website_type = "social"

    def start_requests(self):
        accounts = ['Vivo_India']
        for account in accounts:
            account = account
            model_id = self.get_md5(self.website_id + account)  # 这里将account作为model_name
            yield scrapy.Request(url='https://twitter.com/{}?lang=en'.
                                 format(account), meta={"account": account})

    def parse(self, response):
        """解析twitter账户信息"""
        url_current = response.url
        user_name = response.meta["account"]
        post_num = response.xpath(
            ".//li[@class='ProfileNav-item ProfileNav-item--tweets is-active']//"
            "span[@class='ProfileNav-value']/@data-count").extract_first()
        following_num = response.xpath(
            ".//li[@class='ProfileNav-item ProfileNav-item--following']//"
            "span[@class='ProfileNav-value']/@data-count").extract_first()
        follower_num = response.xpath(
            ".//li[@class='ProfileNav-item ProfileNav-item--followers']//"
            "span[@class='ProfileNav-value']/@data-count").extract_first()
        post_thumb_up_num = response.xpath(
            ".//li[@class='ProfileNav-item ProfileNav-item--favorites']//"
            "span[@class='ProfileNav-value']/@data-count").extract_first()
        region = response.xpath(".//span[@class='ProfileHeaderCard-locationText u-dir']") \
            .xpath("string(.)").extract_first()
        region = region.strip() if region else ""
        min_position = response.xpath(".//div[contains(@class,'stream-container')]"
                                      "/@data-min-position").extract_first()

        # print('min_position:', min_position)
        url = "https://twitter.com/i/profiles/show/{}/" \
              "timeline/tweets?include_available_features=1&" \
              "include_entities=1&max_position={}&reset_error_state=false". \
            format(user_name, min_position)
        yield scrapy.Request(url, callback=self.parse_page,
                             meta={"user_name": user_name})

        item = {"user_name": user_name, "user_url": url_current, "region": region, "follower_num": follower_num,
                "following_num": following_num, "post_num": post_num, "post_thumb_up_num": post_thumb_up_num}
        yield self.padding_item(item, refer_id="")

    def parse_page(self, response):
        """解析twitter文章相关信息"""
        user_name = response.meta["user_name"]
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
            main_body = main_body.strip() if main_body else None

            comment_num = self.drop_suffix(comment_num)
            share_num = self.drop_suffix(share_num)
            thumb_up_num = self.drop_suffix(thumb_up_num)
            time = strftime("%Y-%m-%d %H:%M:%S",
                            localtime(float(time))) if time else ""

            # =================增量更新=========================
            # if time and max_time and time < max_time:  # 增量更新（如果当前时间早于上次更新的最早时间，则停止更新）
            #     print("增量更新，time:max_time：", time + max_time)
            #     return
            # =================增量更新=========================

            if comment_num and comment_num.strip() and share_num and share_num.strip() and \
                    thumb_up_num and thumb_up_num.strip() and main_body and main_body.strip() \
                    and time and time.strip():
                item = {"user_name": user_name, "main_body": main_body, "content_url": url_current,
                        "content_comment_num": comment_num, "thumb_up_num": thumb_up_num, "time": time}
                yield self.padding_item(item, -1)

        min_position = data['min_position']
        url = "https://twitter.com/i/profiles/show/{}/timeline/tweets?" \
              "include_available_features=1&include_entities=1&max_position={}" \
              "&reset_error_state=false".format(user_name, min_position)

        # get next page
        has_more_items = data["has_more_items"]
        if has_more_items:
            yield scrapy.Request(url=url, callback=self.parse_page,
                                 meta={'user_name': user_name, })
        else:
            print("=======over======")

    @staticmethod
    def drop_suffix(item):
        """去掉评论，转发，喜欢后面的单词，eg：25 likes--> 25"""
        if item:
            temp = item.strip().split(" ")[0]
            return re.sub(r"\D", '', temp)
        else:
            return ""

    @staticmethod
    def get_md5(str):
        return hashlib.md5(str.encode('utf8')).hexdigest()

    @staticmethod
    def get_current_time():
        return strftime("%Y-%m-%d %H:%M:%S", localtime())
