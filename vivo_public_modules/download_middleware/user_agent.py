'''
作者: 郑阔
日期: 2018.4.26
版本: 1.0 完成 user_agent 伪装,使用了第三方库,所以需要先安装相应的模块
      pip install fake-useragent
问题: 使用第三方库,首次使用需要向服务器请求数据完成 user_agent 头部的缓存
      假如网络连通性不好,有可能出现无法异常情况,目前并未对潜在风险设置有效预防措施
'''
# 依赖的库
from fake_useragent import UserAgent

class VivoUserAgentMiddleware(object):
    '''
    针对系统产生的 scrapy.Request 请求添加伪装的 User-Agent.
    '''
    def __init__(self):
        '''
        初始化 fake_useragent.UserAgent对象
        :param self: 中间件对象本身
        :return: None
        '''
        self.user_agent = UserAgent()

    def process_request(self, request, spider):
        '''
        下载中间件要求实现的接口之一,我们需要针对请求进行包装
        所以仅实现 process_request 模块即可
        '''
        request.headers['User-Agent'] = self.user_agent.random
