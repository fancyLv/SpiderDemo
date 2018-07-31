# -*- coding: utf-8 -*-
# @File    : run.py
# @Author  : LVFANGFANG
# @Time    : 2018/7/30 0030 23:09
# @Desc    :

import django

django.setup()

import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scrapy_common.spiders.example import ExampleSpider

from configs.models import Seed, Selector

if __name__ == '__main__':
    if len(sys.argv) > 1:
        seedid = sys.argv[1]
        seed = Seed.objects.get(id=seedid)
        config = {'name': seed.name, 'start_urls': seed.start_urls.split(), 'method': seed.method,
                  'headers': seed.headers, 'cookies': seed.cookies, 'dynamic': seed.dynamic,
                  'proxy': seed.proxy,
                  'form_data': seed.form_data, 'download_delay': seed.download_delay, 'status': seed.status,
                  'concurrent_requests': seed.concurrent_requests, 'rule': seed.id}
        selectors = []
        for s in Selector.objects.filter(rid=seed.id):
            item = {'parentSelectors': s.parent.name if s.parent else '_root', 'name': s.name, 'type': s.type,
                    'multiple': s.multiple, 'method': s.method, 'selector': s.selector, 'regex': s.regex,
                    'rule_id': s.rid_id}
            selectors.append(item)

        name = config['name']  # 爬虫名称
        url = config['start_urls']  # 起始链接
        method = config['method']  # 请求方法
        proxy = config['proxy']  # 是否启用代理
        dynamic = config['dynamic']  # 是否启用浏览器
        headers = config['headers']  # 请求头
        cookie = config['cookies']
        form = config['form_data']  # 表单
        downloadDelay = config['download_delay']  # 请求间隔
        concurrent = config['concurrent_requests']  # 并发数

        DEFAULT_SETTINGS = get_project_settings()

        proxy_url = DEFAULT_SETTINGS['PROXY_URL'] if proxy else None

        if downloadDelay:
            DEFAULT_SETTINGS['DOWNLOAD_DELAY'] = downloadDelay
        if concurrent:
            DEFAULT_SETTINGS['CONCURRENT_REQUESTS_PER_DOMAIN'] = concurrent

        if proxy and not dynamic:
            DEFAULT_SETTINGS['DOWNLOADER_MIDDLEWARES'].update({
                'scrapy_common.middlewares.httpproxy.ProxyMiddleware': 960,
            })

        if dynamic:
            DEFAULT_SETTINGS['DOWNLOADER_MIDDLEWARES'].update({
                'scrapy_splash.SplashCookiesMiddleware': 723,
                'scrapy_splash.SplashMiddleware': 725,
                'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            })
            DEFAULT_SETTINGS['SPIDER_MIDDLEWARES'] = {
                'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
            }
            DEFAULT_SETTINGS['DUPEFILTER_CLASS'] = 'scrapy_splash.SplashAwareDupeFilter'
            DEFAULT_SETTINGS['HTTPCACHE_STORAGE'] = 'scrapy_splash.SplashAwareFSCacheStorage'

        process = CrawlerProcess(DEFAULT_SETTINGS)
        process.crawl(ExampleSpider, url, name, method, headers, form, cookie, selectors, proxy_url, dynamic)
        process.start()
