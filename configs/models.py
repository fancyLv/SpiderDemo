# -*- coding: utf-8 -*-
from django.db import models
from jsonfield import JSONField


class Rule(models.Model):
    name = models.CharField(unique=True, max_length=30, verbose_name='名称')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '规则'
        verbose_name_plural = '规则配置'


class Seed(models.Model):
    METHOD_GET = 'get'
    METHOD_POST = 'post'
    METHOD_CHOIXES = (
        (METHOD_GET, 'GET'),
        (METHOD_POST, 'POST')
    )
    name = models.CharField(unique=True, max_length=100, verbose_name='名称')
    rule = models.ForeignKey(Rule, verbose_name='使用规则')
    start_urls = models.TextField(verbose_name='起始url')
    method = models.CharField(max_length=6, default=METHOD_GET, choices=METHOD_CHOIXES, verbose_name='请求方法')
    headers = JSONField(default={
        'User_Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'},
        blank=True, null=True, verbose_name='headers参数')
    cookies = JSONField(blank=True, null=True, verbose_name='cookies参数')
    form_data = JSONField(blank=True, null=True, verbose_name='form-data参数')
    proxy = models.BooleanField(verbose_name='启用代理')
    dynamic = models.BooleanField(verbose_name='启用浏览器')
    download_delay = models.PositiveSmallIntegerField(default=0, verbose_name='访问间隔(秒)')
    concurrent_requests = models.PositiveSmallIntegerField(default=1, verbose_name='并发数量')

    crawl_time = models.DateTimeField(blank=True, null=True,verbose_name='下次爬取时间')
    frequency = models.IntegerField(default=86400,verbose_name='爬取频率(秒)')

    status = models.BooleanField(default=False, verbose_name='是否启用')

    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '种子'
        verbose_name_plural = '种子配置'


class Selector(models.Model):
    SELECTOR_CHOICES = (
        ('SelectorText', '文本选择器'),
        ('SelectorLink', '翻页选择器'),
        ('SelectorDetail', '详情页选择器'),
        ('SelectorHTML', 'html选择器'),
        ('SelectorElement', '元素集选择器'),
        ('SelectorImage', '图片选择器'),
        # ('SelectorElementAttribute', '元素属性选择器')
    )
    METHOD_CHOICES = (('css', 'CSS'), ('xpath', 'XPATH'))
    rid = models.ForeignKey(to='Rule', to_field='id', related_name='rule_id')
    parent = models.ForeignKey("self", blank=True, null=True, related_name='parent_selector', verbose_name='父选择器')
    name = models.CharField(max_length=30, verbose_name='字段名称')
    type = models.CharField(max_length=25, default='SelectorText', choices=SELECTOR_CHOICES, verbose_name='字段类型')
    multiple = models.BooleanField(verbose_name='多元素')
    method = models.CharField(max_length=5, default='css', choices=METHOD_CHOICES, verbose_name='定位方法')
    selector = models.CharField(max_length=100, verbose_name='选择器')
    regex = models.CharField(blank=True, null=True, max_length=100, verbose_name='正则过滤')

    # attribute = models.CharField(blank=True, null=True, max_length=20, verbose_name='属性名称')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '选择器'
        verbose_name_plural = '选择器'
