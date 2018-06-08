# -*- coding: utf-8 -*-
'''
使用xpath_parsing_spider类的需要将自己的itemloader放入这里
并继承VivoItemLoader,之后在xpath配置文件当中使用itemloader_class设置相应的itemloader
'''
import re
import datetime

from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose
from scrapy.loader.processors import TakeFirst
from scrapy.loader.processors import Join


class CleanText(object):
    '''
    总结一些常用的文本清晰方法
    方便以后loader.processor调用
    '''
    @classmethod
    def clean_white_space(cls, text):
        '''
        只是简单针对文本进行空白清洗,类方法
        :param text: 待清洗文本
        '''
        text = re.sub(r'(\n+|\t+|\r+)', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @classmethod
    def remove_begin_part(cls, text, trash_sign):
        '''
        移除字符串开头的一部分,目前做法比较简答
        找到垃圾文本的识别字符串,删除匹配字符串以及之前的文本
        text -> 'This is an advertisement. This is the text we want.'
        trash_sign -> 'advertisement.'
        result -> 'This is the text we want.'
        :param text: 待清洗文本
        :param trash_sign: 垃圾文本字符串
        :return: 清洗过后的文本
        '''
        trash_index = text.find(trash_sign)
        if trash_index != -1:
            text = text[trash_index + len(trash_sign):]
        return text.strip()

    @classmethod
    def remove_end_part(cls, text, trash_sign):
        '''
        移除字符串开头的一部分,目前做法比较简答
        找到垃圾文本的识别字符串,删除匹配字符串以及之前的文本
        text -> 'This is the text we want. Advertisement...'
        trash_sign -> 'advertisement'
        result -> 'This is the text we want.'
        :param text: 待清洗文本
        :param trash_sign: 垃圾文本字符串
        :return: 清洗过后的文本
        '''
        trash_index = text.find(trash_sign)
        if trash_index != -1:
            text = text[:trash_index]
        return text.strip()


class VivoItemLoader(ItemLoader):
    '''
    重点是将add_xpath,add_value,add_css,统一起来
    在xpath配置文件当中提供type值明确到底是xpath,value or css即可
    '''
    def __init__(self, item=None, selector=None, response=None, parent=None, **context):
        '''
        完成self.add_func的配置
        '''
        ItemLoader.__init__(self, item, selector, response, parent, **context)
        add_func = dict()
        add_func['xpath'] = self.add_xpath
        add_func['value'] = self.add_value
        add_func['css'] = self.add_css
        self.add_func = add_func

    def add(self, method, name, value):
        '''
        详细的解析函数
        :param method: xpath value css 三选一
        :param name: 对应item当中的哪个字段
        :param value: xpath路径,css路径,value值三选一
        '''
        self.add_func[method](name, value)


class TakeFirstItemLoader(VivoItemLoader):
    '''
    xpath解析得到的往往是一个列表,但我们实际上只需要第一项
    '''
    default_output_processor = TakeFirst()


class FormatTime(object):
    '''
    针对从网页当中的时间、日期类信息进行格式化
    首先需要使用re_pattern, 将各个日期部分(year, month, day, hour, second)匹配出来
    并且需要每个re group 为一个时间部件,随后需要将各个时间部件进行格式化
    最后结合各个部件实际的含义(time_segment_order: month, year)
    转换成真正的datetime.datetime类型
    '''
    month2num_dict = {
        'January': 1,
        'February': 2,
        'March': 3,
        'April': 4,
        'May': 5,
        'June': 6,
        'July': 7,
        'August': 8,
        'September': 9,
        'October': 10,
        'November': 11,
        'December': 12
    }

    def month2num(self, target_month):
        '''
        部分英文网站将月份展示为December or Dec
        本函数完成 Dec -> 12 的转换
        :param target_month: month in english
        :return: month in number, -1 代表数据异常无法解析到对应的月份
        '''
        for month in self.month2num_dict:
            if month.lower().startswith(target_month.lower()):
                return self.month2num_dict[month]
        return -1

    @classmethod
    def format_time(cls, time):
        '''
        基类提供的默认的时间格式化函数
        字符串通过正则解析后得到时间各个部分的列表,列表格式化后变为全数字形式
        数字与相应的时间部分名称进行结合 [12, 3, 2018] + ['month', 'day', 'year']
        {'year': 2018, 'month': 12, 'day': 3} -> datetime.datetime
        该函数完成时间部分列表 -> 数字列表的转化
        :param time: [2018, 'Aug', 20]
        '''
        return time

    @classmethod
    def str2num(cls, time_segment_list):
        '''
        默认只完成字符串到数字的转换
        部分网站可能需要 Aug -> 8 这种转换
        这种则需要网站继承该类别,实现自己的str2num方法
        :param time_segment_list: 各个时间部件组成的list
        :return: 时间部件组成的列表,列表元素必须为数字
        '''
        return [int(item) for item in time_segment_list]

    def __init__(self, re_pattern, time_segment_order):
        '''
        初始化传入一些必要的参数
        :param self: 类的实例
        :param re_pattern: 匹配时间的正则表达式
        :param time_segment_order: ['month', 'day', 'year'] 正则匹配到的部件表达的含义
        '''
        self.re_pattern = re_pattern
        self.time_segment_order = time_segment_order

    def __call__(self, values):
        '''
        该类别可以调用,针对loader传过来的数据列表进行处理
        '''
        time = ''.join(values).strip()
        time = re.search(self.re_pattern, time, re.M)
        if time:
            time = time.groups()
            # ['2018', 'Aug', '03']
            time = self.format_time(time)
            # ['2018', 8, '03']
            time = self.str2num(time)
            # [2018, 8, 03]
            if -1 in time or len(time) != len(self.time_segment_order):
                return None
            # {'year': 2018, 'month': 8, 'day': 3}
            return datetime.datetime(**dict(zip(self.time_segment_order, time)))
        return None


class CleanAndRemoveEndPart(CleanText):
    '''
    india_consumer_forum consumer_complaints
    网站的文本都是这样的,一方面需要清洗,另一方面需要去除尾部的广告
    '''
    def __init__(self, trash_sign):
        '''
        类的初始化函数,传入结尾垃圾文本的起始标志
        '''
        self.trash_sign = trash_sign

    def __call__(self, values):
        '''
        方法类需要实现的方法,使用正则完成文本清洗
        '''
        main_body = ' '.join(values)
        main_body = self.clean_white_space(main_body)
        main_body = self.remove_end_part(main_body, self.trash_sign)
        return main_body


class IndiaConsumerForumComplaintLoader(VivoItemLoader):
    '''
    网站投诉信息的itemloader
    '''
    default_output_processor = TakeFirst()
    date_out = FormatTime(r'(\d{2})/(\d{2})/(\d{4})', ['day', 'month', 'year'])
    content_comment_num_out = Compose(TakeFirst(), lambda num: int(num.split(' ')[0]))
    main_body_out = CleanAndRemoveEndPart('google_ad_client')


class IndiaConsumerForumComplaintCommentLoader(VivoItemLoader):
    '''
    网站投诉评论信息的itemloader
    '''
    default_output_processor = TakeFirst()
    main_body_out = CleanAndRemoveEndPart('google_ad_client')
    time_out = FormatTime(
        r'(\d{2})/(\d{2})/(\d{4}).+?(\d{1,2}):(\d{1,2})',
        ['day', 'month', 'year', 'hour', 'minute']
    )


class ConsumerComplaintsFormatTime(FormatTime):
    '''
    该网站时间格式为: on May 28, 2018
    所以继承FormatTime类重写format_time方法
    将 May -> 5
    '''
    def format_time(self, time):
        '''
        实现 May -> 5 的转换
        '''
        time_dict = dict(zip(self.time_segment_order, time))
        time_dict['month'] = self.month2num(time_dict['month'])
        return list(time_dict.values())


class ConsumerComplaintsComplaint(VivoItemLoader):
    '''
    网站投诉评论信息的itemloader
    '''
    content_url_out = Join('')
    main_body_out = CleanAndRemoveEndPart('(adsbygoogle')
    date_out = ConsumerComplaintsFormatTime(
        r'on ([A-Za-z]+).+?(\d+),.+?(\d+)',
        ['month', 'day', 'year']
    )
