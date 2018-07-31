from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from .models import Seed, Rule, Selector
from pprint import pprint
import json
import re
import time

from scrapy.crawler import CrawlerProcess, CrawlerRunner

from scrapy_common.spiders.example import ExampleSpider
from scrapy.utils.project import get_project_settings


class SelectorInline(admin.TabularInline):
    model = Selector
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent' and re.findall('\d+', request.path):
            kwargs['queryset'] = Selector.objects.filter(rid=re.findall('\d+', request.path)[0])
        return super(SelectorInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'update_time')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    inlines = [SelectorInline]


@admin.register(Seed)
class SeedAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'crawl_time')
    list_display_links = ('id', 'name')
    list_filter = ('status',)
    search_fields = ('name',)
    list_editable = ('status',)
    actions = ['copy_objects']

    def copy_objects(self, request, queryset):
        for obj in queryset.values():
            obj.pop('id')
            obj['name'] = obj['name'] + str(int(time.time()))
            Seed.objects.create(**obj)

    copy_objects.short_description = "复制所选的 种子配置"


admin.site.site_header = '爬虫系统'
admin.site.site_title = '爬虫系统'
