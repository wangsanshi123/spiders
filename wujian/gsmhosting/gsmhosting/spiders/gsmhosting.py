"""
解析数据和爬虫逻辑模块
"""
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider
from ..itemloader import DataLoader


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'gsmhosting'
    allowed_domains = ['forum.gsmhosting.com']
    start_urls = ['http://forum.gsmhosting.com/vbb/f854/']

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        """
        super().__init__(name, **kwargs)

        self.website_id = 'gsmhosting'
        self.website_type = 'complaint'

        self.forum_list_xpath = '/html/body/div/div[1]/div/table[5]/tbody'
        self.forum_url_xpath = './tr/td/table/tr/td[3]/div/a/@href'
        self.post_list_xpath = '//*[@id="threadslist"]/tbody[2]/tr'
        self.post_url_xpath = './td[3]/div/a/@href'
        self.post_list_url_xpath = '//a[@rel="next"]/@href'
        self.post_comment_num = './td[5]/a/text()'
        self.post_view_num = './td[6]/text()'

        self.item_list_path = '//*[@id="posts"]/div'
        self.item_path = dict()
        self.item_path['user_name'] = './/*[@class="bigusername"]//text()'
        self.item_path['user_url'] = './/*[@class="bigusername"]//@href'
        self.item_path['user_group'] = './div/div/div/table/tr[2]/td[1]/div[2]/text()'
        self.item_path['user_name'] = './/*[@class="bigusername"]//text()'
        self.item_path['registration_date'] = './/*[contains(text(),"Join Date")]//text()'
        self.item_path['region'] = './/*[contains(text(),"Location")]//text()'
        self.item_path['age'] = './/*[contains(text(),"Age")]//text()'
        self.item_path['user_comment_num'] = './/*[contains(text(),"Posts")]//text()'
        self.item_path['points'] = './/*[contains(text(),"Thanks Meter")]//text()'
        self.item_path['title'] = './div/div/div/table/tr[2]/td[2]/div[1]/strong/text()'
        self.item_path['time'] = './div/div/div/table/tr[1]/td[1]/text()'
        self.item_path['main_body'] = './div/div/div/table/tr[2]/td[2]/div/text()'
        self.item_path['floor'] = './div/div/div/table/tr[1]/td[2]/a/strong/text()'
        self.item_url = '/html/body/div[3]/div[1]/div/table[1]/tr/td[2]/div/table/tr/td[5]/a/@href'

    def parse(self, response):
        """
        构造帖子页请求
        """
        forums = response.xpath(self.forum_list_xpath)
        for forum in forums:
            forum_url = forum.xpath(self.forum_url_xpath).extract_first()
            if forum_url:
                yield response.follow(forum_url, callback=self.parse_post)

    def parse_post(self, response):
        """
        构造评论页请求
        """
        posts = response.xpath(self.post_list_xpath)
        for post in posts:
            post_url = post.xpath(self.post_url_xpath).extract_first()
            if post_url:
                comment_num = post.xpath(self.post_comment_num).extract_first()
                view_num = post.xpath(self.post_view_num).extract_first()
                yield response.follow(
                    post_url,
                    callback=self.parse_comment,
                    meta={'comment_num': comment_num, 'view_num': view_num}
                )

        post_list_url = response.xpath(self.post_list_url_xpath).extract_first()
        if post_list_url:
            yield response.follow(post_list_url, callback=self.parse_post)

    def parse_comment(self, response):
        """
        解析评论页数据以及构造下一评论页请求
        """
        if response.meta.get('post_id'):
            post_id = response.meta['post_id']
        else:
            post_id = None
        comments = response.xpath(self.item_list_path)
        if comments:
            for comment_data in comments[:-1]:
                item = DataLoader(item=dict(), selector=comment_data)
                for field, xpath in self.item_path.items():
                    item.add_xpath(field, xpath)
                item.add_value("content_url", response.url)
                item = item.load_item()
                if item.get('floor') == '1':
                    item["content_comment_num"] = response.meta['comment_num']
                    item["view_num"] = response.meta['view_num']
                    yield self.padding_item(item, -1)
                    post_id = item['content_id']
                else:
                    yield self.padding_item(item, post_id)

        item_url = response.xpath(self.item_url).extract_first()
        if item_url:
            yield response.follow(
                item_url,
                callback=self.parse_comment,
                meta={'post_id': post_id}
            )
