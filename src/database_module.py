# -*- encoding: utf-8 -*-
'''
@File    :   database_module.py
@Time    :   2022/11/23
@Author  :   ATANG_
@Version :   2.0
@Desc    :   数据库模块
'''

import datetime
import re
import time

from pymongo import MongoClient
from urllib.parse import quote_plus

import log_module as log


class MongoDB(object):

    def __init__(self,
                 database='bit_secretary',
                 host='localhost',
                 port=27017,
                 collection='test',
                 user='admin',
                 password='liyulin6749901!'
                 ):
        uri = "mongodb://%s:%s@%s:%d" % (quote_plus(user),
                                         quote_plus(password), host, port)
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
        self.log_db = LogDB()

    def _save_template(self, name, template, user='_user'):

        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def create_data():
            return {'name': name, 'template': template, 'datetime': get_datetime()}

        if user == '_user':  # 游客无存储模板权限
            return

        new_template = create_data()
        if self.mdb.is_exist({'user': user}):
            data = self.mdb.find({'user': user})[0]
            for t in data['templates']:
                if t['name'] == name:
                    data['templates'].remove(t)
                    data['templates'].append(new_template)
                    self.mdb.update({'user': user}, data)
                    log.INFO("用户 {} 已更新文档模板: {}".format(user, name))
                    self.log_db.store_log("更新文档模板: {}".format(name), user)
                    break
            else:
                data['templates'].append(new_template)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已添加文档模板: {}".format(user, name))
                self.log_db.store_log("添加文档模板: {}".format(name), user)
        else:
            self.mdb.insert({'user': user, 'templates': [new_template]})
            log.INFO("用户 {} 已添加文档模板: {}".format(user, name))
            self.log_db.store_log("添加文档模板: {}".format(name), user)

    def load_template(self, name, user='_user'):
        if not self.mdb.is_exist({'user': user}):
            log.INFO("用户 {} 无文档模板集".format(user))
            return ""

        data = self.mdb.find({'user': user})[0]
        for t in data['templates']:
            if t['name'] == name:
                template = t['template']
                log.INFO("已加载用户 {} 的文档模板: {}".format(user, name))
                self.log_db.store_log("加载文档模板: {}".format(name), user)
                return template

        log.ERROR("用户 {} 不存在文档模板: {}".format(user, name))
        return ""

    def delete_template(self, name, user='_user'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 无文档模板集".format(user)
            log.INFO(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for t in data['templates']:
            if t['name'] == name:
                data['templates'].remove(t)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已删除文档模板: {}".format(user, name))
                self.log_db.store_log("删除文档模板: {}".format(name), user)
                return "OK"

        message = "用户 {} 不存在文档模板: {}".format(user, name)
        log.ERROR(message)
        return message

    def clear_templates(self, user='_user'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 无文档模板集".format(user)
            log.INFO(message)
            return message

        data = self.mdb.find({'user': user})[0]
        data['templates'] = []
        self.mdb.update({'user': user}, data)
        log.INFO('用户 {} 已清空文档模板集'.format(user))
        self.log_db.store_log("清空文档模板", user)
        return "OK"

    def show_templates(self, user='_user'):
        if not self.mdb.is_exist({'user': user}):
            log.INFO("用户 {} 无文档模板集".format(user))
            return []

        data = self.mdb.find({'user': user})[0]
        templates = [{'name': t['name'], 'datetime':t['datetime']}
                     for t in data['templates']]
        log.INFO('用户 {} 文档模板集: {}'.format(user, templates))
        result = {'templates': templates}
        return result


class UserDictDB(object):
    """ 用户词典 -
    """

    user_dict_type = {
        "sensitive": "敏感词",
        "entity": "实体",
        "desensity": "脱敏",
    }

    def __init__(self):
        self.mdb = MongoDB(collection='user_dict')
        self.log_db = LogDB()

    def add_userdict(self, name, lang_type, paths, dict_type='sensitive', user='_user'):

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
                    self.log_db.store_log("更新{}词典: {}".format(
                        UserDictDB.user_dict_type[dict_type], name), user)
                    break
            else:
                data[dict_type].append(new_data)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已添加{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], name))
                self.log_db.store_log("添加{}词典: {}".format(
                    UserDictDB.user_dict_type[dict_type], name), user)
        else:
            new_user_data = {'user': user, 'sensitive': [], 'entity': [], 'desensity': []}
            new_user_data[dict_type].append(new_data)
            self.mdb.insert(new_user_data)
            log.INFO("用户 {} 已添加{}词典: {}".format(
                user, UserDictDB.user_dict_type[dict_type], name))
            self.log_db.store_log("添加{}词典: {}".format(
                UserDictDB.user_dict_type[dict_type], name), user)
        return "OK"

    def select_userdict(self, config, dict_type='sensitive', user='_user'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 无词典集".format(user)
            log.INFO(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for item in config:
            for d in data[dict_type]:
                if item['name'] == d['name']:
                    d['checked'] = int(item['checked'])
                    self.mdb.update({'user': user}, data)
                    if d['checked'] == 1:
                        log.INFO("用户 {} 已选中使用{}词典: {}".format(
                            user, UserDictDB.user_dict_type[dict_type], item['name']))
                        self.log_db.store_log("选中使用{}词典: {}".format(
                            UserDictDB.user_dict_type[dict_type], item['name']), user)
                    else:
                        log.INFO("用户 {} 已取消使用{}词典: {}".format(
                            user, UserDictDB.user_dict_type[dict_type], item['name']))
                        self.log_db.store_log("取消使用{}词典: {}".format(
                            UserDictDB.user_dict_type[dict_type], item['name']), user)
                    break
            else:
                log.ERROR("用户 {} 不存在{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], item['name']))

        log.INFO("已完成用户 {} 的{}词典配置".format(
            user, UserDictDB.user_dict_type[dict_type]))
        return "OK"

    def _load_userdict(self, dict_type='sensitive', user='_user'):
        if not self.mdb.is_exist({'user': user}):
            log.INFO("用户 {} 无词典集".format(user))
            return []

        user_dict = []
        data = self.mdb.find({'user': user})[0]
        if dict_type == 'sensitive' or dict_type == 'desensity':
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

    def delete_userdict(self, name, dict_type='sensitive', user='_user'):
        if not self.mdb.is_exist({'user': user}):
            message = "用户 {} 无词典集".format(user)
            log.INFO(message)
            return message

        data = self.mdb.find({'user': user})[0]
        for d in data[dict_type]:
            if d['name'] == name:
                data[dict_type].remove(d)
                self.mdb.update({'user': user}, data)
                log.INFO("用户 {} 已删除{}词典: {}".format(
                    user, UserDictDB.user_dict_type[dict_type], name))
                self.log_db.store_log("删除{}词典: {}".format(
                    UserDictDB.user_dict_type[dict_type], name), user)
                return "OK"

        message = "用户 {} 不存在{}词典: {}".format(
            user, UserDictDB.user_dict_type[dict_type], name)
        log.ERROR(message)
        return message

    def show_userdict(self, dict_type='sensitive', user='_user'):
        if not self.mdb.is_exist({'user': user}):
            log.INFO("用户 {} 无词典集".format(user))
            return {'data': []}

        data = self.mdb.find({'user': user})[0]
        dicts = [{'name': d['name'], 'datetime': d['datetime'],
                  'lang_type': d['lang_type'], 'size': d['size'], 'checked': d['checked']} for d in data[dict_type]]
        log.INFO('用户 {} {}词典集: {}'.format(
            user, UserDictDB.user_dict_type[dict_type], dicts))
        return {'data': dicts}


class UserManageDB(object):
    """ 用户管理 -
    """

    # module_e2c = {
    #     "reading": "智能阅读",
    #     "learn_template": "模板学习",
    #     "show_templates": "模板展示",
    #     "load_template": "模板加载",
    #     "delete_template": "模板删除",
    #     "show_user_dict": "获取词典列表",
    #     "add_user_dict": "添加词典",
    #     "delete_user_dict": "删除词典",
    #     "select_user_dict": "选择词典",
    # }

    def __init__(self):
        self.mdb = MongoDB(collection='user_manage')
        self.log_db = LogDB()

    def register(self, user, password):
        """ 注册 -
        """

        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def create_data():
            return {'user': user, 'password': password, 'datetime': get_datetime(),
                    'permission': {
                        'reading': 1,
                        'learn_template': 1,
                        'show_templates': 1,
                        'load_template': 1,
                        'delete_template': 1,
                        'show_user_dict': 0,
                        'add_user_dict': 0,
                        'delete_user_dict': 0,
                        'select_user_dict': 0,
            }}

        if not bool(re.match("^[A-Za-z0-9_]*$", user)):
            message = "注册失败，用户名不合法"
            return {'state': -1, 'message': message}
        # if password != password_ack:
        #     message = "注册失败，两次输入密码不一致"
        #     return {'state': -1, 'message': message}
        if self.mdb.is_exist({'user': user}):
            message = "注册失败，用户名已被占用"
            return {'state': -1, 'message': message}
        if not password:
            message = "注册失败，密码不能为空"
            return {'state': -1, 'message': message}

        new_user = create_data()
        self.mdb.insert(new_user)
        log.INFO("已注册新用户: {}, 密码: {}".format(user, password))

        message = "注册成功"
        self.log_db.store_log(message, user)
        return {'state': 0, 'message': message}

    def cancel(self, user):
        """ 注销 -
        """

        if not self.mdb.is_exist({'user': user}):
            message = "注销失败，用户不存在"
            return {'state': -1, 'message': message}

        self.mdb.delete({'user': user})
        self.log_db.clear_logs(user)
        log.INFO("已注销用户 {}".format(user))
        message = "注销成功"
        return {'state': 0, 'message': message}

    def login(self, user, password):
        """ 登录 -
        """

        if not self.mdb.is_exist({'user': user}):
            message = "登录失败，用户名不存在"
            return {'state': -1, 'message': message}
        if not password:
            message = "登录失败，密码不能为空"
            return {'state': -1, 'message': message}
        user_data = self.mdb.find({'user': user})[0]
        if user_data['password'] != password:
            message = "登录失败，用户名或密码错误"
            return {'state': -1, 'message': message}

        message = "登录成功"
        self.log_db.store_log(message, user)
        return {'state': 0, 'message': message}

    def update_password(self, user, password):
        """ 修改密码 -
        """

        if not self.mdb.is_exist({'user': user}):
            message = "修改失败，用户名不存在"
            return {'state': -1, 'message': message}
        if not password:
            message = "修改失败，密码不能为空"
            return {'state': -1, 'message': message}

        user_data = self.mdb.find({'user': user})[0]
        user_data['password'] = password
        self.mdb.update({'user': user}, user_data)
        log.INFO("用户 {} 已修改密码: {}".format(user, password))

        self.log_db.store_log("修改密码: {}".format(password), user)
        message = "修改成功"
        return {'state': 0, 'message': message}

    # def view_permission(self, user='_user'):
    #     """ 查看用户权限
    #     """

    #     user_data = self.mdb.find({'user': user})[0]
    #     permission = user_data['permission']
    #     return permission

    # def update_permission(self, config, user='_user'):
    #     """ 修改用户权限

    #     :param config: [{'module':'reading', 'value':1}]
    #     """

    #     if not self.mdb.is_exist({'user': user}):
    #         message = "修改用户权限失败，用户不存在"
    #         return {'state': -1, 'message': message}

    #     user_data = self.mdb.find({'user': user})[0]
    #     for item in config:
    #         user_data['permission'][item['module']] = int(item['value'])
    #         if int(item['value']) == 1:
    #             log.INFO("已授权用户 {} {}功能".format(
    #                 user, UserManageDB.module_e2c[item['module']]))
    #         elif int(item['value']) == 0:
    #             log.INFO("已禁用用户 {} {}功能".format(
    #                 user, UserManageDB.module_e2c[item['module']]))

    #     log.INFO("已完成用户 {} 的权限配置".format(user))
    #     message = "修改用户权限成功"
    #     return {'state': 0, 'message': message}


class LogDB(object):
    """ 日志 -
    """

    def __init__(self):
        self.mdb = MongoDB(collection='user_log')

    def view_logs(self, keyword='', s_time='', e_time='', user='_user'):

        def get_timestamp(date):
            return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp()

        if user == '_user':
            return []

        if not self.mdb.is_exist({'user': user}):
            log.INFO("查询日志失败，用户 {} 不存在".format(user))
            return []

        data = self.mdb.find({'user': user})[0]
        logs = data['logs']
        if keyword:
            logs = [log for log in logs if keyword in log]
        if s_time:
            s_time = time.strptime(s_time, "%Y-%m-%d %H:%M:%S")
            logs = [log for log in logs if time.strptime(
                log.split('|')[0], "%Y-%m-%d %H:%M:%S") >= s_time]
        if e_time:
            e_time = time.strptime(e_time, "%Y-%m-%d %H:%M:%S")
            logs = [log for log in logs if time.strptime(
                log.split('|')[0], "%Y-%m-%d %H:%M:%S") < e_time]
        logs = sorted(logs, key=lambda log: get_timestamp(
            log.split('|')[0]), reverse=True)
        return logs

    def clear_logs(self, user='user'):
        if user == '_user':
            return

        if self.mdb.is_exist({'user': user}):
            self.mdb.delete({'user': user})

    def store_log(self, log: str, user='user'):

        def get_datetime():
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def create_data():
            return "{}| {}".format(get_datetime(), log)

        if user == '_user':
            return

        new_data = create_data()
        if not self.mdb.is_exist({'user': user}):
            self.mdb.insert({'user': user, 'logs': [new_data]})
        else:
            data = self.mdb.find({'user': user})[0]
            data['logs'].append(new_data)
            self.mdb.update({'user': user}, data)


if __name__ == '__main__':
    pass
