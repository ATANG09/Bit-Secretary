# -*- encoding: utf-8 -*-
'''
@File    :   database_module.py
@Time    :   2022/11/23
@Author  :   ATANG_
@Version :   2.0
@Desc    :   数据库模块
'''

import time

from pymongo import MongoClient
from urllib.parse import quote_plus

import log_module as log


class MongoDB(object):

    def __init__(self, 
                 database = 'bit_secretary',
                 host = 'localhost',
                 port = 27017,
                 collection = 'user1',
                 user = 'admin',
                 password = 'liyulin6749901!'
                ):
        uri = "mongodb://%s:%s@%s:%d" % (quote_plus(user), quote_plus(password), host, port)
        self._client = MongoClient(uri)
        self._db = self._client[database]
        self._col = self._db[collection]

    def insert(self, data):
        if data == None:
            return
        elif isinstance(data, dict):
            self._col.insert_one(data)
        elif isinstance(data, list):
            self._col.insert_many(data)

    def update(self, data, new_data, single=True):
        if data == None or new_data == None:
            return
        if single:
            self._col.update_one(data, {'$set': new_data})
        else:
            self._col.update_many(data, {'$set': new_data})

    def delete(self, data, single=True):
        if data == None:
            return
        if single:
            self._col.delete_one(data)
        else:
            self._col.delete_many(data)

    def find(self, data, single=True):
        if data == None:
            return []
        if single:
            res = [self._col.find_one(data)]
        else:
            res = list(self._col.find(data))
        return res

    def is_exist(self, data):
        return bool(list(self._col.find(data)))


class DocTemplateDB(object):
    """ 文档模板 -
    """

    def __init__(self):

        self.mdb = MongoDB(collection='doc_template')

    def save_template(self, name, template, user='user1'):

        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def create_data():
            return {'name': name, 'template': template, 'datetime': get_datetime()}

        new_template = create_data()
        if self.mdb.is_exist({'user': user}):
            data = self.mdb.find({'user': user})[0]
            for t in data['templates']:
                if t['name'] == name:
                    data['templates'].remove(t)
                    data['templates'].append(new_template)
                    self.mdb.update({'user': user}, data)
                    log.INFO("用户 {} 已更新文档模板: {}".format(user, name))
                    break
            else:
                data['templates'].append(new_template)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已添加文档模板: {}".format(user, name))
        else:
            self.mdb.insert({'user': user, 'templates': [new_template]})
            log.INFO("已存储新用户 {} 的文档模板: {}".format(user, name))

    def load_template(self, name, user='user1'):
        if not self.mdb.is_exist({'user': user}):
            log.ERROR("用户 {} 不存在".format(user))
            return ""

        data = self.mdb.find({'user': user})[0]
        for t in data['templates']:
            if t['name'] == name:
                template = t['template']
                log.INFO("已加载用户 {} 的文档模板: {}".format(user, name))
                return template

        log.ERROR("用户 {} 不存在文档模板: {}".format(user, name))
        return ""

    def delete_template(self, name, user='user1'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 不存在".format(user)
            log.ERROR(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for t in data['templates']:
            if t['name'] == name:
                data['templates'].remove(t)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已删除文档模板: {}".format(user, name))
                return "OK"

        message = "用户 {} 不存在文档模板: {}".format(user, name)
        log.ERROR(message)
        return message

    def clear_templates(self, user='user1'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 不存在".format(user)
            log.ERROR(message)
            return message

        data = self.mdb.find({'user': user})[0]
        data['templates'] = []
        self.mdb.update({'user': user}, data)
        log.INFO('用户 {} 已清空文档模板集'.format(user))
        return "OK"

    def show_templates(self, user='user1'):
        if not self.mdb.is_exist({'user': user}):
            log.ERROR("用户 {} 不存在".format(user))
            return []

        data = self.mdb.find({'user': user})[0]
        templates = [{'name': t['name'], 'datetime':t['datetime']}
                     for t in data['templates']]
        log.INFO('用户 {} 文档模板集: {}'.format(user, templates))
        return templates


class UserDictDB(object):
    """ 用户词典 -
    """

    user_dict_type = {
        "sensitive": "敏感词",
        "entity": "实体"
    }

    def __init__(self):

        self.mdb = MongoDB(collection='user_dict')

    def add_userdict(self, name, lang_type, paths, dict_type='sensitive', user='user1'):

        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def create_data():
            words = []
            for path in paths:
                data = open(path, 'r', encoding='utf-8').readlines()
                data = [w.strip() for w in data if w.strip()]
                words.extend(data)
            words = list(set(words))
            size = len(words)
            return {'name': name, 'lang_type': lang_type,
                    'size': size, 'words': words, 'datetime': get_datetime(), 'checked': 0}

        new_data = create_data()
        if self.mdb.is_exist({'user': user}):
            data = self.mdb.find({'user': user})[0]
            for d in data[dict_type]:
                if d['name'] == name:
                    data[dict_type].remove(d)
                    data[dict_type].append(new_data)
                    self.mdb.update({'user': user}, data)
                    log.INFO("用户 {} 已更新{}词典: {}".format(
                        user, UserDictDB.user_dict_type[dict_type], name))
                    break
            else:
                data[dict_type].append(new_data)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已添加{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], name))
        else:
            new_user_data = {'user': user, 'sensitive': [], 'entity': []}
            new_user_data[dict_type].append(new_data)
            self.mdb.insert(new_user_data)
            log.INFO("已存储新用户 {} 的{}词典: {}".format(
                user, UserDictDB.user_dict_type[dict_type], name))
        return "OK"

    def select_userdict(self, config, dict_type='sensitive', user='user1'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 不存在".format(user)
            log.ERROR(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for item in config:
            for d in data[dict_type]:
                if item['name'] == d['name']:
                    d['checked'] = int(item['checked'])
                    self.mdb.update({'user': user}, data)
                    if d['checked'] == 1:
                        log.INFO("用户 {} 已选中{}词典: {}".format(
                            user, UserDictDB.user_dict_type[dict_type], item['name']))
                    else:
                        log.INFO("用户 {} 已取消使用{}词典: {}".format(
                            user, UserDictDB.user_dict_type[dict_type], item['name']))
                    break
            else:
                log.ERROR("用户 {} 不存在{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], item['name']))

        log.INFO("已完成用户 {} 的{}词典配置".format(
            user, UserDictDB.user_dict_type[dict_type]))
        return "OK"

    def _load_userdict(self, dict_type='sensitive', user='user1'):
        if not self.mdb.is_exist({'user': user}):
            log.ERROR("用户 {} 不存在".format(user))
            return []

        user_dict = []
        data = self.mdb.find({'user': user})[0]
        if dict_type == 'sensitive':
            for d in data[dict_type]:
                if d['checked'] == 1:
                    user_dict.extend(d['words'])
            user_dict = list(set(user_dict))
        elif dict_type == 'entity':
            for d in data[dict_type]:
                if d['checked'] == 1:
                    user_dict.append({'name': d['name'], 'words': d['words']})

        log.INFO('已加载用户 {} 的{}词典: {}'.format(
            user, UserDictDB.user_dict_type[dict_type], user_dict))
        return user_dict

    def delete_userdict(self, name, dict_type='sensitive', user='user1'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 不存在".format(user)
            log.ERROR(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for d in data[dict_type]:
            if d['name'] == name:
                data[dict_type].remove(d)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已删除{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], name))
                return "OK"

        message = "用户 {} 不存在{}词典: {}".format(
            user, UserDictDB.user_dict_type[dict_type], name)
        log.ERROR(message)
        return message

    def show_userdict(self, dict_type='sensitive', user='user1'):
        if not self.mdb.is_exist({'user': user}):
            log.ERROR("用户 {} 不存在".format(user))
            return {'data': []}

        data = self.mdb.find({'user': user})[0]
        dicts = [{'name': d['name'], 'datetime': d['datetime'],
                  'lang_type': d['lang_type'], 'size': d['size'], 'checked': d['checked']} for d in data[dict_type]]
        log.INFO('用户 {} {}词典集: {}'.format(
            user, UserDictDB.user_dict_type[dict_type], dicts))
        return {'data': dicts}


if __name__ == '__main__':
    pass
