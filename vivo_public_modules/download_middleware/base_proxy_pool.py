# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.5.10
版本: 1.0 实现基础代理池类
问题: raise_for_status 异常没有针对性处理
'''
import time
import random
import datetime
import requests

from fake_useragent import UserAgent


class BaseProxyPool(object):
    '''
    希望为代理池提供统一的接口
    之后不管是自己搜集的代理建立的IP池,或者是使用其他的有偿代理服务
    都可以使用这个基类，并进行扩展,代理池主要负责如下功能
        提供指定大小的代理池;
        随机提供代理;
        检查更新代理状态;
    '''
    def __init__(self, proxy_database_info, proxy_num=500):
        '''
        完成代理池的初始化工作
        :param self: 代理池类的对象
        :param proxy_database_info: 代理数据库的配置信息
        :param proxy_num: 根据数据采集任务的不同，设置不同大小的代理池
        '''
        # 根据数据库配置信息,完成代理池的初始化工作,并明确代理数据的代理项
        # 由于代理池初始化访问数据库,代理状态更新访问数据库
        # 所以我们将数据库配置信息保留起来
        self.proxy_database_info = proxy_database_info
        self.proxy_list, self.proxy_field = self.init_proxy_pool(proxy_num)
        self.user_agent = UserAgent()

    def get_proxy(self):
        '''
        该接口为提供服务的接口，每次随机提供代理一个
        '''
        proxy = self.proxy_list[random.randint(0, len(self.proxy_list) - 1)][self.proxy_field]
        return proxy

    def init_proxy_pool(self, proxy_num):
        '''
        初始化指定大小代理池
        :param self: 代理池类的对象
        :param proxy_num: 代理池大小
        :return:
            proxy_list: [{'proxy': '....', 'usable': 1}, {'proxy': '....', 'usable': 1}]
            proxy_field: 'proxy'
        :raise: NotImplementedError
            由于使用的数据库并不明确,所以具体的访问数据库
            初始化代理列表的工作需要留给子类来完成
            假如调用基类的方法会报未实现异常
        '''
        raise NotImplementedError

    def check_proxy(self, proxy):
        '''
        检测代理是否可用，并返回请求相应的时间差
        :param proxy: 待检测代理
        :return: 代理, [是否可用, 传输时间, 检查时间]
        '''
        # 这里简单的用必应进行检测
        check_url = 'http://cn.bing.com'
        # 设置 User-Agent 头部
        headers = dict()
        headers['User-Agent'] = self.user_agent.random
        check_session = requests.session()
        # 需要记录代理的下载延迟,代表代理的质量
        begin_time = time.time()
        try:
            result = check_session.get(
                check_url, headers=headers,
                verify=False, proxies={'http': proxy},
                timeout=3
            )
            end_time = time.time()
            # 非200的响应则抛出异常
            result.raise_for_status()
            # 假如成功请求到页面则页面中应该包含某些关键字
            # warning 假如网站改版,这里可能就会受影响
            if '必应' in result.content.decode('utf8', 'ignore'):
                # 代理, [是否可用, 传输时间, 检查时间]
                return proxy, [1, end_time - begin_time, datetime.datetime.now()]
            return proxy, [0, 0, datetime.datetime.now()]
        except:
            return proxy, [0, 0, datetime.datetime.now()]

    def update_proxy_state(self):
        '''
        哪些代理可用,哪些代理速度快,啥时候更新的
        由于代理状态的更新需要涉及数据库读写
        需要确定数据库存储方案后,由子类实现相应的接口
        :return: None
        :raise: NotImplementedError
        '''
        raise NotImplementedError
