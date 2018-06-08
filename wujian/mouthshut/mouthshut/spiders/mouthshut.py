"""
解析数据和爬虫逻辑模块
"""
import re
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider
from ..itemloader import DataLoader


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'mouthshut'
    allowed_domains = ['mouthshut.com']
    start_urls = ['https://www.mouthshut.com/mobile-phones']

    def __init__(self, name=None, **kwargs):
        """
        完成解析前的初始化工作,主要是将用的到 xpath 配合完成
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        """
        super().__init__(name, **kwargs)

        self.website_id = 'mouthshut'
        self.website_type = 'e-commerce'

        self.model_list_xpath = '//*[@id="categorierightpanel"]/div/div[3]/div[1]/div[@class="box product"]'
        self.model_url = './div[2]/div[1]/a/@href'
        self.model_name = './div[2]/div[1]/a/text()'
        self.model_list_url_xpath = '//*[@id="categorierightpanel"]/div/div[3]/div[2]/div/ul/li[@class="next"]//@href'

        self.model_xpath = dict()
        self.model_xpath['model_name'] = '//*[@id="prodTitle1"]/a/text()'
        self.model_xpath[
            'recommend_rate'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_customheader_dvRecBy"]/div[2]/text()'
        self.model_xpath[
            'model_score'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_customheader_dvRecBy"]/div[3]/span/text()'
        self.model_xpath[
            'model_comment_num'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_customheader_lnkrevcnt"]/text()'
        self.model_xpath[
            'price'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_customheader_lblPrice"]/text()'
        self.model_xpath['brand'] = '//*[@id="prodTitle1"]/a/text()'

        self.item_list_xpath = '//*[@id="dvreview-listing"]/div[@class="row review-article"]'
        self.item_url = './div/div[2]/strong/a/@href'
        self.item_comment_num = './div/div[2]/div[3]/div[2]/div[2]/a/span[2]/text()'
        self.item_thumb_up_num = './div/div[2]/div[3]/div[2]/div[1]/div[2]/a/text()'
        self.item_list_url_xpath = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_litPages"]/ul/li[@class="next"]//@href'
        self.item_xpath = dict()
        self.item_xpath[
            'user_url'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_linkrevname"]/a/@href'
        self.item_xpath[
            'user_name'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_linkrevname"]/a/text()'
        self.item_xpath[
            'user_group'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_imgBadge"]/@title'
        self.item_xpath[
            'user_level'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_lnkRevName"]/span/img'
        self.item_xpath[
            'region'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_spncity"]/text()'
        self.item_xpath['user_comment_num'] = '//*[@id="firstReview"]/div/div[1]/p[3]/a/text()'
        self.item_xpath['follower_num'] = '//*[@id="firstReview"]/div/div[1]/p[4]/a/text()'
        self.item_xpath['title'] = '//*[@id="firstReview"]/div/div[2]/div[2]/p[1]/strong/text()'
        self.item_xpath[
            'main_body_score'] = '//*[@id="ctl00_ctl00_ContentPlaceHolderFooter_ContentPlaceHolderBody_litMemRating"]/span'
        self.item_xpath['time'] = '//*[@id="firstReview"]/div/div[2]/div[2]/div[1]/small[1]/text()'
        self.item_xpath[
            'view_num'] = '//*[@id="firstReview"]/div/div[2]/div[2]/div[1]/small[2]/span[2]/text()'
        self.item_xpath[
            'main_body'] = '//*[@id="firstReview"]/div/div[2]/div[2]/p[position() > 1]//text()'

        self.reply_list_xpath = '//div[@class="row table corp-response"]'
        self.reply_xpath = dict()
        self.reply_xpath['user_url'] = './div[2]/p[2]/span[1]/a/@href'
        self.reply_xpath['user_name'] = './div[2]/p[2]/span[1]/a/text()'
        self.reply_xpath['main_body'] = './div[2]/p[1]/text()'
        self.reply_xpath['time'] = './div[2]/p[2]/span[2]/text()'

    def parse(self, response):
        """
        解析列表页数据以及构造手机首页和下一列表页请求
        """
        for model in response.xpath(self.model_list_xpath):
            model_url = model.xpath(self.model_url).extract_first()
            model_name = model.xpath(self.model_name).extract_first()
            if model_url and not "GB" in model_name:
                yield response.follow(
                    model_url + "-sort-MsDate-order-d",
                    callback=self.parse_model,
                    meta={
                        'splash': {
                            'endpoint': 'render.html',
                            'args': {
                                'wait': 5,
                                'image': 0
                            }
                        },
                        "url": model_url
                    }
                )

        modle_list_url = response.xpath(self.model_list_url_xpath).extract_first()
        if modle_list_url:
            yield response.follow(modle_list_url, callback=self.parse)

    def parse_model(self, response):
        """
        解析手机页数据以及构造详细评价页和下一页评价页请求
        """
        model = DataLoader(item=dict(), response=response)
        for field, xpath in self.model_xpath.items():
            model.add_xpath(field, xpath)
        model.add_value('model_url', response.meta["url"])
        model = model.load_item()
        yield self.padding_item(model, None)

        for selector in response.xpath(self.item_list_xpath):
            item_url = selector.xpath(self.item_url).extract_first()
            item_main_body_comment_num = selector.xpath(self.item_comment_num).extract_first()
            item_thumb_up_num = selector.xpath(self.item_thumb_up_num).extract_first()
            item_main_body_comment_num = re.search(r'\d+', item_main_body_comment_num).group(0)
            if item_url and item_main_body_comment_num != '0':
                yield response.follow(
                    item_url,
                    callback=self.parse_content,
                    meta={
                        'url': item_url,
                        'model_id': model['model_id'],
                        "thumb_up_num": item_thumb_up_num,
                        "main_body_comment_num": item_main_body_comment_num,
                        'splash': {
                            'endpoint': 'render.html',
                            'args': {
                                'wait': 5,
                                'image': 0
                            }
                        }
                    }
                )
            else:
                yield response.follow(
                    item_url,
                    callback=self.parse_content,
                    meta={
                        'url': item_url,
                        'model_id': model['model_id'],
                        "thumb_up_num": item_thumb_up_num,
                        "main_body_comment_num": item_main_body_comment_num
                    }
                )

        item_list_url = response.xpath(self.item_list_url_xpath).extract_first()
        if item_list_url:
            yield response.follow(
                item_list_url,
                callback=self.parse_content_list,
                meta={
                    'model_id': model['model_id'],
                    'splash': {
                        'endpoint': 'render.html',
                        'args': {
                            'wait': 5,
                            'image': 0
                        }
                    }
                }
            )

    def parse_content_list(self, response):
        """
        解析评价页数据以及构造详细评价页和下一页评价页请求
        """
        for selector in response.xpath(self.item_list_xpath):
            item_url = selector.xpath(self.item_url).extract_first()
            item_main_body_comment_num = selector.xpath(self.item_comment_num).extract_first()
            item_thumb_up_num = selector.xpath(self.item_thumb_up_num).extract_first()
            item_main_body_comment_num = re.search(r'\d+', item_main_body_comment_num).group(0)
            if item_url and item_main_body_comment_num != '0':
                yield response.follow(
                    item_url,
                    callback=self.parse_content,
                    meta={
                        'url': item_url,
                        'model_id': response.meta["model_id"],
                        "thumb_up_num": item_thumb_up_num,
                        "main_body_comment_num": item_main_body_comment_num,
                        'splash': {
                            'endpoint': 'render.html',
                            'args': {
                                'wait': 5,
                                'image': 0
                            }
                        }
                    }
                )
            else:
                yield response.follow(
                    item_url,
                    callback=self.parse_content,
                    meta={
                        'url': item_url,
                        'model_id': response.meta["model_id"],
                        "thumb_up_num": item_thumb_up_num,
                        "main_body_comment_num": item_main_body_comment_num
                    }
                )
        item_list_url = response.xpath(self.item_list_url_xpath).extract_first()
        if item_list_url:
            yield response.follow(
                item_list_url,
                callback=self.parse_content_list,
                meta={
                    'model_id': response.meta["model_id"],
                    'splash': {
                        'endpoint': 'render.html',
                        'args': {
                            'wait': 5,
                            'image': 0
                        }
                    }
                }
            )

    def parse_content(self, response):
        """
        解析详细评价页数据
        """
        item = DataLoader(item=dict(), response=response)
        for field, xpath in self.item_xpath.items():
            item.add_xpath(field, xpath)
        item.add_value('thumb_up_num', response.meta['thumb_up_num'])
        item.add_value('content_comment_num', response.meta['main_body_comment_num'])
        item.add_value('content_url', response.meta["url"])
        item = item.load_item()
        yield self.padding_item(item, response.meta['model_id'])

        for selector in response.xpath(self.reply_list_xpath):
            reply = DataLoader(item=dict(), selector=selector)
            for field, xpath in self.reply_xpath.items():
                reply.add_xpath(field, xpath)
            reply.add_value('content_url', response.meta["url"])
            reply = reply.load_item()
            yield self.padding_item(reply, item['content_id'])
