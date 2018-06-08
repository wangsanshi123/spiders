"""数据库工具类"""
import hashlib
import logging
import pymongo

LOGGER = logging.getLogger(__name__)

# mongodb数据库的配置信息
MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017  # 端口号
MONGO_DB = "export_sale_web_data"  # 数据库


class MongodbUtil(object):
    """mongo的工具类"""

    def __init__(self):
        # 链接数据库
        self.client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT)
        # 数据库登录需要帐号密码的话
        # self.client.admin.authenticate(settings['MINGO_USER'], settings['MONGO_PSW'])
        self.db = self.client[MONGO_DB]  # 获得数据库的句柄
        return

    def get_max_item_from_col(self, collection, item, queryset=None):
        """
        从指定collection中获得最大的item值
        querset为字典
        """
        try:
            cursor = self.db[collection].find(queryset).sort([{item, pymongo.DESCENDING}]).limit(1)
        except Exception as error:
            LOGGER.error(error)
            return ""
        if cursor.count() > 0:
            return cursor[0][item]
        else:
            return ""


def get_md5(str):
    return hashlib.md5(str.encode('utf8')).hexdigest()


if __name__ == '__main__':
    model_id = get_md5("mobile_mi" + "mix2")
    print(MongodbUtil().get_max_item_from_col("User", "post_num", {"user_name": "BellaCandice"}))
