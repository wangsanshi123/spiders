"""instagram爬虫"""
import re
import json
import hashlib
import urllib.parse
from scrapy.http import Request
from .match_spider import MatchDictSpier


class Instagram(MatchDictSpier):
    """instagram爬虫类"""

    name = "instagram"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        self.website_id = "instagram"
        self.website_type = "social"

        self.match_dict = {
            'ins_user_home': {
                'request': self.simple_new_request,
                'parse': self.ins_user_home_parse,
                'save': self.simple_data_save,
            },
            'ins_ajax_post': {
                'request': self.ins_ajax_post_request,
                'parse': self.ins_ajax_post_parse
            },
            'ins_post_detail': {
                'request': self.simple_new_request,
                'parse': self.ins_post_detail_parse,
                'save': self.simple_data_save
            },
            'ins_ajax_detail': {
                'request': self.ins_ajax_detail_request,
                'parse': self.ins_post_detail_parse,
                'save': self.simple_data_save
            }
        }

    def start_requests(self):
        """发送起始页请求"""
        url = "https://www.instagram.com/vivo/"
        meta = {'url_type': 'ins_user_home'}
        yield Request(url, meta=meta, callback=self.parse)

    def ins_user_home_parse(self, response):
        """解析用户首页， 获取用户信息，动态链接"""
        data = {"data": [], "new_request": []}
        re_dict = dict()
        re_dict['rule_type'] = 're'
        re_dict['edges'] = re.compile(r'"edge_owner_to_timeline_media":.*,'
                                      r'"edges":(\[.*\])},"edge_saved_media"')
        re_dict['user_id'] = re.compile(r'"id":"(\d*?)","is_p')
        re_dict['has_next_page'] = re.compile(r'"has_next_page":(.*?),')
        re_dict['end_cursor'] = re.compile(r'"end_cursor":"(.*?)"')
        re_dict['rhx_gis'] = re.compile(r'"rhx_gis":"(.*?)",')
        re_dict['user_info'] = re.compile(r'<meta content="(.*?) Followers, '
                                          r'(.*?) Following, (.*?) Posts.*"')
        re_dict['user_name'] = re.compile(r'username=(.*?)"')

        temp_dict = self.get_rule_data(re_dict, response.text)
        # 获取用户信息
        data_item = dict()
        data_item['user_name'] = temp_dict['user_name']
        data_item['follower_num'] = temp_dict['user_info'][0]
        data_item['follower_num'] = temp_dict['user_info'][1]
        data_item['post_num'] = temp_dict['user_info'][2]
        data_item['user_url'] = response.url
        data_item['next_url_request'] = None

        data['data'].append(data_item)

        rhx_gis = temp_dict['rhx_gis']
        owner_id = temp_dict['user_id']
        end_cursor = temp_dict['end_cursor']
        edges = json.loads(temp_dict['edges'])

        # 获取帖子详情页链接
        for edge in edges:
            # 判断是否有这个键,防止提取报错
            shortcode = self.get_dict_key(edge, ['node', 'shortcode'])
            new_post_detail_request = {
                'url_type': 'ins_post_detail',
                'url': 'https://www.instagram.com/p/{0}/?__a=1'.format(shortcode),
                'params': {"shortcode": shortcode, "rhx_gis": rhx_gis}
            }
            data['new_request'].append(new_post_detail_request)

        # 判断是否有跟多的帖子页，如果有则获取对应的请求参数
        if temp_dict['has_next_page']:
            url = 'https://www.instagram.com/graphql/query/?query_hash={0}&variables={1}'
            params = {'id': owner_id, 'end_cursor': end_cursor, 'rhx_gis': rhx_gis}
            new_post_list_request = {'url_type': 'ins_ajax_post', 'url': url, 'params': params}
            data['new_request'].append(new_post_list_request)

        return data

    def ins_ajax_post_request(self, new_request):
        """构造帖子页ajax请求"""
        query_hash = '42323d64886122307be10013ad2dcc44'

        url = new_request['url']
        params = new_request['params']

        # 生成接口需要的对应参数
        variables = '{"id": "%s", "first": 12, "after": "%s"}' %\
                    (params['id'], params['end_cursor'])
        values = "%s:%s" % (params['rhx_gis'], variables)
        x_instagram_gis = hashlib.md5(values.encode()).hexdigest()
        # 构造请求url
        encoded_vars = urllib.parse.quote(variables, safe='"')
        url = url.format(query_hash, encoded_vars)
        # 构造ajax请求
        headers = {'x_instagram_gis': x_instagram_gis}
        # 删除end_cursor键，将params 带给下一级请求
        params.pop('end_cursor')
        meta = {'url_type': new_request['url_type'], 'params': params}
        return Request(url, headers=headers, meta=meta, callback=self.parse)

    def ins_ajax_post_parse(self, response):
        """解析ajax请求返回的帖子列表页，获取帖子信息"""
        data = {"data": [], "new_request": []}

        data_dict = json.loads(response.body)

        tier_list = ['data', 'user', 'edge_owner_to_timeline_media']
        edge_media = self.get_dict_key(data_dict, tier_list)
        edges = self.get_dict_key(edge_media, ['edges'])
        has_next_page = self.get_dict_key(edge_media, ['page_info', 'has_next_page'])
        end_cursor = self.get_dict_key(edge_media, ['page_info', 'end_cursor'])
        owner_id = response.meta['params']['id']
        rhx_gis = response.meta['params']['rhx_gis']

        for edge in edges:
            # 判断是否有这个键,防止提取报错
            shortcode = self.get_dict_key(edge, ['node', 'shortcode'])
            new_post_detail_request = {
                'url_type': 'ins_post_detail',
                'url': 'https://www.instagram.com/p/{0}/?__a=1'.format(shortcode),
                'params': {'shortcode': shortcode, 'rhx_gis': rhx_gis}
            }
            data['new_request'].append(new_post_detail_request)

        # 判断是否有更多的帖子页
        if has_next_page:
            url = 'https://www.instagram.com/graphql/query/?query_hash={0}&variables={1}'
            params = {
                'id': owner_id,
                'end_cursor': end_cursor,
                'rhx_gis': response.meta['params']['rhx_gis']
            }
            new_post_list_request = {'url_type': 'ins_ajax_post', 'url': url, 'params': params}
            data['new_request'].append(new_post_list_request)
        return data

    def ins_post_detail_parse(self, response):
        """解析帖子页， 获取评论信息"""
        data = {"data": [], "new_request": []}

        data_dict = json.loads(response.body)
        first_key = list(data_dict.keys())[0]
        tier_list = [first_key, 'shortcode_media', 'edge_media_to_comment']
        edge_media_to_comment = self.get_dict_key(data_dict, tier_list)
        edges = self.get_dict_key(edge_media_to_comment, ['edges'])
        has_next_page = self.get_dict_key(edge_media_to_comment, ['page_info', 'has_next_page'])
        end_cursor = self.get_dict_key(edge_media_to_comment, ['page_info', 'end_cursor'])
        shortcode = response.meta['params']['shortcode']
        rhx_gis = response.meta['params']['rhx_gis']
        # 获取每一条评论信息
        for edge in edges:
            main_body = self.get_dict_key(edge, ["node", "text"])
            user_name = self.get_dict_key(edge, ["node", "owner", "username"])
            item_dict = {
                "main_body": main_body,
                "user_name": user_name,
                "content_url": response.url,
                "next_url_request": None
            }
            data['data'].append(item_dict)

            if user_name != "vivo":
                url = 'https://www.instagram.com/{0}/'.format(user_name)
                new_user_home_request = {'url_type': 'ins_user_home', 'url': url, 'params': None}
                data['new_request'].append(new_user_home_request)

        # 判断是否还有评论页
        if has_next_page:
            url = 'https://www.instagram.com/graphql/query/?query_hash={0}&variables={1}'
            params = {'shortcode': shortcode, 'end_cursor': end_cursor, 'rhx_gis': rhx_gis}
            new_post_detail_request = {'url_type': 'ins_ajax_detail', 'url': url, 'params': params}
            data['new_request'].append(new_post_detail_request)

        return data

    def ins_ajax_detail_request(self, new_request):
        query_hash = '33ba35852cb50da46f5b5e889df7d159'

        url = new_request['url']
        params = new_request['params']

        # 生成接口需要的对应参数
        variables = '{"shortcode": "%s", "first": 12, "after": "%s"}' % \
                    (params['shortcode'], params['end_cursor'])
        values = "%s:%s" % (params['rhx_gis'], variables)
        x_instagram_gis = hashlib.md5(values.encode()).hexdigest()
        # 构造请求url
        encoded_vars = urllib.parse.quote(variables, safe='"')
        url = url.format(query_hash, encoded_vars)
        # 构造ajax请求
        headers = {'x_instagram_gis': x_instagram_gis}
        # 删除end_cursor键，将params 带给下一级请求
        params.pop('end_cursor')
        meta = {'url_type': new_request['url_type'], 'params': params}
        return Request(url, headers=headers, meta=meta, callback=self.parse)
