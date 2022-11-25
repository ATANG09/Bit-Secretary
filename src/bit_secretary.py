# -*- encoding: utf-8 -*-
'''
@File    :   bit_secretary.py
@Time    :   2022/11/23
@Author  :   ATANG_
@Version :   2.0
@Desc    :   比特秘书主程序
'''

import json
import os

from flask import Flask, request, send_file
from flask_cors import CORS

from database_module import UserManageDB, DocTemplateDB, UserDictDB
from learn_module import DocLearnModule
import log_module as log
from quote_module import PromptWritingModule
from reading_module import SmartReading
from STI_module import STIModule


app = Flask(__name__)
CORS(app, supports_credentials=True)

CACHE_DIR = './cache/upload/'

HEADER_CONFIG = [('Access-Control-Allow-Origin', '*')]


"""  ****************** 模板学习 ******************
"""

# 模板学习
@app.route('/learn_template', methods=['POST'])
def learn_template():
    name = request.form.get('template_name')
    doc_type = request.form.get('doc_type')
    username = request.form.get('username')
    upload_files = request.files.getlist('doc_files')
    doc_paths = []
    for file in upload_files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'learn_template/', filename)
        file.save(filepath)
        doc_paths.append(filepath)

    log.INFO('模板名称: {}'.format(name))
    template = doc_learn.learn_docs(doc_type, doc_paths)
    doc_template_db._save_template(name, template, username)
    result = json.dumps(template)
    return result, 200, HEADER_CONFIG


# 模板展示
@app.route('/show_templates', methods=['GET', 'POST'])
def show_templates():
    username = request.form.get('username')
    templates = doc_template_db.show_templates(username)
    result = json.dumps(templates)
    return result, 200, HEADER_CONFIG


# 模板加载
@app.route('/load_template', methods=['POST'])
def load_template():
    template_name = request.form.get('template_name')
    username = request.form.get('username')
    log.INFO('模板名称: {}'.format(template_name))

    template = doc_template_db.load_template(template_name, username)
    result = json.dumps(template)
    return result, 200, HEADER_CONFIG


# 模板删除
@app.route('/delete_template', methods=['POST'])
def delete_template():
    template_name = request.form.get('template_name')
    username = request.form.get('username')
    message = doc_template_db.delete_template(template_name, username)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 模板清空
@app.route('/clear_templates', methods=['GET', 'POST'])
def clear_templates():
    username = request.form.get('username')
    message = doc_template_db.clear_templates(username)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


"""  ****************** 提示写作 *****************
"""

# 提示写作
@app.route('/prompt_write', methods=['POST'])
def prompt_write():
    text = request.form.get('prompt_write_inputs')
    if len(text.strip()) == 0:
        log.ERROR('提示写作输入为空')
        return "", 200, HEADER_CONFIG

    log.INFO("提示写作输入: {}".format(text))
    result = prompt_writing.prompt_writing(text)
    log.INFO("提示写作结果: {}".format(result))
    return result, 200, HEADER_CONFIG


"""  ****************** 智能阅读 *****************
"""

# 智能阅读
@app.route('/reading', methods=['POST'])
def reading():
    text = request.form.get('text')
    method = request.form.get('method')
    username = request.form.get('username')
    if not text:
        log.ERROR('阅读文本为空')
        return "", 200, HEADER_CONFIG

    log.INFO("阅读文本: {}".format(text))
    log.INFO("阅读功能: {}".format(method))
    result = smart_reading.smart_reading(text, method, username)
    if method != 'sentiment_analysis':
        log.INFO("智能阅读结果: {}".format(result))
    return result, 200, HEADER_CONFIG


# 获取词典列表
@app.route('/show_user_dict', methods=['POST'])
def show_user_dict():
    dict_type = request.form.get('dict_type')
    username = request.form.get('username')
    result = json.dumps(user_dict_db.show_userdict(dict_type, username))
    return result, 200, HEADER_CONFIG


# 添加词典
@app.route('/add_user_dict', methods=['POST'])
def add_user_dict():
    name = request.form.get('name')
    lang_type = request.form.get('lang_type')
    dict_type = request.form.get('dict_type')
    username = request.form.get('username')
    files = request.files.getlist('files')
    paths = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'user_dict/', filename)
        file.save(filepath)
        paths.append(filepath)

    message = user_dict_db.add_userdict(
        name, lang_type, paths, dict_type, username)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 删除词典
@app.route('/delete_user_dict', methods=['POST'])
def delete_user_dict():
    name = request.form.get('name')
    dict_type = request.form.get('dict_type')
    username = request.form.get('username')
    message = user_dict_db.delete_userdict(name, dict_type, username)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 用户选择使用的词典
@app.route('/select_user_dict', methods=['POST'])
def select_user_dict():
    data = json.loads(request.form.get('data'))
    dict_type = request.form.get('dict_type')
    username = request.form.get('username')
    message = user_dict_db.select_userdict(data, dict_type, username)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


"""  ****************** 写作分析 ******************
"""


"""  ****************** 科技情报 ******************
"""

# 情报分析与报告生成
@app.route('/STI', methods=['POST'])
def STI():
    upload_files = request.files.getlist('doc_files')
    doc_paths = []
    for file in upload_files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'sti/', filename)
        file.save(filepath)
        doc_paths.append(filepath)
    log.INFO('情报文档列表: {}'.format(doc_paths))

    sti.STI_manager(doc_paths)
    return send_file('../cache/STI/网络信息参考.docx'), 200, HEADER_CONFIG


"""  ****************** 用户管理 ******************
"""

# 用户注册（登出）
@app.route('/user_register', methods=['POST'])
def user_register():
    username = request.form.get('username')
    password = request.form.get('password')
    result = json.dumps(user_db.register(username, password))
    return result, 200, HEADER_CONFIG


# 用户注销（登入）
@app.route('/user_cancel', methods=['POST'])
def user_cancel():
    username = request.form.get('username')
    result = json.dumps(user_db.cancel(username))
    return result, 200, HEADER_CONFIG


# 用户登录（登出）
@app.route('/user_login', methods=['POST'])
def user_login():
    username = request.form.get('username')
    password = request.form.get('password')
    result = json.dumps(user_db.login(username, password))
    return result, 200, HEADER_CONFIG


# 修改密码（登入）
@app.route('/update_password', methods=['POST'])
def update_password():
    username = request.form.get('username')
    password = request.form.get('password')
    result = json.dumps(user_db.update_password(username, password))
    return result, 200, HEADER_CONFIG


# 查看用户权限
# @app.route('/view_permission', methods=['POST'])
# def view_permission():
#     username = request.form.get('username')
#     result = json.dumps(user_db.view_permission(username))
#     return result, 200, HEADER_CONFIG


# 更新用户权限
# @app.route('/update_permission', methods=['POST'])
# def update_permission():
#     username = request.form.get('username')
#     data = json.loads(request.form.get('data'))
#     result = json.dumps(user_db.update_permission(data, username))
#     return result, 200, HEADER_CONFIG


if __name__ == '__main__':
    user_db = UserManageDB()
    user_db.register('_user', '123456') # 注册游客
    log.INFO(' 用户管理数据库模块加载完成 '.center(20, '*'))
    doc_learn = DocLearnModule()
    log.INFO(' 模板学习模块加载完成 '.center(20, '*'))
    prompt_writing = PromptWritingModule()
    log.INFO(' 提示写作模块加载完成 '.center(20, '*'))
    doc_template_db = DocTemplateDB()
    log.INFO(' 文档模板数据库模块加载完成 '.center(20, '*'))
    user_dict_db = UserDictDB()
    log.INFO(' 用户词典数据库模块加载完成 '.center(20, '*'))
    smart_reading = SmartReading()
    log.INFO(' 智能阅读模块加载完成 '.center(20, '*'))
    sti = STIModule()
    log.INFO(' 科技情报模块加载完成 '.center(20, '*'))

    log.INFO(' 比特秘书启动 '.center(30, '*'))
    app.run(host='0.0.0.0', port=5002, debug=False)
