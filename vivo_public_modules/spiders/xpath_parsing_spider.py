# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.05.16
版本: 1.0
希望能够将爬虫类的xpath解析工作更加规范
网站逻辑与代码的耦合度能够降低
希望相同的parse函数,不同的 解析模板传递进来,就能够完成解析
限制条件: 目前解析只支持add_path, add_css, add_value
    所以假如你re + xpath的方式完成数据解析,你依然可以将xpath部分的解析使用该类实现

该解析类的使用主要需要完成网页xpath解析配置文件的撰写
<?xml version="1.0"?>
<config>
    # page_type列表页或者是详情页,具体叫什么名字可以自己定
    # 你需要在 request.meta['page_type']当中明确出来
    # 这样解析函数就会知道response是什么类型的页面,使用哪个模板进行解析
    <parse page_type='list'>
        # list_item 标签对应网页当中的列表项内容,比如说新闻列表、评论列表
        # 一类页面当中可以有多个 list_item 所以 list_item 的'name'属性就很重要,明确列表页的内容
        # 其中item_class, itemloader_class 作为可选项
        # 程序在不传递以上两个参数的时候会使用默认的 item itemloader
        # 假如要传递则需要将 item itemloader 写入 vivo_public_modules.vivo_items,
        # vivo_public_modules.vivo_itemloaders 模块当中
        # type必填:css, value, xpath三选一
        # path必填:定位到列表的xpath
        <list_item name='content_abs' item_class='BHuaweiFeedbackPartOne' itemloader_class='BHuaweiFeedbackPartOneLoader' type='xpath' path='//div[@class="thdpp-cont"]'>
            # 列表元素当中需要解析的元素的名称,类型,路径
            # 注意其中路径是相对于列表路径的
            <field name='title' type='xpath' path='.//a[@class="s xst"]/text()'></field>
            <field name='detail_url' type='value' path='http://club.huawei.com/'></field>
            <field name='detail_url' type='xpath' path='.//a[@class="s xst"]/attribute::href'></field>
            <field name='view_count' type='xpath' path='.//span[@class="thd-ico thd-view"]/text()'></field>
            <field name='view_count' type='value' path='-1'></field>
        </list_item>
        # single_item 表示页面当中哪些非列表元素,比如说 网页当中 当天的日期,当天的天气等信息只有一个
        # 页面中非列表元素的解析可以放置到 single_item 标签下
        # single_item 一类网页仅需一个
        <single_item item_class='BHuaweiFeedbackTest' itemloader_class='BHuaweiFeedbackTestLoader'>
            <field name='status' type='xpath' path='//div[@class="thdpp-sub"]/text()'></field>
        </single_item>
    </parse>
    # 一个网站会有几类不同的页面其中 list->item的形式是最多的
    <parse page_type='item'>
        <single_item item_class='BHuaweiFeedbackPartTwo' itemloader_class='BHuaweiFeedbackPartTwoLoader'>
            <field name='content' type='xpath' path='//td[@class="t_f"]/text()'></field>
            <field name='upvote' type='xpath' path='//span[@id="recommendv_add"]/text()'>-1</field>
            <field name='upvote' type='value' path='-1'></field>
        </single_item>
    </parse>
</config>
'''
import xml.etree.ElementTree as ET

import scrapy
from scrapy import Field
from scrapy import Item
from scrapy.exceptions import NotConfigured

from vivo_public_modules import vivo_items
from vivo_public_modules import vivo_itemloaders
from vivo_public_modules.vivo_itemloaders import VivoItemLoader


class XpathParsingSpider(scrapy.Spider):
    '''
    完成网站解析配置文件的加载以及和解析逻辑
    使用该类需要提供的信息
    xpath_config_file,见模块注释
    自定义Item, ItemLoader可提供可不提供
    '''
    def __init__(self, name=None, **kwargs):
        '''
        解析配置文件,并将解析得到的xpath信息放置到self.xpath_config
        :param self: 类的对象自身
        :param name: scrapy 会将 name 属性传递进来
        :param kwargs: 字典形式的参数,用于更新 self.__dict__
        :return: None
        :raise: NotConfigured
        '''
        super(XpathParsingSpider, self).__init__(name, **kwargs)
        xpath_config_file = kwargs['xpath_config']
        if not xpath_config_file:
            raise NotConfigured
        # init self.xpath_config
        self.xpath_config = self.parse_xpath_config(xpath_config_file)

    @classmethod
    def from_crawler(cls, crawler):
        '''
        想要在spider类的__init__方法中访问settings需要实现from_crawler方法
        主要任务是完成XPATH_CONFIG变量的读取工作
        :param cls: 类自身
        :param crawler: crawler实例
        :return: 爬虫类的对象
        '''
        return cls(xpath_config=crawler.settings.get('XPATH_CONFIG', None))

    @classmethod
    def _parse_section_config(cls, section_xpath_config):
        '''
        xpath配置文件由一个个小的块组成
        格式就像这样,这种块无论是list还是item都是有的
        <single_item item_class='BHuaweiFeedbackPartTwo' itemloader_class='BHuaweiFeedbackPartTwoLoader'>
            <field name='content' type='xpath' path='//td[@class="t_f"]/text()'></field>
            <field name='upvote' type='xpath' path='//span[@id="recommendv_add"]/text()'>-1</field>
            <field name='upvote' type='value' path='-1'></field>
        </single_item>
        :param cls: 只是简单的完成文件某个部分的解析,并返回解析结果,并不需要使用类实例的信息
        :param section_xpath_config: 某一小块待解析的配置信息
        '''
        # 存储解析之后得到的信息
        result = list()
        # 将定位列表的xpath,列表中每一项对应的item, itemloader信息加载进来
        result.append(
            # item_class, itemloader_class 解析出来
            {key: section_xpath_config.attrib[key] for key in section_xpath_config.attrib}
        )
        # xpath解析出来
        for field in section_xpath_config.findall('field'):
            info = {key: field.attrib[key] for key in field.attrib}
            result.append(info)
        return result

    @classmethod
    def parse_xpath_config(cls, xpath_config_file):
        '''
        重点是完成xpath配置文件的解析工作
        :param xpath_config_file: 网站的xpath解析配置文件,文件的格式请参考本模块的注释
        :return: 返回解析完成的网站的xpath配置信息
        '''
        xpath_config_tree = ET.parse(xpath_config_file)
        xpath_config_tree_root = xpath_config_tree.getroot()
        # 配置文件当中解析得到的信息放置在xpath_config当中
        xpath_config = dict()
        # parse标签范围代表着一类网页的xpath配置信息
        for page_xpath_config in xpath_config_tree_root.findall('parse'):
            page_type = page_xpath_config.attrib['page_type']
            # 存放该page_type的xpath信息
            xpath_config[page_type] = dict()
            xpath_config[page_type]['list'] = dict()
            xpath_config[page_type]['item'] = None
            for list_xpath_config in page_xpath_config.findall('list_item'):
                list_xpath_result = cls._parse_section_config(list_xpath_config)
                # 将配置信息加入到整个xpath配置信息当中
                page_list_name = list_xpath_config.attrib['name']
                xpath_config[page_type]['list'][page_list_name] = list_xpath_result

            # 解析单元素项
            item_xpath_config = page_xpath_config.find('single_item')
            if item_xpath_config:
                item_xpath_result = cls._parse_section_config(item_xpath_config)
                xpath_config[page_type]['item'] = item_xpath_result
        return xpath_config

    @classmethod
    def _parse_section(cls, section_config, selector):
        '''
        内部类方法
        完成item,itemloader的初始化
        并根据给定的xpath信息,selector完成相应的数据解析返回解析得到的数据
        :param cls: 爬虫类
        :param section_config: 某一块的xpath解析模板
        :param selector: 对应网页的某一部分
        :return: 返回解析到的数据
        '''
        # 初始化item
        item_class = Item
        if 'item_class' in section_config[0]:
            item_class = getattr(vivo_items, section_config[0]['item_class'])
        item = item_class()
        # 假如没有配置item_class,则提供默认的item
        if item_class == Item:
            for path in section_config[1:]:
                item.fields[path['name']] = Field()

        # 初始化itemloader
        itemloader_class = VivoItemLoader
        if 'itemloader_class' in section_config[0]:
            itemloader_class = getattr(
                vivo_itemloaders,
                section_config[0]['itemloader_class']
            )
        item_loader = itemloader_class(item, selector)
        # 根据xpath配置信息完成数据解析
        for config in section_config[1:]:
            item_loader.add(config['type'], config['name'], config['path'])
        # 返回解析到的数据
        return item_loader.load_item()

    def parse(self, response):
        '''
        根据response.meta的page_type属性
        选择相应的xpath解析模板完成数据解析
        :param self: 类对象
        :param response: 页面响应
        :return: 返回页面解析得到的数据
        '''
        # 根据 page_type 选择对应类型页面的解析模板
        page_type = response.meta['page_type']
        page_xpath_config = self.xpath_config[page_type]
        # 存放解析得到的结果
        page_data = dict()
        # 列表类的元素
        list_xpath_config = page_xpath_config['list']
        # 页面可能有两个列表
        for list_name in list_xpath_config:
            list_data = list()
            current_config = list_xpath_config[list_name]
            for selector in getattr(response, current_config[0]['type'])(current_config[0]['path']):
                section_data = self._parse_section(current_config, selector)
                list_data.append(section_data)
            page_data[list_name] = list_data

        item_xpath_config = page_xpath_config['item']
        if item_xpath_config:
            page_data['item'] = self._parse_section(item_xpath_config, response)
        return page_data
