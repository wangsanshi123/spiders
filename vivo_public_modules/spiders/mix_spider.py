import datetime
import json
import os
from time import strftime
from vivo_public_modules.spiders.item_padding_spider import ItemPaddingSpider


class MixSpider(ItemPaddingSpider):
    """"
    增量更新类
    """
    first_in = True
    update_date = 0
    current_date = strftime("%Y-%m-%d")
    support_new_append = True  # 默认子爬虫类型是支持新增model_name

    def get_config_file(self):
        config_dir = self.settings.get('CONFIG_DIR', None)
        config_file = os.path.join(config_dir, "website_config/{}.json".format(self.name))
        return config_file

    def init_update_time_config(self):
        """
        用于获取该项目的更新时间，如果update_date>0,update为需要更新的天数，否则表示全量更新
        只能在parse方法即以后调用，否则无法加载配置文件
        """
        if self.first_in:  # 第一次调用parse方法时，获取配置信息
            self.first_in = False
            update_date = self.settings.get("UPDATE_DATE", None)
            if not update_date:
                # 项目配置信息所在的路径
                config_dir = self.settings.get('CONFIG_DIR', None)
                base = os.path.join(config_dir, "base.json")
                base_configs = json.load(open(base, 'r'))
                try:
                    update_date = base_configs["UPDATE_DATE"]
                except Exception:
                    update_date = -1
            self.update_date = update_date

    def get_date_to_update(self, response, date_or_time):
        """
        :param response:
        :param date_or_time:
        :return:
        在需要做增量更新的地方调用此方法，如果返回值为-1，则表明该请求更新完成，否则继续爬取
        如果是支持增加model_name的网站则，要传入new_append参数，1表示该机型是新增加，0表示不是；
        且翻页时new_append要传入request的meta中；first_in在翻页时要传入request的meta中去，且值为False
        """
        try:
            first_in = response.meta["first_in"]  # 子类中应该在做翻页请求时，应将first_in传入request的meta中
        except:
            first_in = True
            pass
        if first_in:  # 判断第一次进入parse_comment时，response中是否带有brand,model_name，
            # 如带有，则会有新增加指定model_name的情况，所以会执行
            try:
                brand = response.meta["brand"]  # 如果是新闻类，则不会有brand,try except内的代码都不会执行
                model_name = response.meta["model_name"]
                new_append = response.meta["new_append"]

                # 修改配置文件中的状态，一个机型只会在第一次进入parse/parse_comments的时候执行一次
                config_dir = self.settings.get('CONFIG_DIR', None)
                base = os.path.join(config_dir, "website_config/{}.json".format(self.name))
                with open(base, 'r+') as f:
                    result = json.load(f)
                    for item in result:
                        if item["brand"] == brand and item["model_name"] == model_name:
                            item["new_append"] = 0
                    f.seek(0)
                    f.truncate()
                    f.write(json.dumps(result))
            except:
                self.support_new_append = False
                pass
            date_to_update = (datetime.datetime.strptime(self.current_date, "%Y-%m-%d")
                              - datetime.timedelta(self.update_date)).strftime("%Y-%m-%d")
        else:  # 如果不是第一次进入，即翻页时，date_to_update通过从response的meta里面获取
            date_to_update = response.meta["date_to_update"]
            new_append = response.meta["new_append"] if self.support_new_append else None

        # ==================增量更新=============================
        if self.support_new_append and not new_append and self.update_date > 0:  # 如果不是新增加的机型，且update_date>0,则增量更新，否则全量
            if date_or_time and date_to_update and date_or_time < date_to_update:
                print("增量更新，date:{},date_to_update:{}".format(date_or_time, date_to_update))
                return -1
        elif not self.support_new_append and self.update_date > 0:
            if date_or_time and date_to_update and date_or_time < date_to_update:
                print("增量更新，date:{},date_to_update:{}".format(date_or_time, date_to_update))
                return -1
        return date_to_update
        # ==================增量更新=============================
