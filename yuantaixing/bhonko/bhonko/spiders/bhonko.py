"""bhonkon"""
import hashlib
from time import strptime, strftime

import scrapy
from scrapy import Selector

from vivo_public_modules.spiders.mix_spider import MixSpider


class BhonkoSpider(MixSpider):
    """bhonko"""
    name = 'bhonko'
    page = 0
    formatdata = {"group_no": str(page)}
    url = "http://www.bhonko.in/index-post.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               "X-Requested-With": "XMLHttpRequest"}

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = "bhonko"
        self.website_type = "complaint"

    def start_requests(self):
        yield scrapy.FormRequest(url=self.url, headers=self.headers, formdata=self.formatdata)

    def parse(self, response):
        self.init_update_time_config()
        current_url = response.url
        temp = Selector(text=response.text)
        divs = temp.xpath(".//div[contains(@class,'col-md-12 no-padd-xs')]")
        if not divs:
            # no more content
            print("==================last page=======================:", self.page)
            return
        for item in divs:
            user_name = item.xpath(".//span[contains(@class,'user-name')]/text()").extract_first()
            time = item.xpath(".//span[contains(@class,'post-time')]/text()").extract_first()
            company = item.xpath(
                ".//div[contains(@class,'col-md-9 col-sm-9 col-xs-9 no-padd')]"
                "/h2/text()").extract_first()

            time = time.replace("Posted on", "").strip() if time else ""
            # "21 March 2018 12:40 PM"
            time = strftime("%Y-%m-%d %H:%M", strptime(time, "%d %B %Y %I:%M %p"
                                                             "")) if time else ""

            title = item.xpath(".//div/h3/text()").extract_first()
            main_body = item.xpath(".//p[contains(@class,'more')]/text()").extract_first()

            # ==================增量更新=============================
            date_to_update = super().get_date_to_update(response, strftime("%Y-%m-%d", strptime(time, "%Y-%m-%d %H:%M")))
            if date_to_update == -1:
                return
            # ==================增量更新=============================
            # 保存content
            item = {"content_url": current_url,
                    "user_url": current_url,
                    "user_name": user_name,
                    "time": time,
                    "company": company,
                    "title": title,
                    "main_body": main_body}
            refer_id = self.get_md5(self.website_id + company)
            yield self.padding_item(item, refer_id=refer_id)

        # nextpage
        self.page += 1
        self.formatdata["group_no"] = str(self.page)
        yield scrapy.FormRequest(url=self.url,
                                 headers=self.headers,
                                 formdata=self.formatdata,
                                 meta={
                                     "first_in": True,
                                     "date_to_update": date_to_update,
                                 })

    @staticmethod
    def get_md5(str):
        return hashlib.md5(str.encode('utf8')).hexdigest()
