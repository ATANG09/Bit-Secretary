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

from database_module import DocTemplateDB, UserDictDB
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
@app.route('/learn_template', methods=['GET', 'POST'])
def learn_template():
    name = request.form.get('template_name')
    doc_type = request.form.get('doc_type')
    upload_files = request.files.getlist('doc_files')
    doc_paths = []
    for file in upload_files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'learn_template/', filename)
        file.save(filepath)
        doc_paths.append(filepath)

    log.INFO('模板名称: {}'.format(name))
    template = doc_learn.learn_docs(doc_type, doc_paths)
    doc_template_db.save_template(name, template)
    result = json.dumps(template)
    return result, 200, HEADER_CONFIG


# 模板展示
@app.route('/show_templates', methods=['GET', 'POST'])
def show_templates():
    templates = doc_template_db.show_templates()
    result = json.dumps(templates)
    return result, 200, HEADER_CONFIG


# 模板加载
@app.route('/load_template', methods=['GET', 'POST'])
def load_template():
    template_name = request.form.get('template_name')
    log.INFO('模板名称: {}'.format(template_name))

    template = doc_template_db.load_template(template_name)
    result = json.dumps(template)
    return result, 200, HEADER_CONFIG


# 模板删除
@app.route('/delete_template', methods=['GET', 'POST'])
def delete_template():
    name = request.form.get('template_name')
    message = doc_template_db.delete_template(name)
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 模板清空
@app.route('/clear_templates', methods=['GET', 'POST'])
def clear_templates():
    message = doc_template_db.clear_templates()
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


"""  ****************** 提示写作 *****************
"""

# 提示写作
@app.route('/prompt_write', methods=['GET', 'POST'])
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
@app.route('/reading', methods=['GET', 'POST'])
def reading():
    text = request.form.get('text')
    method = request.form.get('method')
    if len(text.strip()) == 0:
        log.ERROR('阅读文本为空')
        return "", 200, HEADER_CONFIG

    log.INFO("阅读文本: {}".format(text))
    log.INFO("阅读功能: {}".format(method))
    result = smart_reading.smart_reading(text, method)
    if method != 'sentiment_analysis':
        log.INFO("智能阅读结果: {}".format(result))
    return result, 200, HEADER_CONFIG


# 获取敏感词词典列表
@app.route('/show_sensitive_dict', methods=['GET', 'POST'])
def show_sensitive_dict():
    result = json.dumps(user_dict_db.show_userdict(dict_type='sensitive'))
    return result, 200, HEADER_CONFIG


# 添加敏感词词典
@app.route('/add_sensitive_dict', methods=['GET', 'POST'])
def add_sensitive_dict():
    name = request.form.get('name')
    lang_type = request.form.get('lang_type')
    files = request.files.getlist('files')
    paths = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'user_dict/', filename)
        file.save(filepath)
        paths.append(filepath)

    message = user_dict_db.add_userdict(
        name, lang_type, paths, dict_type='sensitive')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 删除敏感词词典
@app.route('/delete_sensitive_dict', methods=['GET', 'POST'])
def delete_sensitive_dict():
    name = request.form.get('name')
    message = user_dict_db.delete_userdict(name, dict_type='sensitive')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 用户选择使用的敏感词词典
@app.route('/select_sensitive_dict', methods=['GET', 'POST'])
def select_sensitive_dict():
    data = json.loads(request.form.get('data'))
    message = user_dict_db.select_userdict(data, dict_type='sensitive')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 获取实体词典列表
@app.route('/show_entity_dict', methods=['GET', 'POST'])
def show_entity_dict():
    result = json.dumps(user_dict_db.show_userdict(dict_type='entity'))
    return result, 200, HEADER_CONFIG


# 添加实体词典
@app.route('/add_entity_dict', methods=['GET', 'POST'])
def add_entity_dict():
    name = request.form.get('name')
    lang_type = request.form.get('lang_type')
    files = request.files.getlist('files')
    paths = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(CACHE_DIR + 'user_dict/', filename)
        file.save(filepath)
        paths.append(filepath)

    message = user_dict_db.add_userdict(
        name, lang_type, paths, dict_type='entity')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 删除实体词典
@app.route('/delete_entity_dict', methods=['GET', 'POST'])
def delete_entity_dict():
    name = request.form.get('name')
    message = user_dict_db.delete_userdict(name, dict_type='entity')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


# 用户选择使用的实体词典
@app.route('/select_entity_dict', methods=['GET', 'POST'])
def select_entity_dict():
    data = request.form.get('data')
    message = user_dict_db.select_userdict(data, dict_type='entity')
    result = json.dumps({'message': message})
    return result, 200, HEADER_CONFIG


"""  ****************** 写作分析 ******************
"""


"""  ****************** 科技情报 ******************
"""

# 情报分析与报告生成
@app.route('/STI', methods=['GET', 'POST'])
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


if __name__ == '__main__':
    doc_learn = DocLearnModule()
    log.INFO(' 文档学习模块加载完成 '.center(20, '*'))
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
