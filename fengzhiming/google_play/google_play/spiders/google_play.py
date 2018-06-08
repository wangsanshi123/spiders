# -*- coding: utf-8 -*-
"""google play 爬虫"""
import re
from scrapy.http import Request
from scrapy.http import FormRequest
from .match_spider import MatchDictSpier


class GooglePlay(MatchDictSpier):
    """google_play 爬虫类"""
    name = 'google_play'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        self.website_id = "google_play"
        self.website_type = 'e-commerce'

        self.match_dict = {
            'g_play_comment': {
                'request': self.request_g_play_comment,
                'parse': self.parse_g_play_comment,
                'save': self.padding_item,
            }
        }

    def start_requests(self):
        # app评论页url
        url = 'https://play.google.com/_/PlayStoreUi/data'
        form_data = {
            'f.req': '[[[136880256,[{"136880256":[null,null,[2,2,[40,null]],["com.facebook.katana",7]]}],null,null,0]]]',
        }
        meta = {'url_type': 'g_play_comment'}
        yield FormRequest(url, formdata=form_data, meta=meta, callback=self.parse)

    def parse_g_play_comment(self, response):
        """解析评论页数据"""
        data = {'data': [], 'new_request': []}

        comment_list_re = re.compile(
            r',(\d),null,"(.*?)",\[(\d+?),\d+?\]\n,(\d*?),null,null,\["\d*?","(.*?)",.*\n')

        f_req_re = re.compile(r'\]\n,\["(.*?)"\]\n\]\n\}\]')

        for comment in comment_list_re.findall(response.text):
            temp_dict = dict()
            temp_dict['app_score'] = comment[0]
            temp_dict['main_body'] = comment[1]
            # 时间戳
            temp_dict['time'] = comment[2]
            temp_dict['thumb_up_num'] = comment[3]
            temp_dict['user_name'] = comment[4]
            temp_dict['content_url'] = response.url
            temp_dict['next_url_request'] = None
            data['data'].append(temp_dict)

        f_req = f_req_re.findall(response.text)
        if f_req:
            print(f_req)
            f_req = f_req[0]
            new_request = {'url_type': 'g_play_comment', 'url': '', 'params': {'f_req': f_req}}
            data['new_request'].append(new_request)
        else:
            with open('fb.html', 'wb') as f:
                f.write(response.body)
        return data

    def request_g_play_comment(self, new_request):
        """发送评论页post请求"""
        url = 'https://play.google.com/_/PlayStoreUi/data'
        f_req = new_request['params']['f_req'] + r'\u003d'
        f_req = '[[[136880256,[{"136880256":[null,null,[2,2,[40,"%s="]],["com.facebook.katana",7]]}],null,null,0]]]' % f_req
        form_data = {
            'f.req': f_req
        }
        meta = {'url_type': 'g_play_comment'}
        return FormRequest(url, formdata=form_data, callback=self.parse, meta=meta)
