"""ndtv爬虫"""
import re
from scrapy.http import Request
from .match_spider import MatchDictSpier


class Ndtv(MatchDictSpier):
    """ndtv爬虫类"""
    name = "ndtv"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        self.website_id = 'ndtv'
        self.website_type = 'e-commerce'

        # 匹配字典，根据对应的字典key匹配对应的方法
        self.match_dict = {
            "ndtv_mobile": {
                "parse": self.ndtv_mobile_parse
            },
            "ndtv_mobile_detail": {
                "request": self.simple_new_request,
                "parse": self.ndtv_mobile_detail_parse,
                'save': self.ndtv_mobile_detail_save
            },
            "ndtv_user_reviews": {
                "request": self.simple_new_request,
                "parse": self.ndtv_user_reviews_parse,
                "save": self.ndtv_user_reviews_save,
            },
            "ndtv_news_list": {
                "request": self.simple_new_request,
                "parse": self.ndtv_news_list_parse,
            },
            "ndtv_new": {
                "request": self.simple_next_request,
                "parse": self.ndtv_new_parse,
                "save": self.ndtv_new_save,
            }
        }

    def start_requests(self):
        # 发送起始请求
        url = "https://gadgets.ndtv.com/mobiles/vivo-phones"
        meta = {'url_type': 'ndtv_mobile'}

        yield Request(url, meta=meta, callback=self.parse)

    @staticmethod
    def ndtv_mobile_parse(response):
        """获取所有的机型详情链接"""
        data = {"data": [], "new_request": []}
        url_re = re.compile(r'href="(https://gadgets.ndtv.com/vivo[^?]*?)"')

        url_list = set(url_re.findall(response.text))

        for url in url_list:
            new_request = {'url_type': 'ndtv_mobile_detail', 'url': url, 'params': None}
            data['new_request'].append(new_request)
        return data

    @staticmethod
    def ndtv_mobile_detail_parse(response):
        """解析手机详情页"""
        data = {"data": [], "new_request": []}
        re_dict = dict()
        re_dict['brand'] = re.compile(r'<span class="black" itemprop="brand">(.*?)</span>')
        re_dict['model_name'] = re.compile(r'<h1 data-full-title="(.*?)">')
        re_dict['launch_date'] = re.compile(r'<span itemprop="releaseDate">(.*?)</span>')
        re_dict['model_weight'] = re.compile(r'<td width="50%">Weight \(g\)'
                                             r'</td><td width="50%">(.*?)</td>')
        re_dict['battery'] = re.compile(r'<td width="50%">Battery capacity \(mAh\)'
                                        r'</td><td width="50%">(.*?)</td>')
        re_dict['screen_size'] = re.compile(r'<td width="50%">Screen size \(inches\)'
                                            r'</td><td width="50%">(.*?)</td>')
        re_dict['cpu'] = re.compile(r'Processor</td><td width="50%">(.*?)</td>')
        re_dict['ram'] = re.compile(r'RAM</td><td width="50%">(.*?)</td>')
        re_dict['rom'] = re.compile(r'Internal storage</td><td width="50%">(.*?)</td>')
        re_dict['score_num'] = re.compile(r'<div class="head margin_b10">'
                                          r'Based on (.*?) rating</div>')
        re_dict['model_score'] = re.compile(r'<span class="str_count">(.*?)</span>')
        re_dict['model_comment_num'] = re.compile(r'<span class="randr_dispalying_total">'
                                                  r'(.*?)</span>')

        data_dict = {
            "model_url": response.url,
            "next_url_request": None
        }

        for key, re_compile in re_dict.items():
            value = re_compile.findall(response.text)
            # 由于部分网页本身数据不完整，进行数据预判断
            if value:
                data_dict[key] = value[0]
            else:
                data_dict[key] = ""

        new_reviews_request = {"url_type": "ndtv_user_reviews",
                               "url": response.url+r"/user-reviews",
                               "params": None}

        new_news_request = {"url_type": "ndtv_news_list",
                            "url": response.url+r"/news",
                            "params": None}

        data['data'].append(data_dict)
        data['new_request'].append(new_reviews_request)
        data['new_request'].append(new_news_request)
        return data

    def ndtv_mobile_detail_save(self, data):
        """保存手机详情页数据"""
        return self.generate_item(data, -1)

    @staticmethod
    def ndtv_user_reviews_parse(response):
        """解析手机用户评论页数据"""
        data = {"data": [], "new_request": []}

        comment_list_xpath = '//div[@itemprop="review"]'
        xpath_dict = dict()
        xpath_dict['title'] = './/div[@class="cmnt_title"]/text()'
        xpath_dict['user_name'] = './/span[@itemprop="name"]/text()'
        xpath_dict['date'] = './/span[@itemprop="datePublished"]/text()'
        xpath_dict['main_body'] = './/div[@class="user_cmnt_text"]/text()'
        xpath_dict['main_body_score'] = './/div[@class="total_r_text"]/text()'

        for comment in response.xpath(comment_list_xpath):
            temp_dict = dict()
            for key, xpath in xpath_dict.items():
                temp_dict[key] = comment.xpath(xpath).extract_first()
            temp_dict['content_url'] = response.url
            temp_dict['next_url_request'] = None

            data['data'].append(temp_dict)

        return data

    def ndtv_user_reviews_save(self, data):
        """保存手机用户评论页数据"""

        return self.generate_item(data, -1)

    @staticmethod
    def ndtv_news_list_parse(response):
        """解析手机新闻列表页请求"""
        data = {"data": [], "new_request": []}

        url_xpath = '//div[@class="caption_box"]/a/@href'
        model_name_xpath = '//h1/text()'

        url_list = response.xpath(url_xpath).extract()
        model_name = response.xpath(model_name_xpath).extract_first()
        for url in url_list:
            data_dict = dict()
            data_dict['model_name'] = model_name
            data_dict['next_url_request'] = {'url_type': 'ndtv_new', 'url': url, 'params': None}
            data['data'].append(data_dict)

        return data

    @staticmethod
    def ndtv_new_parse(response):
        """解析手机新闻页数据"""
        data = {"data": [], "new_request": []}
        xpath_dict = dict()
        xpath_dict['title'] = '//h1/span/text()'
        xpath_dict['user_name'] = '//span[@itemprop="name"]/text()'
        xpath_dict['time'] = '//span[@class="value-title"]/@title'
        xpath_dict['main_body'] = 'string(//div[@id="center_content_div"])'
        xpath_dict['content_comment_num'] = '//span[@class="ndtv-detailp-comments-count"]/text()'

        data_dict = dict()
        for key, xpath in xpath_dict.items():
            data_dict[key] = response.xpath(xpath).extract_first()

        data_dict['content_url'] = response.url
        data_dict['next_url_request'] = None

        data['data'].append(data_dict)
        return data

    def ndtv_new_save(self, data):
        """保存手机新闻页数据"""
        return self.generate_item(data, -1)
