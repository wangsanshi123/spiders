"""gsmdevelopers爬虫"""
# -*- coding: utf-8 -*-
import re
from scrapy.http import Request
from .match_spider import MatchDictSpier


class GSMDevelopers(MatchDictSpier):
    """gsmdevelopers爬虫类"""
    name = "gsmdevelopers"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        self.website_id = "gsmdevelopers"
        self.website_type = "complaint"

        self.match_dict = {
            "gsm_forum_list": {
                "parse": self.gsm_forum_list_parse,
            },
            "gsm_forum": {
                'request': self.simple_new_request,
                'parse': self.gsm_forum_parse,

            },
            "gsm_thread": {
                'request': self.simple_new_request,
                'parse': self.gsm_thread_parse,
                'save': self.gsm_thread_save,

            }
        }

    def start_requests(self):
        """请求论坛板块列表页"""
        url = "http://forum.gsmdevelopers.com/technical-support-section-for-major-brands"
        meta = {'url_type': 'gsm_forum_list'}
        # 发送板块列表页请求
        yield Request(url, meta=meta, callback=self.parse)

    @staticmethod
    def gsm_forum_list_parse(response):
        """解析板块列表页，获取各个板块的链接地址"""
        data = {"data": [], "new_request": []}

        forum_urls_xpath = '//ol[@class="childsubforum"]//h2/a/@href'

        forum_url_list = response.xpath(forum_urls_xpath).extract()
        # 测试！！！！！！！！！！！！只取获取一个版块信息
        for url in forum_url_list[:1]:
            new_request = {'url_type': 'gsm_forum', 'url': url, 'params': None}
            data['new_request'].append(new_request)

        return data

    @staticmethod
    def gsm_forum_parse(response):
        """解析板块页，获取各个主题的链接地址"""
        data = {"data": [], "new_request": []}

        thread_urls_xpath = '//a[@class="title"]/@href'
        next_page_xpath = '//a[@rel="next"]/@href'

        thread_url_list = response.xpath(thread_urls_xpath).extract()
        next_page_url = response.xpath(next_page_xpath).extract_first()

        for url in thread_url_list:
            new_request = {'url_type': 'gsm_thread', 'url': url, 'params': None}
            data['new_request'].append(new_request)

        # 翻页请求
        if next_page_url:
            next_page_request = {'url_type': 'gsm_forum', 'url': next_page_url, 'params': None}
            data['new_request'].append(next_page_request)

        return data

    def gsm_thread_parse(self, response):
        """解析主题页，获取每个帖子的信息"""
        data = {"data": [], "new_request": []}

        next_page_xpath = '//a[@rel="next"]/@href'
        post_list_xpath = '//li[@class="postbitlegacy postbitim postcontainer old"]'
        title_xpath = '//span[@class="threadtitle"]/a/text()'
        xpath_dict = dict()
        xpath_dict['rule_type'] = "xpath"
        xpath_dict['user_name'] = './/strong//text()'
        xpath_dict['time'] = 'string(.//span[@class="date"])'
        xpath_dict['main_body'] = 'string(.//blockquote)'
        xpath_dict['floor'] = './/a[@class="postcounter"]/text()'

        title = response.xpath(title_xpath).extract_first()
        for comment in response.xpath(post_list_xpath):
            temp_dict = self.get_rule_data(xpath_dict, comment)
            temp_dict['content_url'] = response.url
            temp_dict['title'] = title
            temp_dict['next_url_request'] = None
            data['data'].append(temp_dict)

        # 翻页请求
        next_page_url = response.xpath(next_page_xpath).extract_first()
        if next_page_url:
            next_page_request = {'url_type': 'gsm_thread', 'url': next_page_url, 'params': None}
            data['new_request'].append(next_page_request)

        return data

    def gsm_thread_save(self, data):
        """格式化帖子信息，并保存"""
        data['main_body'] = re.sub(r'[\n\t\r]', '', data['main_body'])
        data['time'] = re.sub(r',\xa0', ' ', data['time'])
        data['floor'] = re.sub(r'#', '', data['floor'])
        return self.generate_item(data, -1)
