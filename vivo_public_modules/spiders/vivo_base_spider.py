# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.05.16
版本: 1.0
将 ItemPaddingSpider, XpathParsingSpider, MasterControlSpider
三个类的功能进行合并,这样子类的继承以及函数调用都会简洁一些
'''
import hashlib
import inspect
import datetime
import xml.etree.ElementTree as ET

import scrapy
from scrapy import Request
from scrapy import Field
from scrapy import Item
from scrapy.exceptions import NotConfigured

from vivo_public_modules import vivo_items
from vivo_public_modules import vivo_itemloaders
from vivo_public_modules.vivo_itemloaders import VivoItemLoader


class VivoBaseSpider(scrapy.Spider):
    '''
    提供item补全,Xpath解析,parse->more request->parse主控功能
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
        super(VivoBaseSpider, self).__init__(name, **kwargs)
        xpath_config_file = kwargs['xpath_config']
        if not xpath_config_file:
            raise NotConfigured
        # init self.xpath_config
        self.xpath_config = self.parse_xpath_config(xpath_config_file)
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

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        '''
        想要在spider类的__init__方法中访问settings需要实现from_crawler方法
        主要任务是完成XPATH_CONFIG变量的读取工作
        :param cls: 类自身
        :param crawler: crawler实例
        :return: 爬虫类的对象
        '''
        kwargs['xpath_config'] = crawler.settings.get('XPATH_CONFIG', None)
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    @classmethod
    def _parse_section_config(cls, section_xpath_config):
        '''
        xpath配置文件由一个个小的块组成
        格式就像这样,这种块无论是list还是item都是有的
        <single_item item_class='BHuaweiFeedbackPartTwo' itemloader_class='YourLoader'>
            <field name='content' type='xpath' path='//td[@class="t_f"]/text()'></field>
            <field name='upvote' type='xpath' path='//span[@id="upvote"]/text()'>-1</field>
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
            xpath_config[page_type] = {
                key: page_xpath_config.attrib[key] for key in page_xpath_config.attrib
            }
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

    def parse_by_xpath(self, response):
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

    def more_requests(self, page_data, next_page_type):
        '''
        希望解决需要采集多个页面才能完成完成的数据采集情况
        考虑新闻列表页,投诉列表页的情况
        列表页提供了摘要,需要继续访问详情页获取新闻正文,投诉正文等
        可以将列表页的摘要数据传入详情页请求的mate当中字段名称为'pre_page_data'
        并且可以根据page_data当中数据的类型自动适配列表类或是字典类
        warning: 只支持数据当中仅有一个需要访问的URL情况,字段后缀为'_url'
        举个例子新闻列表页拿到数据进一步访问新闻详情页并附带上列表页的相关数据是可以的
        但是从列表页拿到数据不仅需要进一步访问详情页还需要访问比如说新闻作者简介页面这种情况就不支持
        PageA->PageB->PageC YES
        PageA->PageB and PageA->PageC NO
        :param self: 类的对象自身
        :param page_data: 页面解析得到的数据
        :param next_page_type: 新Request请求的页面类型
        '''
        # 新请求结果列表
        request_list = list()
        for item_name in page_data:
            if not page_data[item_name]:
                continue
            # type() 不考虑继承关系,不认为子类是父类类型
            # isinstance() 相反
            if isinstance(page_data[item_name], list):
                # 明确有数据的前提下拿到其中第一个record
                record = page_data[item_name][0]
                # 确定 新请求的URL,URL字段名称为需要以'_url'结尾
                url_key = self._find_url_key_from_record(record)
                # 针对列表中的每一项,将数据,url,page_type填入请求
                for record in page_data[item_name]:
                    request_list.append(
                        self._generate_request_from_record(
                            url_key, record, next_page_type
                        )
                    )
            elif isinstance(page_data[item_name], dict):
                record = page_data[item_name]
                url_key = self._find_url_key_from_record(record)
                request_list.append(
                    self._generate_request_from_record(
                        url_key, record, next_page_type
                    )
                )
            else:
                continue
        return request_list

    def _find_url_key_from_record(self, record):
        '''
        从字典类型的record当中查找首个'_url'结尾的字段
        并将字段名称返回
        :param record: {'user_name': 'Jon', 'content_url': 'url'}
        :return: 'content_url'
        '''
        url_key = ''
        for key in record:
            if key.endswith('_url'):
                url_key = key
                break
        return url_key

    def _generate_request_from_record(self, url_key, record, new_page_type):
        '''
        使用url, record, page_type生成新的request
        '''
        if url_key not in record:
            return None
        url = record[url_key]
        request = Request(url)
        request.meta['page_data'] = record.copy()
        request.meta['page_type'] = new_page_type
        return request

    def parse(self, response):
        '''
        完成网页的解析,并且在当前网页类型依赖后续页面数据才能达到数据完整性时
        负责生成更多request或是网页不再有后续页面时将数据送入format_data方法
        进行数据格式化
        :param self: 类的实例本身
        :param response: 返回的响应
        '''
        # 页面的数据解析
        page_data = self.parse_by_xpath(response)
        # 当前页面有前置数据
        # 目前假设前置数据为dict类别
        pre_page_data = response.meta.get('page_data', {})
        page_type = response.meta['page_type']
        # 前置数据放入item字段
        if 'item' not in page_data:
            page_data['item'] = dict()
        page_data['item'] = dict(page_data['item'], **pre_page_data)

        next_page_type = self.xpath_config[page_type].get('next_page_type', None)
        # 假如当前页面存在后置页面
        if next_page_type:
            # 继续请求后置页面
            for request in self.more_requests(page_data, next_page_type):
                if not request:
                    continue
                yield request
        else:
            # 根据page_type进行页面数据格式化
            for record in self.format_data(page_data, page_type):
                yield record

    def format_data(self, page_data, page_type):
        '''
        需要根据网站的不同使用不同的格式化方法
        :param self: 类的实例对象
        :param page_data: 页面的数据,包含所有前置页面的数据,前置页面的数据会放到item字段当中
        :param page_type: 不同的页面类型,数据不同,具体的格式化方法会不同
        :raise NotImplementedError 基类该函数不可调用
        '''
        raise NotImplementedError
