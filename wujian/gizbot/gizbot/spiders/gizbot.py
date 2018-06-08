"""
解析数据和爬虫逻辑模块
"""
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider
from ..itemloader import DataLoader


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'gizbot'
    allowed_domains = ['gizbot.com']
    start_urls = ['https://www.gizbot.com/mobile/news/']

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        """
        super().__init__(name, **kwargs)

        self.website_id = 'gizbot'
        self.website_type = 'news'

        self.post_list_xpath = '//*[@id="content"]/section/div/div[1]/div/ul/li'
        self.post_url_xpath = './div[1]/a/@href'
        self.post_list_url_xpath = '(//*[@id="content"]/section/div/div[1]/div/ul/div[1]/div)[last()]/a/@href'
        self.post_xpath = dict()
        self.post_xpath[
            "title"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[1]/h1/text()'
        self.post_xpath[
            "abstract"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[1]/div[3]/h2/text()'
        self.post_xpath[
            "time"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[2]/div[2]/span/time/text()'
        self.post_xpath[
            "main_body"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[4]/article/div[1]/p/descendant-or-self::*/text()'
        self.post_xpath[
            "user_name"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[2]/div[1]/div/a/text()'
        self.post_xpath[
            "user_url"] = '//*[@id="container"]/div[1]/div[1]/article/div/section[1]/div/div[2]/div[1]/div/a/@href'

        self.user_xpath = dict()
        self.user_xpath['user_name'] = '//*[@id="content"]/section/div[1]/div/div/div[2]/div[1]/div[2]/table/tbody/tr[1]/td[2]/text()'
        self.user_xpath['region'] = '//*[@id="content"]/section/div[1]/div/div/div[2]/div[1]/div[2]/table/tbody/tr[2]/td[2]/text()'
        self.user_xpath['info'] = '//*[@id="content"]/section/div[1]/div/div/div[2]/div[1]/div[2]/table/tbody/tr[3]/td[2]/text()'


    def parse(self, response):
        """
        解析列表页数据以及构造新闻页和下一列表页请求
        """
        posts = response.xpath(self.post_list_xpath)
        for post in posts:
            post_url = post.xpath(self.post_url_xpath).extract_first()
            if post_url:
                yield response.follow(post_url, callback=self.parse_content)

        post_list_url = response.xpath(self.post_list_url_xpath).extract_first()
        if post_list_url:
            yield response.follow(post_list_url, callback=self.parse)

    def parse_content(self, response):
        """
        解析新闻页数据
        """
        post = DataLoader(item=dict(), response=response)
        for field, xpath in self.post_xpath.items():
            post.add_xpath(field, xpath)
        post.add_value('content_url', response.url)
        post = post.load_item()
        yield self.padding_item(post, -1)

        user_url = response.xpath(self.post_xpath['user_url']).extract_first()
        if user_url:
            yield response.follow(user_url, callback=self.parse_user)

    def parse_user(self, response):
        """
        解析用户页数据
        """
        user = DataLoader(item=dict(), response=response)
        for field, xpath in self.user_xpath.items():
            user.add_xpath(field, xpath)
        user = user.load_item()
        yield self.padding_item(user, None)
