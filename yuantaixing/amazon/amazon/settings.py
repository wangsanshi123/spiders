"""配置信息"""
# Scrapy settings for consumer_complaints project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import logging

BOT_NAME = 'amazon'

SPIDER_MODULES = ['amazon.spiders']
NEWSPIDER_MODULE = 'amazon.spiders'

# DOWNLOADER_MIDDLEWARES = {
#     'download_middleware.TuringUserAgentMiddleware': 543,
#     'download_middleware.VivoProxyMiddleware': 543,
# }

ROBOTSTXT_OBEY = False

COOKIES_ENABLED = False
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3
DOWNLOAD_TIMEOUT = 10
RETRY_TIMES = 8
CONCURRENT_REQUESTS = 4

ITEM_PIPELINES = {
    'vivo_public_modules.item_pipeline.item_sorter.ItemSorter': 300,
    'vivo_public_modules.item_pipeline.item2mongodb.Item2Mongodb': 800,
}

# CONFIG_DIR = '/opt/zhengkuo/public_python_module/vivo_spider/config'
CONFIG_DIR = 'D:/ytx/git/spider_code_new/spider_temp/spider/vivo_public_modules/config'
DATABASE_STRUCTURE = 'database_structure.json'
DATABASE_CONFIG = 'database_config.json'

# Crawl responsibly by identifying yourself (and your website) on the user-agent

# Obey robots.txt rules

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'consumer_complaints.middlewares.ConsumerComplaintSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'consumer_complaints.middlewares.MyCustomDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'consumer_complaints.pipelines.ConsumerComplaintPipeline': 300,
# }
DOWNLOADER_MIDDLEWARES = {
    'vivo_public_modules.download_middleware.user_agent.VivoUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}
# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings


LOG_FILE = 'exceptions.txt'
LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.DEBUG

# 从当前时间往前更新的天数
# 如果没有，则从vivo_public_modules中读取，如果vivo_public_modules中也没有，则默认为0
# 如果为零则默认更新到上次更新的最新时间（如果没有，则一直更新到没有内容，即全量更新，适用用新加手机型号时），
# 新加手机型号时，new_append字段为1，做全量更新
UPDATE_DATE = 90
