"""
处理数据模块
"""
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst


class DataLoader(ItemLoader):
    """
    处理数据类
    """
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    main_body_out = Join()
    user_level_out = Compose(TakeFirst(), lambda x: 1 if x else 0)
    model_name_out = Compose(TakeFirst(), lambda x: x.replace('from ', ''))
