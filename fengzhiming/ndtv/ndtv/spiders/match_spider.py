"""根据代码风格抽象出来的代码基类，提高代码复用率"""

from scrapy.item import Item
from scrapy.item import Field
from scrapy.http import Request
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class MatchDictSpier(ItemPaddingSpider):
    """根据代码风格抽象出来的代码基类，提高代码复用率"""
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.match_dict = dict()

    def parse(self, response):
        """主解析，流程控制"""
        # 获取当前网页的类型
        url_type = response.meta['url_type']
        # 判断是否有上级数据
        is_has_superior_data = "data" in response.meta
        # 调用对应的网页解析方法
        data_dict = self.match_dict[url_type]['parse'](response)
        # 获取页面解析后的数据
        for data in data_dict['data']:
            # 如果有上级数据，合并两个数据字典
            if is_has_superior_data:
                data = dict(data, **response.meta['data'])

            # 判断当前数据是否有后续数据
            if data['next_url_request']:
                # 如果有后续数据，调用对应的后续数据请求方法
                yield self.match_dict[data['next_url_request']['url_type']]['request'](data)
            else:
                # 如果没有后续数据，调用对应的数据保存方法
                data.pop("next_url_request")
                yield self.match_dict[url_type]['save'](data)

        # 获取页面解析后的非后续数据请求链接请求
        for new_request in data_dict['new_request']:
            yield self.match_dict[new_request['url_type']]['request'](new_request)

    def simple_new_request(self, new_request):
        """简单的新url请求，没有需要关联的数据与接口参数破解"""
        url = new_request.pop('url')
        return Request(url, meta=new_request, callback=self.parse)

    def simple_next_request(self, data):
        """简单的带数据url请求，主要是将当前类型网页解析的数据传到别的类型网页"""
        url = data['next_url_request']['url']
        url_type = data['next_url_request']['url_type']
        data.pop('next_url_request')
        meta = {'url_type': url_type, "data": data}
        return Request(url, meta=meta, callback=self.parse)

    def simple_data_save(self, data):
        """简单的数据保存方式，referer_id为-1"""
        return self.generate_item(data, -1)

    def generate_item(self, data, refer_id):
        """将传入的字典类型的data数据转换成item"""
        item = Item()
        for key, value in data.items():
            item.fields[key] = Field()
            item[key] = value
        return self.padding_item(item, refer_id)

    @staticmethod
    def get_rule_data(rule_dict, content):
        """
        根据规则，获取数据,此方法只适合提取的单个数据，不适用于列表
        :param rule_dict: 规则字典
        :param content: 待提取的原始内容
        :return: 提取后的数据字典
        """
        temp_item = dict()
        # 获取规则类型
        rule_type = rule_dict.pop('rule_type')
        # 正则
        if rule_type == "re":
            for key, rule in rule_dict.items():
                result = rule.findall(content)
                if result:
                    temp_item[key] = result[0]
                else:
                    temp_item[key] = ""
        # xpath
        if rule_type == "xpath":
            for key, rule in rule_dict.items():
                temp_item[key] = content.xpath(rule).extract_first()
        return temp_item

    @staticmethod
    def get_dict_key(dict_obj, key_tier_list):
        """传入一个字典对象，以及一个层级列表，获取对应的层级列表值，如果不存在，则返回空"""
        key_iter_len = len(key_tier_list)
        for i in range(key_iter_len):
            if key_tier_list[i] not in dict_obj:
                return ""
            else:
                dict_obj = dict_obj[key_tier_list[i]]
        else:
            return dict_obj
