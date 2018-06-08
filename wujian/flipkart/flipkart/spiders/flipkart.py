"""
解析数据和爬虫逻辑模块
"""
import json
from datetime import datetime
import logging
import re
from scrapy import Request
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class MySpider(ItemPaddingSpider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'flipkart'
    allowed_domains = ['flipkart.com']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.website_id = 'flipkart'
        self.website_type = 'e-commerce'

        self.url = 'https://www.flipkart.com/api/2/product/smart-browse'
        self.header = {
            'x-user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0 FKUA/website/41/website/Desktop",
        }
        self.params = {
            "requestContext": {
                "store": "tyy/4io",
                "start": 0,
                "disableProductData": True,
                "count": 40,
                "filters": [
                    "facets.brand%5B%5D=Mi",
                    # "facets.brand%5B%5D=Lenovo",
                    # "facets.brand%5B%5D=Apple",
                    # "facets.brand%5B%5D=Samsung",
                    # "facets.brand%5B%5D=OPPO",
                    # "facets.brand%5B%5D=Motorola",
                    # "facets.brand%5B%5D=VIVO",
                    "sort=recency_desc"
                ],
                "ssid": "xekfkzplq8wskckw1510295006069",
                "sqid": "ne5v9g95xscc408c1510295021539"
            }
        }
        self.mobile_names = set()

    def start_requests(self):
        """
        填写post需要的字段信息，filters字段可以过滤手机品牌
        :return:
        """
        yield Request(
            self.url,
            method='POST',
            headers=self.header,
            body=json.dumps(self.params),
            callback=self.parse
        )

    def parse(self, response):
        """
        解析列表页数据以及构造手机首页和下一列表页请求
        """
        text = json.loads(response.text)

        datas = text['RESPONSE']['pageContext']['searchMetaData']['storeSearchResult']['tyy/4io'][
            'productList']
        if datas:
            for data in datas[0:24]:
                params = {
                    "requestContext": {
                        "productId": data,
                        "aspectId": "overall",
                        "sortOrder": "MOST_RECENT",
                        "start": 0,
                        "count": 10,
                    }
                }
                yield Request(
                    'https://www.flipkart.com/api/3/page/dynamic/product-reviews',
                    method='POST',
                    headers=self.header,
                    body=json.dumps(params),
                    callback=self.parse_model,
                    meta={
                        'productId': data,
                        'start': 0
                    }
                )

        params = text['REQUEST']['params']['requestBody']
        params = json.loads(params)
        if params['requestContext']['start'] < text['RESPONSE']['pageContext']['searchMetaData']['metadata']['totalProduct']:
            params['requestContext']['start'] += 24
            yield Request(
                self.url,
                method='POST',
                headers=self.header,
                body=json.dumps(params),
                callback=self.parse
            )

    def parse_model(self, response):
        """
        解析手机首页数据以及构造评价页请求
        """
        text = json.loads(response.text)
        try:
            mobile = text['RESPONSE']['data']['product_summary_review_page_1']['data'][0]
            _ = mobile['value']['title'].split('(', 1)
            if len(_) != 1 and re.search(r'(\d+ [MG]B)\)', _[1]):
                title = _[0] + re.search(r'(\d+ [MG]B)\)', _[1]).group(1)
            else:
                title = _[0].strip()

            try:
                sub_title = mobile['value']['subTitle']
            except KeyError:
                mobile_name = title
            else:
                mobile_name = title + ' ' + sub_title

            if mobile_name not in self.mobile_names:
                self.mobile_names.add(mobile_name)
                model = dict()
                model['model_url'] = "https://www.flipkart.com" + mobile['action']['url']
                model['model_name'] = mobile_name
                if mobile['value'].get('rating'):
                    model['model_score'] = mobile['value']['rating']['average']
                    model['score_num'] = mobile['value']['rating']['count']
                model['price'] = mobile['value']['pricing']['finalPrice']['value']
                if mobile['value'].get('reviewCount'):
                    model['model_comment_num'] = mobile['value']['reviewCount']
                yield self.padding_item(model, None)

                for data in text['RESPONSE']['data']['product_review_page_default_1']['data']:
                    comment = dict()
                    comment['content_url'] = "https://www.flipkart.com/reviews/%s" % (
                        data['value']['downvote']['action']['params']['reviewId'])
                    comment['user_name'] = data['value']['author']
                    comment['user_level'] = 1 if data['value']['certifiedBuyer'] else 0
                    comment['date'] = datetime.strptime(data['value']['created'],
                                                        '%d %b, %Y').strftime('%Y-%m-%d %H:%M:%S')
                    comment['main_body'] = data['value']['text']
                    comment['title'] = data['value']['title']
                    comment['main_body_score'] = data['value']['rating']
                    comment['thumb_up_num'] = data['value']['upvote']['value']['count']
                    comment['thumb_down_num'] = data['value']['downvote']['value']['count']
                    yield self.padding_item(comment, model['model_id'])

                response.meta['start'] += 10
                yield Request(
                    'https://www.flipkart.com/api/3/product/reviews?productId=%s&start=%s&count=10' % (
                        response.meta['productId'], response.meta['start']),
                    headers=self.header,
                    callback=self.parse_content,
                    meta={
                        'productId': response.meta['productId'],
                        'start': response.meta['start'],
                        'model_id': model['model_id']
                    }
                )
        except TypeError as error:
            logging.info(error)

    def parse_content(self, response):
        """
        解析评价页数据以及构造下一评价页请求
        """
        text = json.loads(response.text)
        try:
            for data in text['RESPONSE']['data']:
                comment = dict()
                comment['content_url'] = "https://www.flipkart.com/reviews/%s" % (
                    data['value']['downvote']['action']['params']['reviewId'])
                comment['user_name'] = data['value']['author']
                comment['user_level'] = data['value']['certifiedBuyer']
                comment['date'] = datetime.strptime(data['value']['created'],
                                                    '%d %b, %Y').strftime('%Y-%m-%d %H:%M:%S')
                comment['main_body'] = data['value']['text']
                comment['title'] = data['value']['title']
                comment['main_body_score'] = data['value']['rating']
                comment['thumb_up_num'] = data['value']['upvote']['value']['count']
                comment['thumb_down_num'] = data['value']['downvote']['value']['count']
                yield self.padding_item(
                    comment,
                    response.meta['model_id']
                )

            response.meta['start'] += 10
            yield Request(
                'https://www.flipkart.com/api/3/product/reviews?productId=%s&start=%s&count=10' % (
                    response.meta['productId'], response.meta['start']),
                headers=self.header,
                callback=self.parse_content,
                meta={
                    'productId': response.meta['productId'],
                    'start': response.meta['start'],
                    'model_id': response.meta['model_id']
                }
            )
        except TypeError as error:
            logging.info(error)
