# -*- coding: utf-8 -*-
# @File    : httpproxy.py
# @Author  : LVFANGFANG
# @Time    : 2018/6/19 0019 16:13
# @Desc    :

import base64
from collections import defaultdict
from urllib.request import _parse_proxy

from scrapy.utils.python import to_bytes
from twisted.internet.error import ConnectionDone, ConnectionRefusedError


class ProxyMiddleware(object):
    maxbans = 400
    ban_code = 503
    download_timeout = 190
    connection_refused_delay = 90

    def __init__(self, crawler):
        self._bans = defaultdict(int)
        self.crawler = crawler
        self._saved_delays = defaultdict(lambda: None)
        proxy_url = self.crawler.settings.get('PROXY_URL')
        self.proxy_type, self.user, self.password, self.hostport = _parse_proxy(proxy_url)

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler)
        return o

    def process_request(self, request, spider):
        if self.hostport:
            proxy_url = self.proxy_type + '://' + self.hostport if self.proxy_type else 'http://' + self.hostport
            request.meta['proxy'] = proxy_url
            if self.user and self.password:
                user_pass = to_bytes('%s:%s' % (self.user, self.password), encoding="latin-1")
                creds = base64.b64encode(user_pass).strip()
                request.headers['Proxy-Authorization'] = b'Basic ' + creds

    def process_response(self, request, response, spider):
        key = self._get_slot_key(request)
        self._restore_original_delay(request)
        if response.status == self.ban_code:
            self._bans[key] += 1
            if self._bans[key] > self.maxbans:
                self.crawler.engine.close_spider(spider, 'banned')
            else:
                after = response.headers.get('retry-after')
                if after:
                    self._set_custom_delay(request, float(after))
        else:
            self._bans[key] = 0
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, (ConnectionRefusedError, ConnectionDone)):
            self._set_custom_delay(request, self.connection_refused_delay)

    def _get_slot_key(self, request):
        return request.meta.get('download_slot')

    def _get_slot(self, request):
        key = self._get_slot_key(request)
        return key, self.crawler.engine.downloader.slots.get(key)

    def _set_custom_delay(self, request, delay):
        """Set custom delay for slot and save original one."""
        key, slot = self._get_slot(request)
        if not slot:
            return
        if self._saved_delays[key] is None:
            self._saved_delays[key] = slot.delay
        slot.delay = delay

    def _restore_original_delay(self, request):
        """Restore original delay for slot if it was changed."""
        key, slot = self._get_slot(request)
        if not slot:
            return
        if self._saved_delays[key] is not None:
            slot.delay, self._saved_delays[key] = self._saved_delays[key], None
