# -*- coding: utf-8 -*-
# @File    : example.py
# @Author  : LVFANGFANG
# @Time    : 2018/6/11 0014 10:36
# @Desc    :
import copy
import re
import urllib

import scrapy
from scrapy import FormRequest, Request
from scrapy.http.response import Response
from scrapy_splash import SplashRequest, SplashFormRequest


class ExampleSpider(scrapy.Spider):
    name = 'example'
    allowed_domains = []
    start_urls = []
    method = ''
    form = {}
    cookies = {}
    selectors = []

    def __init__(self, url, name, method, headers, form, cookies, selectors, proxy, dynamic, *args, **kwargs):
        super(ExampleSpider, self).__init__(*args, **kwargs)
        self.name = name
        self.start_urls = url
        self.method = method
        self.headers = headers
        self.form = form
        self.cookies = cookies
        self.selectors = selectors
        self.dynamic = dynamic
        self.args_data = {'wait': 0.5, 'images': 0}
        script = """
                function main(splash)
                    splash:set_viewport_size(1028, 10000)
                    splash:go(splash.args.url)
                    local scroll_to = splash:jsfunc("window.scrollTo")
                    scroll_to(0, 2000)
                    splash:wait(15)
                    return {
                        html = splash:html()
                    }
                end
                """
        if proxy:
            self.args_data.update({'proxy': proxy})
        # if scroll:
        #     self.args_data.update({'lua_source': script})

    def start_requests(self):
        # 请求方式
        # print(self.start_urls)
        for url in self.start_urls:
            if not self.dynamic:
                if self.method.lower() == 'post':
                    request = FormRequest(url=url, formdata=self.form, headers=self.headers, cookies=self.cookies,
                                          callback=self.parse_first, dont_filter=True)
                else:
                    request = Request(url=url, headers=self.headers, cookies=self.cookies, callback=self.parse_first)
            else:
                if self.method.lower() == 'post':
                    request = SplashFormRequest(url=url, formdata=self.form,
                                                callback=self.parse_first, dont_filter=False,
                                                args=self.args_data)
                else:
                    request = SplashRequest(url, callback=self.parse_first, endpoint='execute',
                                            args=self.args_data)
            yield request

    def parse_first(self, response):
        """web socket参数"""
        _, rest = urllib.parse.splittype(response.url)
        host, _ = urllib.parse.splithost(rest)
        self.domain = host

        for elem in self.parse(response):
            yield elem

    def parse(self, response):
        """响应处理函数"""
        # 判断响应结果
        # if not isinstance(response, HtmlResponse):
        if not isinstance(response, Response):
            self.logger.info("non-HTML response is skipped: %s", response.url)
            return
        # 根目录选择器
        root_selectors = [i for i in self.selectors if i["parentSelectors"] == "_root"]
        # 结果集
        result = {}
        # 翻页url
        link = ''
        # 遍历根目录选择器
        for root_selector in root_selectors:
            # text类型选择器
            if root_selector["type"] == "SelectorText":
                text = self.text_resolve(root_selector, response)
                # 非多元素
                if text and not root_selector["multiple"]:
                    text = [text[0]]
                # 正则过滤
                if 'regex' in root_selector and root_selector["regex"]:
                    text = [re.findall(root_selector["regex"], i)[0] if re.findall(root_selector["regex"], i) else ""
                            for i in text]
                result[root_selector['name']] = text if root_selector["multiple"] or not text else text[0]
            # image类型选择器
            elif root_selector["type"] == "SelectorImage":
                image = self.image_resolve(root_selector, response, response.url)
                # 非多元素
                if image and not root_selector["multiple"]:
                    image = [image[0]]
                result[root_selector['name']] = image if root_selector["multiple"] or not image else image[0]
            # attribute类型选择器
            elif root_selector["type"] == "SelectorElementAttribute":
                attribute = self.attribute_resolve(root_selector, response)
                # 非多元素
                if attribute and not root_selector["multiple"]:
                    attribute = [attribute[0]]
                # 正则过滤
                if 'regex' in root_selector and root_selector["regex"]:
                    attribute = [
                        re.findall(root_selector["regex"], i)[0] if re.findall(root_selector["regex"], i) else "" for i
                        in attribute]
                result[root_selector['name']] = attribute if root_selector["multiple"] or not attribute else attribute[
                    0]
            # html类型选择器
            elif root_selector["type"] == "SelectorHTML":
                html = self.html_resolve(root_selector, response)
                # 非多元素
                if html and not root_selector["multiple"]:
                    html = [html[0]]
                # 正则过滤
                if 'regex' in root_selector and root_selector["regex"]:
                    html = [re.findall(root_selector["regex"], i)[0] if re.findall(root_selector["regex"], i) else ""
                            for i in html]
                result[root_selector['name']] = html if root_selector["multiple"] or not html else html[0]
            # link类型选择器
            elif root_selector["type"] == "SelectorLink":
                if 'first' not in response.meta:
                    link = self.link_resolve(root_selector, response)

        # element类型选择器
        element_selectors = [i for i in self.selectors if
                             i["parentSelectors"] == "_root" and i["type"] == "SelectorElement"]
        # detail类型选择器
        detail_selectors = [i for i in self.selectors if
                            i["parentSelectors"] == "_root" and i["type"] == "SelectorDetail"]
        if element_selectors:
            yield from self.element_parse(element_selectors[0], response, result, response.url)

        elif detail_selectors:
            detail_urls = self.detail_resolve(detail_selectors[0], response, response.url)
            child_selectors = [i for i in self.selectors if i["parentSelectors"] == detail_selectors[0]['name']]
            if detail_urls and child_selectors:
                yield from self.detail_parse(detail_selectors[0], detail_urls, child_selectors, result)
            else:
                yield result
        else:
            yield result

        # 翻页
        print('--------------------------')
        print('next page', link)
        if link:
            if isinstance(link, tuple):
                pagerange, regex = link[0], link[1]
                try:
                    args = eval(pagerange)
                except Exception as e:
                    args = 0
                if not isinstance(args, tuple):
                    args = (0, args)
                for i in range(*args):
                    if not self.dynamic:
                        if self.method.lower() == 'post':
                            request = FormRequest(url=re.sub(regex, str(i), response.url), formdata=self.form,
                                                  headers=self.headers,
                                                  cookies=self.cookies, meta={'first': False}, callback=self.parse)
                        else:
                            request = Request(url=re.sub(regex, str(i), response.url), headers=self.headers,
                                              cookies=self.cookies,
                                              meta={'first': False})
                    else:
                        if self.method.lower() == 'post':
                            request = SplashFormRequest(url=re.sub(regex, str(i), response.url), formdata=self.form,
                                                        meta={'first': False},
                                                        args=self.args_data,
                                                        callback=self.parse)
                        else:
                            request = SplashRequest(url=re.sub(regex, str(i), response.url), meta={'first': False},
                                                    callback=self.parse, endpoint='execute', args=self.args_data)
                    yield request
            if isinstance(link, str):
                print('下一页', link)
                if not self.dynamic:
                    if self.method.lower() == 'post':
                        request = FormRequest(url=link, formdata=self.form, headers=self.headers, cookies=self.cookies,
                                              callback=self.parse, dont_filter=True)
                    else:
                        request = Request(url=link, headers=self.headers, cookies=self.cookies, callback=self.parse)
                else:
                    if self.method.lower() == 'post':
                        request = SplashFormRequest(url=link, formdata=self.form, callback=self.parse, dont_filter=True,
                                                    args=self.args_data)
                    else:
                        request = SplashRequest(url=link, endpoint='execute',
                                                callback=self.parse, args=self.args_data)
                yield request

    def element_parse(self, selectorElement, response, result, response_url):
        """元素选择器解析"""
        # 子选择器
        child_selectors = [i for i in self.selectors if i["parentSelectors"] == selectorElement['name']]
        detail_selectors = [i for i in self.selectors if
                            i["parentSelectors"] == selectorElement['name'] and i["type"] == "SelectorDetail"]
        new_result = []
        selector = getattr(response,selectorElement["method"])
        for sub_response in selector(selectorElement["selector"]):
            data = {}
            # 编辑根目录选择器
            for child_selector in child_selectors:
                # text类型选择器
                if child_selector["type"] == "SelectorText":
                    text = self.text_resolve(child_selector, sub_response)
                    # 非多元素
                    if text and not child_selector["multiple"]:
                        text = [text[0]]
                    # 正则过滤
                    if child_selector["regex"]:
                        text = [
                            re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else ""
                            for i in text]
                    data[child_selector['name']] = text if child_selector["multiple"]  else text[0] if text else None
                # image类型选择器
                elif child_selector["type"] == "SelectorImage":
                    image = self.image_resolve(child_selector, sub_response, response_url)
                    data[child_selector['name']] = image if child_selector["multiple"]  else image[0] if image else None
                # attribute类型选择器
                elif child_selector["type"] == "SelectorElementAttribute":
                    attribute = self.attribute_resolve(child_selector, sub_response)
                    # 非多元素
                    if attribute and not child_selector["multiple"]:
                        attribute = [attribute[0]]
                    # 正则过滤
                    if "regex" in child_selector and child_selector["regex"]:
                        attribute = [
                            re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else ""
                            for
                            i in attribute]
                    data[child_selector['name']] = attribute if child_selector["multiple"] else attribute[
                        0] if attribute else None
                # html类型选择器
                elif child_selector["type"] == "SelectorHTML":
                    html = self.html_resolve(child_selector, sub_response)
                    # 非多元素
                    if html and not child_selector["multiple"]:
                        html = [html[0]]
                    # 正则过滤
                    if child_selector["regex"]:
                        html = [
                            re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else ""
                            for i in html]
                    data[child_selector['name']] = html if child_selector["multiple"] else html[0] if html else None
            if detail_selectors:
                detail_urls = self.detail_resolve(detail_selectors[0], sub_response, response.url)
                sub_child_selectors = [i for i in self.selectors if
                                       i["parentSelectors"] == detail_selectors[0]["name"]]
                detail_item = copy.deepcopy(result)
                detail_item.update(data)
                if detail_urls and sub_child_selectors:
                    yield from self.detail_parse(detail_selectors[0], detail_urls[:1], sub_child_selectors, detail_item)
                elif data:
                    new_result.append(data)


            elif data:
                new_result.append(data)

        if not detail_selectors or new_result:
            result.update({selectorElement['name']: new_result})
            yield result

    def detail_resolve(self, selectorDetail, response, response_url):
        """获取详情页url"""
        if selectorDetail['method'] == 'css':
            if '::attr' in selectorDetail["selector"]:
                pages = response.css(selectorDetail["selector"]).extract()
            else:
                pages = response.css(selectorDetail["selector"] + "::attr(href)").extract()
        else:
            if '/@href' in selectorDetail["selector"]:
                pages = response.xpath(selectorDetail["selector"]).extract()
            else:
                pages = response.xpath(selectorDetail["selector"] + "/@href").extract()
        # 空值
        if not pages:
            return []
        result = []
        if not selectorDetail["multiple"]:
            pages = [pages[0]]
        for page in pages:
            if page.startswith('javascript'):
                continue
            # page = urllib.parse.urljoin(self.start_urls[0], page)
            page = urllib.parse.urljoin(response_url, page)
            result.append(page)
        return result

    def detail_parse(self, selectorsDetail, detailUrls, childSelectors, result):
        """详情页处理"""
        for i in detailUrls:
            if not self.dynamic:
                yield Request(url=i, callback=self.detail_first, headers=self.headers, cookies=self.cookies,
                              meta={'result_item': result, 'childSelectors': childSelectors,
                                    'selectorsDetail': selectorsDetail})
            else:
                yield SplashRequest(url=i, callback=self.detail_first, endpoint='execute',
                                    meta={'result_item': result, 'childSelectors': childSelectors,
                                          'selectorsDetail': selectorsDetail},
                                    args=self.args_data)

    def detail_first(self, response):
        """详情页参数"""
        _, rest = urllib.parse.splittype(response.url)
        host, _ = urllib.parse.splithost(rest)
        self.domain = host
        yield from self.get_detail(response)

    def get_detail(self, response):
        """解析详情页"""
        # 结果集
        result_item = response.meta['result_item']
        # 选择器
        selectorsDetail = response.meta['selectorsDetail']
        # 子选择器
        childSelectors = response.meta['childSelectors']
        # 判断响应结果
        if not isinstance(response, Response):
            self.logger.info("non-HTML response is skipped: %s", response.url)
            return
        result = {}
        # 遍历子选择器
        for child_selector in childSelectors:
            # text类型选择器
            if child_selector["type"] == "SelectorText":
                text = self.text_resolve(child_selector, response)
                # 非多元素
                if text and not child_selector["multiple"]:
                    text = [text[0]]
                # 正则过滤
                if child_selector["regex"]:
                    text = [re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else ""
                            for i in text]
                result[child_selector['name']] = text if child_selector["multiple"]  else text[0] if text else None
            # image类型选择器
            elif child_selector["type"] == "SelectorImage":
                image = self.image_resolve(child_selector, response, response.url)
                result[child_selector['name']] = image if child_selector["multiple"] else image[0] if image else None
            # attribute类型选择器
            elif child_selector["type"] == "SelectorElementAttribute":
                attribute = self.attribute_resolve(child_selector, response)
                # 非多元素
                if attribute and not child_selector["multiple"]:
                    attribute = [attribute[0]]
                # 正则过滤
                if child_selector["regex"]:
                    attribute = [
                        re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else "" for
                        i in attribute]
                result[child_selector['name']] = attribute if child_selector["multiple"] else attribute[
                    0] if attribute else None
            # html类型选择器
            elif child_selector["type"] == "SelectorHTML":
                html = self.html_resolve(child_selector, response)
                # 非多元素
                if html and not child_selector["multiple"]:
                    html = [html[0]]
                # 正则过滤
                if child_selector["regex"]:
                    html = [re.findall(child_selector["regex"], i)[0] if re.findall(child_selector["regex"], i) else ""
                            for i in html]
                result[child_selector['name']] = html if child_selector["multiple"] else  html[0] if html else None

        result_item.update(result)

        # element类型选择器
        element_selectors = [i for i in self.selectors if
                             i["parentSelectors"] == selectorsDetail['name'] and i["type"] == "SelectorElement"]
        # detail类型选择器
        detail_selectors = [i for i in self.selectors if
                            i["parentSelectors"] == selectorsDetail['name'] and i["type"] == "SelectorDetail"]
        if element_selectors:
            yield from self.element_parse(element_selectors[0], response, result_item, response.url)
        elif detail_selectors:
            detail_urls = self.detail_resolve(detail_selectors[0], response, response.url)
            # 子选择器
            child_selectors = [i for i in self.selectors if i["parentSelectors"] == detail_selectors[0]['name']]
            if not detail_urls or not child_selectors:
                yield result_item
            else:
                yield from self.detail_parse(detail_selectors[0], detail_urls[:1], child_selectors, result_item)
        else:
            yield result_item

    def text_resolve(self, selectorText, response):
        """文本类型解析"""
        selector = getattr(response,selectorText["method"])
        text = selector(selectorText["selector"]).extract()
        if '::attr' not in selectorText["selector"]:
            text = [re.sub('<[\s\S]*?>', '', i) for i in text]
        text = [i.strip() for i in text]
        return text

    def image_resolve(self, selectorImage, response, response_url):
        """图片类型解析"""
        if selectorImage["method"] == "css":
            if '::attr' in selectorImage["selector"]:
                images = response.css(selectorImage["selector"]).extract()
            else:
                images = response.css(selectorImage["selector"] + "::attr(src)").extract()
        else:
            if selectorImage["selector"].endswith("/@src"):
                images = response.xpath(selectorImage["selector"]).extract()
            else:
                images = response.xpath(selectorImage["selector"] + "/@src").extract()
        new_images = []
        # 替换完整路径
        for image in images:
            if image.startswith('javascript'):
                continue
            # image = urllib.parse.urljoin(self.start_urls[0], image.strip())
            image = urllib.parse.urljoin(response_url, image.strip())
            new_images.append(image)
        return new_images

    def attribute_resolve(self, selectorElementAttribute, response):
        """element属性类型解析"""
        attribute = response.css(selectorElementAttribute["selector"] + "::attr(%s)" % selectorElementAttribute[
            "extractAttribute"]).extract()
        attribute = [i.strip() for i in attribute]
        return attribute

    def html_resolve(self, selectorHTML, response):
        """html类型解析"""
        selector = getattr(response, selectorHTML["method"])
        html = selector(selectorHTML["selector"]).extract()
        html = [i.strip() for i in html]
        return html

    def link_resolve(self, selectorLink, response):
        """翻页类型解析"""
        # 正则表达式优先于选择器
        if selectorLink['regex'] and re.findall('(\(.+?\))(.+)', selectorLink['regex']):
            pagerange, regex = re.findall('(\(.+?\))(.+)', selectorLink['regex'])[0]
            return pagerange, regex
        if selectorLink["method"] == 'css':
            link = response.css(selectorLink["selector"] + "::attr(href)").extract()
        else:
            link = response.xpath(selectorLink["selector"] + "/@href").extract()
        if not link or link[0].startswith('javascript'):
            return ""
        link = urllib.parse.urljoin(response.url, link[0].strip())
        return link
