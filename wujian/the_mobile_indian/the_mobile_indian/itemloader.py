"""
处理数据模块
"""
import re
import datetime
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst


class DatetimeProcessor(object):
    """
    处理时间类
    """
    def __call__(self, value):
        value = re.match(r"\w+ \w+ : (.+)", value).group(1)
        value = datetime.datetime.strptime(value, '%B %d, %Y %I:%M %p')
        return value.strftime('%Y-%m-%d %H:%M:%S')


class DataLoader(ItemLoader):
    """
    处理数据类
    """
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    main_body_out = Join()
    time_out = Compose(TakeFirst(), DatetimeProcessor())
