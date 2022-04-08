# -*- encoding: utf-8 -*-
'''
@File    :   database_module.py
@Time    :   2022/03/24
@Author  :   ATANG_
@Version :   1.0
@Desc    :   文档模板数据库模块
'''

import time

from pymongo import MongoClient

import log_module as log


class MongoDB(object):

    def __init__(self, 
                 database = 'bit_secretary',
                 host = 'localhost',
                 port = 27017,
                 collection = 'user1',
                ):
        self._client = MongoClient(host, port)
        self._db = self._client[database]
        self._col = self._db[collection]

    def insert(self, data):
        if data == None:
            return
        elif isinstance(data, dict):
            self._col.insert_one(data)
        elif isinstance(data, list):
            self._col.insert_many(data)

    def update(self, data, new_data, single = True):
        if data == None or new_data == None:
            return
        if single:
            self._col.update_one(data, {'$set':new_data})
        else:
            self._col.update_many(data, {'$set':new_data})

    def delete(self, data, single = True):
        if data == None:
            return
        if single:
            self._col.delete_one(data)
        else:
            self._col.delete_many(data)

    def find(self, data, single = True):
        if data == None:
            return []
        if single:
            res = [self._col.find_one(data)]
        else:
            res = list(self._col.find(data))
        return res

    def sort(self, key = 'datetime'):
        res = self._col.find().sort(key)
        return list(res)

    def is_exist(self, data):
        return bool(list(self._col.find(data)))

    def clear(self):
        self._col.delete_many({})


class DocTemplateDB(object):

    def __init__(self, 
                 host = 'localhost',
                 port = 27017,
                 user = 'user1'):
        self.mdb = MongoDB(host=host, port=port, collection=user) 

    def save_template(self, name, template):
        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        def create_data():
            return {'name':name, 'template':template, 'datetime':get_datetime()}

        new_data = create_data()
        if self.mdb.is_exist({'name':name}):
            self.mdb.update({'name':name}, new_data)
            log.INFO('已更新文档模板: {}'.format(name))
        else:
            self.mdb.insert(new_data)
            log.INFO('已存储新的文档模板: {}'.format(name))

    def load_template(self, name):
        if not self.mdb.is_exist({'name':name}):
            log.ERROR('不存在的文档模板: {}'.format(name))
            return None
        else:
            templates = self.mdb.find({'name':name})
            return templates[0]

    def delete_template(self, name):
        if not self.mdb.is_exist({'name':name}):
            log.ERROR('不存在的文档模板: {}'.format(name))
        else:
            self.mdb.delete({'name':name})
            log.INFO('已删除文档模板: {}'.format(name))

    def clear_template(self):
        self.mdb.clear()
        log.INFO('已清空文档集合')

    def show_templates(self):
        templates = self.mdb.sort()
        log.INFO(templates)


if __name__ == '__main__':
    mdb = DocTemplateDB()
    t = 'template'
    mdb.save_template('泰安市政府报告模板', t)
    t = mdb.load_template('泰安市政府报告模板')
    print(t['template'])
    t = mdb.delete_template('泰安市政府报告模板')