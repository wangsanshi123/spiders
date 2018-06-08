"""
解析数据和爬虫逻辑模块
"""
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider
from ..itemloader import DataLoader


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'the_mobile_indian'
    allowed_domains = ['themobileindian.com']
    start_urls = ['https://www.themobileindian.com/reviews/mobile/']

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        """
        super().__init__(name, **kwargs)

        self.website_id = 'the_mobile_indian'
        self.website_type = 'news'

        self.post_list_xpath = '//*[@id="middle"]/div/ul/li[1]/section/ul/li'
        self.post_url_xpath = './h3/a/@href'
        self.post_list_url_xpath = '//*[@id="middle"]/div/ul/li[1]/section/div[3]/ul/li//*[text()="»"]/@href'
        self.post_xpath = dict()
        self.post_xpath['title'] = '//*[@id="middle"]/div/ul/li[1]/section[1]/h1/text()'
        self.post_xpath[
            'user_name'] = '//*[@id="middle"]/div/ul/li[1]/section[1]/div[1]/ul/li/div/p[1]/a/text()'
        self.post_xpath[
            'time'] = '//*[@id="middle"]/div/ul/li[1]/section[1]/div[1]/ul/li/div/p[2]/text()'
        self.post_xpath[
            'main_body'] = '//*[@id="middle"]/div/ul/li[1]/section[1]/p/descendant-or-self::*/text()'

    def parse(self, response):
        """
        解析列表页数据以及构造帖子页和下一列表页请求
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
        post.add_value("content_url", response.url)
        post = post.load_item()
        yield self.padding_item(post, -1)
