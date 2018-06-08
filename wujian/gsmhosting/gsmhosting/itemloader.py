"""
处理数据模块
"""
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
        if "Today" in value:
            value = datetime.datetime.combine(
                datetime.date.today(),
                datetime.datetime.strptime(value, 'Today, %H:%M').time()
            )
        elif "Yesterday" in value:
            value = datetime.datetime.combine(
                datetime.date.today() + datetime.timedelta(days=-1),
                datetime.datetime.strptime(value, 'Yesterday, %H:%M').time()
            )
        else:
            value = datetime.datetime.strptime(value, '%m-%d-%Y, %H:%M')
        return value.strftime('%Y-%m-%d %H:%M:%S')


class RegistrationDateProcessor(object):
    """
    处理注册时间类
    """

    def __call__(self, value):
        return datetime.datetime.strptime(value, '%b %Y')


class DataLoader(ItemLoader):
    """
    处理数据类
    """
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    registration_date_out = Compose(
        TakeFirst(),
        lambda x: x.split(": ")[1] if len(x.split(": ")) > 1 else x,
        RegistrationDateProcessor()
    )
    main_body_out = Join()
    time_out = Compose(lambda x: x[1], DatetimeProcessor())
