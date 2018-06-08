"""
解析数据和爬虫逻辑模块
"""
import json
import logging
import re
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider
from ..itemloader import DataLoader


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'indian_mi'
    allowed_domains = ['c.mi.com']
    start_urls = ['http://c.mi.com/ajax.php?page=0&perpage=10']

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        """
        super().__init__(name, **kwargs)

        self.website_id = 'indian_mi'
        self.website_type = 'complaint'

        self.post_xpath = dict()
        self.post_xpath['title'] = '//*[@id="thread_subject"]/text()'
        self.post_xpath['time'] = '//*[@id="postlist"]/div[1]/div/div/div[1]/span/text()'
        self.post_xpath['view_num'] = '//*[@id="postlist"]/div[1]/div/div/div[2]/span[1]/text()'
        self.post_xpath[
            'content_comment_num'] = '//*[@id="postlist"]/div[1]/div/div/div[2]/span[2]/text()'
        self.post_xpath['main_body'] = '//*[@id="J_shareDesc"]/table/tr/td//font/text()'
        self.post_xpath['favor_num'] = '//*[@id="favoritenumber"]/text()'
        self.post_xpath[
            'user_name'] = '//*[@id="wp"]/div/div/div[2]/div[1]/div/div[1]/div[2]/p[1]/a/text()'
        self.post_xpath[
            'user_url'] = '//*[@id="wp"]/div/div/div[2]/div[1]/div/div[1]/div[2]/p[1]/a/@href'

        self.comment_list_xpath = '//*[@class="subject-content other-floor"]'
        self.comment_xpath = dict()
        self.comment_xpath[
            'model_name'] = './div/div/div[1]/div/div[1]/div/div[3]/div[1]/p/span[2]/text()'
        self.comment_xpath['main_body'] = './div/div/div[1]/div/div[2]/div/div/table/tr/td/text()'
        self.comment_xpath['floor'] = './div/div/div[1]/div/div[1]/div/div[3]/div[2]/p/em/text()'
        self.comment_xpath['time'] = './div/div/div[2]/div/div/span/text()'
        self.comment_xpath[
            'user_name'] = './div/div/div[1]/div/div[1]/div/div[3]/div[1]/p/a[1]/text()'
        self.comment_xpath[
            'user_url'] = './div/div/div[1]/div/div[1]/div/div[3]/div[1]/p/a[1]/@href'
        self.comment_url_xpath = '//*[@id="ct"]/div[3]/a/@href'

        self.user_xpath = dict()
        self.user_xpath[
            'registration_date'] = './/dt[text()="Registration date"]/following::dd[1]/text()'
        self.user_xpath['gender'] = './/dt[text()="Gender"]/following::dd[1]/text()'
        self.user_xpath['interests'] = './/dt[text()="Interests"]/following::dd[1]/text()'
        self.user_xpath['instagram'] = './/dt[text()="Instagram"]/following::dd[1]/text()'
        self.user_xpath['user_name'] = ".//dt[text()='Nickname']/following::dd[1]/text()"
        self.user_xpath[
            'last_login_time'] = ".//dt[text()='Last visit time']/following::dd[1]/text()"
        self.user_xpath['real_name'] = ".//dt[text()='Real Name']/following::dd[1]/text()"
        self.user_xpath[
            'education_degree'] = ".//dt[text()='Education degree']/following::dd[1]/text()"
        self.user_xpath['facebook'] = ".//dt[text()='FB profile']/following::dd[1]/text()"
        self.user_xpath['region'] = ".//dt[text()='Living city']/following::dd[1]/text()"
        self.user_xpath[
            'user_group'] = '//*[@id="wp"]/div/div/div[2]/div/div/div[1]/div[2]/p/span/a/text()'
        self.user_xpath[
            'user_level'] = '//*[@id="wp"]/div/div/div[2]/div/div/div[1]/div[2]/a/img/@class'
        self.user_xpath[
            'follower_num'] = '//*[@class="post-stat cl"]/li[1]/p[2]/a/text()'
        self.user_xpath['post_num'] = '//*[@class="post-stat cl"]/li[2]/p[2]/a/text()'
        self.user_xpath[
            'user_comment_num'] = '//*[@class="post-stat cl"]/li[3]/p[2]/a/text()'
        self.user_xpath['points'] = '//*[@class="post-stat cl"]/li[4]/p[2]/a/text()'

    def parse(self, response):
        """
        解析列表页数据以及构造帖子页和下一列表页请求
        """
        text = json.loads(response.text)
        datas = text["data"]
        if datas:
            post_list_url = "http://c.mi.com/ajax.php?page=" + str(
                int(re.search(r"page=(\d+)", response.url).group(1)) + 1) + "&perpage=10"
            yield response.follow(post_list_url, callback=self.parse)
            for data in datas:
                post_url = data['link']
                yield response.follow(post_url, callback=self.parse_post)

    def parse_post(self, response):
        """
        解析帖子页数据以及构造用户页和评论页请求
        """
        post = DataLoader(item=dict(), response=response)
        for field, xpath in self.post_xpath.items():
            post.add_xpath(field, xpath)
        post.add_value("content_url", response.url)
        post = post.load_item()
        yield self.padding_item(post, -1)

        user_url = response.xpath(self.post_xpath['user_url']).extract_first()
        if user_url:
            yield response.follow(user_url, callback=self.parse_user)

        comments = response.xpath(self.comment_list_xpath)
        if comments:
            for comment_data in comments:
                comment = DataLoader(item=dict(), selector=comment_data)
                for field, xpath in self.comment_xpath.items():
                    comment.add_xpath(field, xpath)
                comment.add_value("content_url", response.url)
                comment = comment.load_item()
                try:
                    yield self.padding_item(comment, post['content_id'])
                except AttributeError as error:
                    logging.info(error)

                user_url = comment_data.xpath(self.comment_xpath['user_url']).extract_first()
                if user_url:
                    yield response.follow(user_url, callback=self.parse_user)

            comment_url = response.xpath(self.comment_url_xpath).extract_first()
            if comment_url:
                yield response.follow(comment_url, callback=self.parse_comment,
                                      meta={'post_id': post['content_id']})

    def parse_user(self, response):
        """
        解析用户页数据
        """
        user = DataLoader(item=dict(), response=response)
        for field, xpath in self.user_xpath.items():
            user.add_xpath(field, xpath)
        user.add_value("user_url", response.url)
        user = user.load_item()
        yield self.padding_item(user, None)

    def parse_comment(self, response):
        """
        解析评论页数据以及构造下一评论页请求
        """
        comments = response.xpath(self.comment_list_xpath)
        if comments:
            for comment_data in comments:
                comment = DataLoader(item=dict(), selector=comment_data)
                for field, xpath in self.comment_xpath.items():
                    comment.add_xpath(field, xpath)
                comment = comment.load_item()
                try:
                    yield self.padding_item(comment, response.meta['post_id'])
                except AttributeError as error:
                    logging.info(error)

                user_url = comment_data.xpath(self.comment_xpath['user_url']).extract_first()
                if user_url:
                    yield response.follow(user_url, callback=self.parse_user)

            comment_url = response.xpath(self.comment_url_xpath).extract_first()
            if comment_url:
                yield response.follow(
                    comment_url,
                    callback=self.parse_comment,
                    meta={'post_id': response.meta['post_id']}
                )
