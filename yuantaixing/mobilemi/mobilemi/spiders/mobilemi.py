"""手机概要信息"""
import json
import os
import re
from time import localtime
from time import strftime
import scrapy
from vivo_public_modules.common_tool.dbbaseutil import get_md5
from vivo_public_modules.spiders.mix_spider import MixSpider


class MobilemiSpider(MixSpider):
    """手机概要信息，评分和评论数等参数无法直接获得"""
    name = "mobilemi"

    base_url = "http://m.buy.mi.com/in/comment/commentlist?product_id={}&orderby=0&pageindex=" \
               "{}&showimg=0&_=1521796496550&jsonpcallback=nextPage"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "mobile_mi"
        self.website_type = "e-commerce"

    def start_requests(self):
        config_dir = self.settings.get('CONFIG_DIR', None)
        base = os.path.join(config_dir, "website_config/{}.json".format(self.name))
        with open(base, 'r')as file:
            result = json.load(file)
            for item in result:
                brand, model_name, new_append, url = item["brand"], item["model_name"], item["new_append"], item["url"]
                yield scrapy.Request(url=url + "#specs",
                                     meta={"brand": brand,
                                           "model_name": model_name,
                                           "url": url,
                                           "new_append": new_append,
                                           }
                                     )

    def parse(self, response):
        self.init_update_time_config()
        brand = response.meta["brand"]
        new_append = response.meta["new_append"]
        model_name = response.meta["model_name"]
        comment_url = response.meta["url"].replace("#specs", "#review")
        configure = response.xpath(".//*[contains(@class,'main-con overview-con')]") \
            .xpath("string()").extract_first()
        configure = response.xpath(".//*[@class='main-con specs-con']") \
            .xpath("string()").extract_first() if not configure else configure
        try:
            configure = re.split(r"\s", configure) if configure else ""
        except Exception:
            configure = ""
        if configure and len(configure) > 1:
            match = re.search(r'product_id=(.*)', comment_url)
            if match:
                product_id = match.groups()[0]
            else:
                product_id = ""
            page_index = 0
            comment_url = self.base_url.format(product_id, page_index)

            yield scrapy.Request(url=comment_url,
                                 meta={
                                     "brand": brand,
                                     "model_name": model_name,
                                     "page_index": page_index,
                                     "product_id": product_id,
                                     "new_append": new_append,
                                 },
                                 callback=self.parse_comments)

    def parse_comments(self, response):
        """解析评论页"""
        current_url = response.url
        new_append = response.meta["new_append"]
        page_index = response.meta["page_index"]
        brand = response.meta["brand"]
        model_name = response.meta["model_name"]
        product_id = response.meta["product_id"]
        page_index += 1
        data = self.format_response(response)
        if data is not None and data != '':  # data不为空才解析本页，否则直接请求下一页
            errmsg = data["errmsg"]
            # the last page
            if errmsg != "Success":
                return
            comments = data['data']['comments']
            for comment in comments:
                time = comment["add_time"]
                time = localtime(float(time))

                item = {"content_url": current_url,
                        "time": strftime("%Y-%m-%d %H:%M:%S", time),
                        "model_name": model_name,
                        "user_name": comment["user_name"],
                        "main_body_score": comment["total_grade"],
                        "main_body": comment["comment_content"],
                        "thumb_up_num": comment["up_num"],
                        "content_comment_num": comment["user_reply_num"]}

                model_id = get_md5(self.website_id + model_name)

                # ==================增量更新=============================
                date_to_update = super().get_date_to_update(response, strftime("%Y-%m-%d", time))
                if date_to_update == -1:
                    return
                # ==================增量更新=============================

                yield self.padding_item(item, refer_id=model_id)

        # the next page
        comment_url = self.base_url.format(product_id, page_index)
        yield scrapy.Request(url=comment_url,
                             meta={"brand": brand,
                                   "model_name": model_name,
                                   "page_index": page_index,
                                   "product_id": product_id,
                                   "new_append": new_append,
                                   "date_to_update": date_to_update,
                                   "first_in": False,
                                   },
                             callback=self.parse_comments)

    def format_response(self, response):
        '''格式化返回的内容'''
        data = response.text
        data = re.search(r"nextPage(\(.*\))", data)
        if data:
            data = data.groups()[0]
        else:
            # 直接解析下一页
            data = ''
        data = data.replace(r"<br \/>\\n", "")
        data = data.replace("\\", "")
        data = re.sub(r"\s", " ", data)
        try:
            data = json.loads(data[1:len(data) - 1])
        except Exception:
            # 直接解析下一页
            data = ''
        return data
