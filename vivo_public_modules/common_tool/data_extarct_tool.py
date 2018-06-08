"""
通用的数据提取模块
使用方式：
    在解析函数中定义一个字典，设置键rule_type 为规则类型， 设置其余键为需要提取信息的字段名
    如果需要先提取列表再提取字段，则定义键list_rule 为具体的规则
    目前支持6中提取规则
    1.re:
        字段键的值为正则表达式字符串，返回字典
    2.re_list
        先按正则提取出一个列表，再遍历列表取值，返回字典列表
    3.xpath
        字段键的值为xpath字符串，返回字典
    4.xpath_list
        先按xpath提取出一个列表，再遍历列表取值，返回字典列表
    5.json
        字段键的值为一个字典层级列表，返回字典
    6.json_list
        先按list_rule获取列表，再遍历列表取值，返回字典列表

    注意：如果规则错误，或需要提取的数据不存在，
          为了避免只因某个字段取值错误，导致报错，使正常提取的数据一并丢失，
          遂把失效的字段键的值设为None，程序不会报错，
          所以如果爬取过程中某个字段的值一直为None，请检查你写的提取规则


"""
import json
import re


class DataExtractTool(object):
    """数据提取工具类"""
    def __init__(self):
        self.__extract_method = {
            're': self.__extract_re,
            're_list': self.__extract_re_list,
            'xpath': self.__extract_xpath,
            'xpath_list': self.__extract_xpath_list,
            'json': self.__extract_json,
            'json_list': self.__extract_json_list,
            # 某个字段需要先提取列表，然后再合并组成一个值
            # 提取链接列表

        }

    def extract_data(self, rule_dict, content):
        """提取数据"""
        if isinstance(rule_dict, dict):
            # 如果rule是一个字典
            if 'rule_type' in rule_dict:
                # 如果字典中有rule_type键
                if rule_dict['rule_type'] in self.__extract_method:
                    # 调用对应的类型解析方法
                    rule_type = rule_dict.pop('rule_type')
                    data = self.__extract_method[rule_type](rule_dict, content)

                else:
                    raise TypeError('Rule_type is unknown')
            else:
                # 自动识别rule类型
                data = None
        else:
            # 当就是有人不按规范传参数的时候
            data = None

        return data

    @staticmethod
    def __extract_re(rule_dict, content):

        temp = dict()
        for key, rule in rule_dict.items():
            result = re.findall(rule, content)
            if result:
                temp[key] = result[0]
            else:
                temp[key] = None
        return temp

    def __extract_re_list(self, rule_dict, content):
        if 'list_rule' in rule_dict:
            temp = list()
            list_rule = rule_dict.pop('list_rule')
            for item in re.findall(list_rule, content):
                temp.append(self.__extract_re(rule_dict, item))
            return temp
        else:
            raise TypeError("没有在字典中定义rule_list的提取规则")

    @staticmethod
    def __extract_xpath(rule_dict, content):
        temp = dict()
        for key, rule in rule_dict.items():
            temp[key] = content.xpath(rule).extract_first()

        return temp

    def __extract_xpath_list(self, rule_dict, content):
        if 'list_rule' in rule_dict:
            temp = list()
            list_rule = rule_dict.pop('list_rule')
            for item in content.xpath(list_rule):
                temp.append(self.__extract_xpath(rule_dict, item))
            return temp
        else:
            raise TypeError("没有在字典中定义rule_list的提取规则")

    def __extract_json(self, rule_dict, content):
        temp = dict()
        if not isinstance(content, dict):
            content = json.loads(content)
        for key, rule in rule_dict.items():
            temp[key] = self.__extract_data_in_dict(rule, content)
        return temp

    def __extract_json_list(self, rule_dict, content):
        if 'list_rule' in rule_dict:
            temp = list()
            list_rule = rule_dict.pop('list_rule')

            if not isinstance(content, dict):
                content = json.loads(content)

            for item in self.__extract_data_in_dict(list_rule, content):
                temp.append(self.__extract_json(rule_dict, item))

            return temp
        else:
            raise TypeError("没有在字典中定义rule_list的提取规则")

    @staticmethod
    def __extract_data_in_dict(tier_list, content):
        for tier in tier_list:
            if tier in content:
                content = content[tier]
                continue
            else:
                content = None
        return content


DE_Tool = DataExtractTool()