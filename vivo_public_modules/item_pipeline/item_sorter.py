'''
作者: 郑阔
日期: 2018.04.18
版本: 1.0
爬虫开发者可以将采集解析到的数据统一放入一个 类 dict 结构的 item 当中
其中 item.keys() 必须是我们定义的 mongodb 数据库结构的子集
开发者可以将 user_name、model_name、main_body 放入同一个 item 当中
该模块完成数据库定义的 collection 完成信息分组
item = {
    'user_name': 'jonsnow',
    'model_name': 'vivo X20',
    'main_body': '人生而孤独'
}
转化为
item = {
    'model': {
        'model_name': 'vivo X20',
        ...
    },
    'user': {
        'user_name': 'jonsnow',
        ...
    },
    'content': {
        'main_body': '人生而孤独'
    }
}
将原始的 item 按照字段所属的 collection 进行分组，方便后边的 item_pipeline 进行信息入库
'''
# -*- coding: utf-8 -*-

import os
import json

from scrapy.exceptions import NotConfigured

class ItemSorter(object):
    '''
    爬虫数据完成采集后数据会进行格式化,填充,但依然是一个 item 包含所有的字段
    本类的作用就是将 item 字段按照 model, user, content分开
    '''
    def __init__(self, database_structure_file):
        '''
        主要是从 settings.py 当中读取 数据库结构文件
        :param self: 类的实例对象
        :param database_structure_file: 数据库结构文件
        :return: None
        '''
        self.database_structure = json.load(open(database_structure_file, 'r'))
        self.all_field_list = list()

    @classmethod
    def from_crawler(cls, crawler):
        '''
        主要是从 crawler 当中的 settings 当中获取两个 数据库结构文件的配置信息
        :param cls: 类本身 cls() 相当于调用构造函数 生成类实例
        :param crawler: scrapy 项目运行后的 crawler 实例
        :return: ItemSorter 类对象
        :raise: 假如 settings 文件当中没有找到 相应的配置项就会抛出异常
        '''
        # 项目配置信息所在的路径
        config_dir = crawler.settings.get('CONFIG_DIR', None)
        # 数据库结构所在的文件
        database_structure_file = crawler.settings.get('DATABASE_STRUCTURE', None)
        if not config_dir or not database_structure_file:
            raise NotConfigured
        database_structure_file = os.path.join(config_dir, database_structure_file)
        return cls(database_structure_file)

    def process_item(self, item, spider):
        '''
        将扁平的 item 当中的信息根据数据库结构进行分组
        :param self: 类的对象本身
        :param item: 生成的 item
        :param spider: 传回该 item 的 spider
        :return: 整理好的 item
        '''
        sorted_item = dict()
        for field in item:
            for collection in self.database_structure:
                if field in self.database_structure[collection]:
                    if collection not in sorted_item:
                        sorted_item[collection] = dict()
                    sorted_item[collection][field] = item[field]

        # 针对某些不包含必备字段的数据需要进行删除
        for collection, necessary_field in (
                ['content', 'content_id'],
                ['user', 'user_id'],
                ['model', 'model_id']
        ):
            if necessary_field not in sorted_item[collection]:
                sorted_item.pop(collection)
        return sorted_item
