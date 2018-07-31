# -*- coding: utf-8 -*-
# @File    : scheduler.py
# @Author  : LVFANGFANG
# @Time    : 2018/7/29 0029 23:05
# @Desc    :

import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SpiderDemo.settings")  # project_name 项目名称
django.setup()
import json
from pprint import pprint
from datetime import timedelta
from configs.models import Seed, Selector


class Scheduler:
    def run(self):
        while True:
            # now = datetime.now()
            now = django.utils.timezone.now()
            for seed in Seed.objects.filter(status=True, crawl_time__lte=now):
                seedid = seed.id
                p = os.system(f"python3 run.py {seedid}")

                print('alter time !')
                seed.crawl_time = now + timedelta(seconds=seed.frequency)
                # seed.save()


if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.run()
