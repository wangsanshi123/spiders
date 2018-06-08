"""
-*- coding: utf-8 -*-
"""

# Scrapy settings for mobiles project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'mobiles'

SPIDER_MODULES = ['mobiles.spiders']
NEWSPIDER_MODULE = 'mobiles.spiders'

# DOWNLOADER_MIDDLEWARES = {
#     'vivo_public_modules.download_middleware.TuringUserAgentMiddleware': 543,
#     'vivo_public_modules.download_middleware.VivoProxyMiddleware': 543,
# }


COOKIES_ENABLED = False
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3
DOWNLOAD_TIMEOUT = 10
RETRY_TIMES = 8
CONCURRENT_REQUESTS = 4

# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 60 * 60 * 6
# HTTPCACHE_DIR = 'html_catch'
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

ITEM_PIPELINES = {
    'vivo_public_modules.item_pipeline.item_sorter.ItemSorter': 300,
    'vivo_public_modules.item_pipeline.item2mongodb.Item2Mongodb': 800,
}

CONFIG_DIR = 'E:/chen/spider/chenchun/vivo_public_modules/config'
DATABASE_STRUCTURE = 'database_structure.json'
DATABASE_CONFIG = 'database_config.json'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'mobiles (+http://www.yourdomain.com)'

# Obey robots.txt rules
# ROBOTSTXT_OBEY = False

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
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML,'
                  ' like Gecko) Chrome/64.0.3282.186 Safari/537.36'
}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'mobiles.middlewares.MobilesSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'mobiles.middlewares.MyCustomDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#     'mobiles.pipelines.MobilesPipeline': 300,
# }

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
# See http://scrapy.readthedocs.org/en/latest/topics/downloader
# -middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
# MONGODB_HOST = '192.168.121.33'
# MONGODB_HOST = '127.0.0.1'
# # 端口号，默认是27017
# MONGODB_PORT = 27017
# # 数据库名称
# MONGODB_DBNAME = 'export_sale_web_data'
# # 存放数据的表名称
# MONGODB_DOCNAME = 'model'
