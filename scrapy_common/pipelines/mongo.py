# -*- coding: utf-8 -*-
# @File    : mongo.py
# @Author  : LVFANGFANG
# @Time    : 2018/6/19 0019 16:46
# @Desc    :

import datetime

import pymongo


class ScrapyCommonPipeline(object):
    def process_item(self, item, spider):
        return item


class MongoDBPipeline(object):
    '''
    保存至mongodb
    '''

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'spider'),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        item['download_time'] = datetime.datetime.utcnow()  # datetime.datetime.now()
        self.db[spider.name].insert(dict(item))
        return item
