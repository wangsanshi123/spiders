"""
解析数据和爬虫逻辑模块
"""
import hashlib
import json
from datetime import datetime
import scrapy
from scrapy.http import Request

PAGE_ID = '1529780750583160'
with open('token.txt') as f:
    TOKEN = f.read()


class MyPostSpider(scrapy.Spider):
    """
    解析数据和爬虫逻辑类
    """
    name = 'facebook'
    allowed_domains = ['facebook.com']

    @staticmethod
    def datetime_processor(value):
        """
        将时间处理成标准格式
        :param value:
        :return:
        """
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S+0000')
        return value.strftime('%Y-%m-%d %H:%M:%S')

    def start_requests(self):
        """
        构造帖子页和评论页请求
        """
        yield Request(
            ('https://graph.facebook.com/v2.12/%s/posts?fields='
             'shares,message,created_time,likes.limit(0).summary(true),'
             'comments.limit(0).summary(true)'
             '&access_token=%s') % (PAGE_ID, TOKEN), callback=self.parse_content
        )
        yield Request(
            ('https://graph.facebook.com/v2.12/%s/posts?fields='
             'comments.limit(1000){created_time,message,comment_count,likes.limit(0).summary(true),'
             'comments.limit(1000){created_time,message,likes.limit(0).summary(true)}}'
             '&access_token=%s') % (PAGE_ID, TOKEN), callback=self.parse_comment
        )

    def parse_content(self, response):
        """
        解析帖子页和构造下一帖子页请求
        """
        text = json.loads(response.text)
        if text.get("paging"):
            datas = text["data"]
            for data in datas:
                post = dict()
                post["content_url"] = "https://www.facebook.com/" + data['id']
                post["time"] = MyPostSpider.datetime_processor(data["created_time"])
                post["main_body"] = data["message"].strip() if data.get("message") else ""
                post["thumb_up_num"] = data["likes"]["summary"]["total_count"]
                post["content_comment_num"] = data["comments"]["summary"]["total_count"]
                post["share_num"] = data["shares"]["count"] if data.get("shares") else 0
                post['refer_id'] = -1
                post_id = data['id']
                post['content_id'] = hashlib.md5(post_id.encode('utf8')).hexdigest()
                yield post
            if "next" in text['paging']:
                yield response.follow(
                    text["paging"]["next"],
                    callback=self.parse_content
                )

    def parse_comment(self, response):
        """
        解析评论页和构造下一评论页请求
        """
        text = json.loads(response.text)
        datas = text["data"]
        for data in datas:
            if data.get("comments"):
                for comment_data in data["comments"]["data"]:
                    comment = dict()
                    comment["content_url"] = "https://www.facebook.com/" + PAGE_ID + "_" + comment_data["id"]
                    comment["time"] = MyPostSpider.datetime_processor(comment_data["created_time"])
                    comment["main_body"] = comment_data["message"]
                    comment["thumb_up_num"] = comment_data["likes"]["summary"]["total_count"]
                    comment["content_comment_num"] = comment_data["comment_count"]
                    comment["refer_id"] = hashlib.md5(data["id"].encode('utf8')).hexdigest()
                    comment_id = comment_data["id"]
                    comment['content_id'] = hashlib.md5(comment_id.encode('utf8')).hexdigest()
                    yield comment
                    if comment_data.get("comments"):
                        for reply_data in comment_data["comments"]["data"]:
                            reply = dict()
                            reply['content_url'] = "https://www.facebook.com/" + PAGE_ID + "_" + reply_data["id"]
                            reply["time"] = MyPostSpider.datetime_processor(
                                reply_data["created_time"])
                            reply["main_body"] = reply_data["message"]
                            reply["thumb_up_num"] = reply_data["likes"]["summary"]["total_count"]
                            reply["refer_id"] = comment['content_id']
                            reply_id = reply_data["id"]
                            reply['content_id'] = hashlib.md5(reply_id.encode('utf8')).hexdigest()
                            yield reply

        if text["paging"].get("next"):
            yield response.follow(
                text["paging"]["next"],
                callback=self.parse_comment
            )
