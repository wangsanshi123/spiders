# -*- coding: utf-8 -*-
'''
作者: 郑阔
日期: 2018.5.10
版本: 1.0 实现外销代理池类,外销的数据存储方案使用mongodb
    所以主要针对mongodb数据库细节实现BaseProxyPool子类VivoProxyPool
'''
import pymongo

from vivo_public_modules.download_middleware.base_proxy_pool import BaseProxyPool


class VivoProxyPool(BaseProxyPool):
    '''
    BaseProxyPool子类
    主要实现代理池初始化 init_proxy_pool
    代理状态更新方法 update_proxy_state
    '''
    def init_mongo_connection(self):
        '''
        根据 self.proxy_database_info 初始化mongodb连接
        :param self: 代理池类的实例
        :return:
            mongo_client: mongo连接客户,将其返回的目的旨在希望使用者能够及时关闭连接
                用完即关,再用再申请即可,避免资源浪费
            database: 操作数据集的句柄
        '''
        # 初始化 MongoClient 对象
        print(self.proxy_database_info)
        mongo_client = pymongo.MongoClient(
            self.proxy_database_info['host'],
            self.proxy_database_info['port']
        )
        # 获取相应的数据库
        database = mongo_client[self.proxy_database_info['database']]
        username = self.proxy_database_info['username']
        password = self.proxy_database_info['password']
        # 假如需要授权信息则进行授权
        if username and password:
            database.authenticate(username, password)
        # 前者用于关闭数据库连接, 后者用于检索数据库
        return mongo_client, database

    def init_proxy_pool(self, proxy_num):
        '''
        父类的抽象方法,针对mongodb数据库操作细节实现代理池初始化
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
        # 代理数据存放的集合名称
        self.proxy_collection = 'vivo_proxy'
        mongo_client, database = self.init_mongo_connection()
        proxy_field = 'proxy'
        # 筛选可用代理,并随机选择其中 proxy_num 个
        proxy_list = database[self.proxy_collection].aggregate(
            [
                {'$sample': {'size': proxy_num}},
                {'$match': {'usable': 1}}
            ]
        )
        proxy_list = list(proxy_list)
        print(len(proxy_list))
        # 关闭数据库连接
        mongo_client.close()
        return proxy_list, proxy_field

    def update_proxy_state(self):
        '''
        更新代理的状态,父类的抽象方法
        将代理从数据库当中读取出来,并使用 check_proxy 进行代理状态更新
        更细的代理状态主要包含: 代理是否可用, 代理的下载延迟, 代理的检测时间
        '''
        mongo_client, database = self.init_mongo_connection()
        # 将所有的代理都检索出来
        proxy_item_list = database[self.proxy_collection].find({})
        # 强制将数据迭代出来
        proxy_item_list = list(proxy_item_list)

        proxy_state_list = list()
        for proxy_item in proxy_item_list:
            proxy = proxy_item[self.proxy_field]
            proxy_state_list.append(self.check_proxy(proxy))

        # 处理代理的检测结果,将数据整理后入库
        proxy_state_dict = dict()
        for proxy, proxy_state in proxy_state_list:
            # proxy [usable, download_latency, check_time]
            proxy_state_dict[proxy] = proxy_state

        for proxy_item in proxy_item_list:
            proxy = proxy_item[self.proxy_field]
            proxy_state = proxy_state_dict[proxy]
            # 相当于主键用于更新
            proxy_item['_id'] = proxy
            # 代理是否可用
            proxy_item['usable'] = proxy_state[0]
            # 代理经历过的总检测次数
            proxy_item['check_total_count'] += 1
            # 代理经历过多次检测,检测成功的次数
            proxy_item['check_success_count'] += proxy_state[0]
            # 代理检测的成功率,说明代理的稳定性
            proxy_item['check_success_ratio'] = proxy_item['check_success_count'] / proxy_item['check_total_count']
            # 代理的下载速度
            proxy_item['download_latency'] = proxy_state[1]
            # 代理最近的检测时间
            proxy_item['check_time'] = proxy_state[2]
            # 将更新后的数据写入数据库
            database[self.proxy_collection].save(proxy_item)
        mongo_client.close()


if __name__ == '__main__':
    DATABASE_INFO = {
        "host": "192.168.121.33",
        "port": 20000,
        "database": "export_sale_web_data",
        "username": None,
        "password": None
    }
    # 模块测试
    proxy_pool = VivoProxyPool(DATABASE_INFO, 50)
    # proxy_pool.update_proxy_state()
