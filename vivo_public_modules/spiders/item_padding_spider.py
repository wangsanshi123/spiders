# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.04.17
版本: 1.0
出于数据库的要求需要,我们每条记录都需要填充或者计算一些字段
需要填充的有: website_id, website_type, crawl_time等
需要计算的有: model_id, user_id, content_id, refer_id等
由于这是所有爬虫都会涉及的操作,我这里写一个爬虫基类完成完成这个操作
'''
import hashlib
import datetime
import inspect

from scrapy import Item
from scrapy import Spider

class ItemPaddingSpider(Spider):
    '''
    完成 item 填充的 spider 基类,重点在于统一的写到这里
    避免每个项目成员自己写一套
    '''

    def __init__(self, name=None, **kwargs):
        '''
        生成 *_id 字段的计算需要哪些域的支持,在初始化中明确
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return None
        '''
        super(ItemPaddingSpider, self).__init__(name, **kwargs)
        self.id_field_list = dict()
        # 列表当中元素的顺序非常重要,不同的顺序会形成不同的字符串,导致无法作为去重的依据
        # model_id 依赖当中 website_id, model_name 为必填项, 假如不足以区分两款机型
        # 则需要 提供 ram, rom 字段, 不需要 ram, rom 的 item 不包含 ram, rom 字段
        # 或者将 ram, rom 字段置为 '' 空字符串即可.
        self.id_field_list['model_id'] = ['website_id', 'model_name', 'ram', 'rom']
        # user_id 依赖当中 website_id, user_name 为必填项, 假如不足以区分两款机型
        self.id_field_list['user_id'] = ['website_id', 'user_name']
        # content_id 依赖当中 website_id, main_body为必填项, user_name, date, time 需要看采集的网站是否支持
        # 假如提供了时间信息,则 date, time 二选一, 类型分别为 datetime.datetime 和 datetime.date
        self.id_field_list['content_id'] = ['website_id', 'main_body', 'user_name', 'date', 'time']

        # website_id, website_type 需要子类去完善
        self.website_id = None
        self.website_type = None

    def padding_item(self, item, refer_id):
        '''
        完成字段填充工作,避免每个人都要在自己的爬虫当中去设置
        :param self: 对象自身
        :param item: 待填充的 item, 可以是 dict 的子类, 也可以是 scrapy.Item的子类
                        能够直接通过赋值添加字段, scrapy.Item 则需要先添加相应的 Field 不能作为参数传进来
        :param refer_id: refer_id 本身和当前 item 并无关系,它代表当前 item 所依赖的内容
        :return: 填充完整的 item
        :raise: AttributeError 来表达 website_type, website_id, user_name 等必要字段的缺失
        '''
        # scrapy.Item 的实例创建新的字段实在是太麻烦
        # 检测到 item 是 Item 子类就将 item 转化为 dict 对象
        if Item in inspect.getmro(item.__class__):
            item = {field: item[field] for field in item}
        if not self.website_id or not self.website_type:
            raise AttributeError('Error: spider object do not have necessary attributes.')
        # 所有记录都需要填写的字段
        item['refer_id'] = refer_id
        item['crawl_time'] = datetime.datetime.now()
        item['website_type'] = self.website_type
        item['website_id'] = self.website_id

        # 检测 item 是否包含 一些必备的字段
        # item 满足最低条件: 三者当中有一个字段认为至少能够插入一条信息
        # 因为 model info 最初录入的时候可能并不存在 content, user
        # 因为 user info 最初录入的时候可能并不存在 content, model
        # 因为 content info 最初录入的时候可能并不存在 user, model
        # 所以 数据是否有效并不是很好检测,需要成员提高警惕,避免数据漏传
        meet_id_condition = False
        for field in item:
            if field in ['main_body', 'user_name', 'model_name']:
                meet_id_condition = True
                break
        # 假如 item 并不包含上述 三个必备字段,则没有存储入库的必要
        # 这时打印错误,并将 None 返回
        if not meet_id_condition:
            raise AttributeError('Error: item does not have necessary field of database.')

        for id_field in self.id_field_list:
            # 生成 model_id, user_id, content_id
            valid_field_num = 0
            id_component = ''
            for field in self.id_field_list[id_field]:
                if field in item:
                    valid_field_num += 1
                    id_component += str(item[field])
            # website_id + model_name
            # website_id + user_name
            # website_id + main_body
            # 至少两个有效字段的 hash 值才能作为 *_id 字段值
            if valid_field_num > 1:
                item[id_field] = hashlib.md5(id_component.encode('utf8')).hexdigest()
        return item

    def parse(self, response):
        '''
        完成响应的数据解析
        :param self: 类的对象本身
        :param response: Scrapy 框架返回的响应
        :return: item
        :raise: NotImplementedError 本类别作为抽象类使用,并不实例化
        '''
        raise NotImplementedError
