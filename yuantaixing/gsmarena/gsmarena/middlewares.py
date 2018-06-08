"""中间层的编写"""
import logging
import time
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from scrapy.http import HtmlResponse
from selenium.webdriver.support import expected_conditions as EC

LOGGER = logging.getLogger(__name__)


class PhantomJSMiddleware(object):
    """浏览器模式爬取"""

    @staticmethod
    def process_request(request, spider):
        """处理请求"""
        if spider.name in ["gsmarena"]:
            dcap = dict(DesiredCapabilities.PHANTOMJS)
            dcap["phantomjs.page.settings.userAgent"] = (
                "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"
            )
            LOGGER.info("===PhantomJS is starting...")
            driver = webdriver.PhantomJS()
            driver.get(request.url)
            try:
                quote = request.meta["isQuote"]
            except KeyError:
                quote = None
            if not quote:
                # "等待底部页面加载出来"
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//*[@id='footer']")))
            else:
                time.sleep(1)
            body = driver.page_source

            return HtmlResponse(driver.current_url, body=body, encoding='utf-8', request=request)
        else:
            print("====unKown_spider====")

    @staticmethod
    def dothing():
        """donothing"""
