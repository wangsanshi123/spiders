# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.5.11
版本: 1.0 为防止IP封锁的下载器中间件
问题: 因为一台代理服务器实际上可以开多个端口产生多个代理
    代理池每次随机选择一个可用代理返回,有可能会是相同的IP不同的端口
    所以针对有非常严格的IP封锁的网站有可能会失败
    所以假如存在此类需求,可以继承或者在维持现有接口的情况下添加新的内容
    从而满足需求
'''
import os
import json

from scrapy.exceptions import NotConfigured

from vivo_public_modules.download_middleware.vivo_proxy_pool import VivoProxyPool

class VivoProxyMiddleware(object):
    '''
    代理中间件,为了防止IP封锁而实现的下载器中间件
    '''
    def __init__(self, database_config_file, proxy_pool_size):
        '''
        主要是完成代理池的初始化工作
        :param database_config_file: 数据库的配置信息,从数据库当中读取代理信息
        :param proxy_pool_size: 代理池大小,不同网站数据量不同,可能需要不同大小的代理池
        '''
        database_config = json.load(open(database_config_file, 'r'))
        self.proxy_pool = VivoProxyPool(database_config, proxy_pool_size)

    def process_request(self, request, spider):
        '''
        下载器中间件必须实现的方法之一,为请求添加代理
        :param request: 待处理的请求
        :param spider: spider实例,或许有些中间件会针对不同的spider做不同的处理
        '''
        proxy = self.proxy_pool.get_proxy()
        request.meta['proxy'] = proxy

    @classmethod
    def from_crawler(cls, crawler):
        '''
        主要从 crawler 当中的 settings 当中获取两个配置信息
        DATABASE_CONFIG PROXY_POOL_SIZE
        :param cls: 类本身 cls() 相当于调用构造函数 生成类实例
        :param crawler: scrapy 项目运行后的 crawler 实例
        :return: VivoProxyMiddleware 类对象
        :raise: 假如 settings 文件当中没有找到 相应的配置项就会抛出异常
        '''
        # 项目配置信息所在的路径
        config_dir = crawler.settings.get('CONFIG_DIR', None)
        database_config_file = crawler.settings.get('DATABASE_CONFIG', None)
        if not config_dir or not database_config_file:
            raise NotConfigured
        database_config_file = os.path.join(config_dir, database_config_file)
        # 明确代理池大小
        proxy_pool_max_size = 100000
        proxy_pool_size = crawler.settings.get('PROXY_POOL_SIZE', proxy_pool_max_size)
        return cls(database_config_file, proxy_pool_size)
