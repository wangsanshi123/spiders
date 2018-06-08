"""
处理数据模块
"""
import re
import datetime
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst


class DatetimeProcessor(object):
    """
    处理时间类
    """

    def __call__(self, value):
        if 'min' in value:
            result = re.match(r'(\d+) hrs? (\d+) mins?  ago', value)
            value = datetime.datetime.now() - datetime.timedelta(
                hours=int(result.group(1)), minutes=int(result.group(2)))
        elif 'day' in value:
            days = re.match(r'(\d+) days? ago', value).group(1)
            value = datetime.datetime.now() - datetime.timedelta(days=int(days))
        elif value == "few seconds ago":
            value = datetime.datetime.now() - datetime.timedelta(minutes=1)
        elif 'Updated' in value:
            value = re.search(r'Updated (.+)\)', value).group(1)
        else:
            value = datetime.datetime.strptime(value, '%b %d, %Y %I:%M %p')
        return value.strftime('%Y-%m-%d %H:%M:%S')


class DataLoader(ItemLoader):
    """
    处理数据类
    """
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    model_score_out = Compose(TakeFirst(), float)
    price_out = Compose(TakeFirst(), lambda x: int(re.sub(r',', '', x)))
    recommend_rate_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
    model_comment_num_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
    brand_out = Compose(TakeFirst(), lambda x: x.split()[0])
    main_body_score_out = Compose(TakeFirst(), lambda x: 5 - x.count('unrated-star'))
    view_num_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
    time_out = Compose(TakeFirst(), DatetimeProcessor())
    main_body_out = Compose(lambda x: '\n'.join(x).strip())
    thumb_up_num_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
    content_comment_num_out = Compose(TakeFirst(), int)
    user_comment_num_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
    user_level_out = Compose(TakeFirst(), lambda x: 1)
    follower_num_out = Compose(TakeFirst(), lambda x: int(re.search(r'\d+', x)[0]))
