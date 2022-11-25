# -*- encoding: utf-8 -*-
'''
@File    :   reading_module.py
@Time    :   2022/07/19
@Author  :   ATANG_
@Version :   1.0
@Desc    :   智能阅读模块
'''

import io
import json
import base64
import requests
import time

from langdet.Langdet import Langdet
import jwt
import matplotlib.pyplot as plt

import log_module as log
from database_module import UserDictDB


plt.rcParams['font.sans-serif'] = ['Songti SC']
plt.rcParams['axes.unicode_minus'] = False

SEN_MAP = {
    "EMOTION_HAPPY": '喜',
    "EMOTION_GOOD": '好',
    "EMOTION_ANGER": '怒',
    "EMOTION_SORROW": '哀',
    "EMOTION_FEAR": '惧',
    "EMOTION_EVIL": '恶',
    "EMOTION_SURPRISE": '惊'
}

EQUIPMENT = {
    '中': ['815A型电子侦察船', '815G型“间谍船”', 'Type815G', '815A型电子侦察舰', '815型电子监视船', '815/815A型电子侦察船'],
    '美': ['“里根”号航母'],
    '日': ['“日向”级直升机航母“伊势”号', '“大隅”级船坞运输舰“国东”号', '水陆机动团', '两栖攻击舰'],
    '澳': [],
}


class SmartReading(object):

    def __init__(self):
        self.url = 'https://online.lingjoin.com:4000/nlpir/request'
        self.dect = Langdet()
        self.user_dict_db = UserDictDB()

    def _buildJWT(self):
        payload = {"timestamp": int(time.time()), "token_expire": 1689129077, "allow_method": [
            "*"], "user_id": "tangzeyang"}
        encrypt_key = "762a3b6da5ad2abe49af096241b4703f4e6edd16c18f9e592acca1e10a3a89522a932833e7f8593f9e9a709fdeadf1716269715c"
        token = jwt.encode(payload, key=encrypt_key, algorithm='HS256')
        return token

    def make_request(self, data, method):
        params = {'instant': 'true', 'method': method}
        token = self._buildJWT()
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer '+token, 'accept': 'application/json'}
        try:
            response = requests.post(
                self.url, params=params, data=json.dumps(data), headers=self.headers)
            return json.loads(response.text)['result']
        except Exception as err:
            log.ERROR("访问 {} 出错".format(self.url))
            log.ERROR(err)

    # 词性标注+新词发现
    def ictclas(self, text, user):
        res = {
            'POS': {
                '军事装备': [],
                '人名': [],
                '地名': [],
                '机构名': [],
                '时间': [],
                '数词': [],
            },
           'new_words':[]
        }

        data = {'data_type': 'text', 'data_list': [
            text], 'param': {'POS': 'true'}}
        ictclas_res = self.make_request(data, 'ictclas')
        if not ictclas_res:
            return {'result':res}

        ictclas_res_list = ictclas_res[0].split()
        for item in ictclas_res_list:
            pos = item.rfind('/')
            word, tag = item[:pos], item[pos+1:]
            if len(word) <= 1:  # 单字不标引
                continue
            if tag == 'nr':
                res['POS']['人名'].append(word)
            elif tag == 'ns':
                res['POS']['地名'].append(word)
            elif tag == 'nt':
                res['POS']['机构名'].append(word)
            elif tag == 't':
                res['POS']['时间'].append(word)
            elif tag == 'm':
                res['POS']['数词'].append(word)

        for country in EQUIPMENT:
            res['POS']['军事装备'].extend(
                [e for e in EQUIPMENT[country] if e in text])

        user_dict = self.user_dict_db._load_userdict(
            dict_type='entity', user=user)  # 用户实体词典
        for d in user_dict:
            res['POS'][d['name']] = [w for w in d['words'] if w in text]

        data = {'data_type': 'text', 'data_list': [text], 'param': {'keys': 5}}
        new_words_res = self.make_request(data, 'new_words_finder')
        res['new_words'] = [item['word'] for item in new_words_res[0]]
        return {'result': res}

    # 新词发现
    def new_words_finder(self, text, method):
        data = {'data_type': 'text', 'data_list': [
            text], 'param': {'keys': 20}}
        new_words_res = self.make_request(data, method)
        if not new_words_res:
            return {'result':[]}

        res = [item['word'] for item in new_words_res[0]]
        return {'result': res}

    # 情感分析
    def sentiment_analysis(self, text, method):
        data = {'data_type': 'text', 'data_list': [text]}
        sentiment_res = self.make_request(data, method)
        if not sentiment_res:
            return {'result':''}

        img = draw(sentiment_res[0])
        return {'result': {'emotion_pic': image_to_str(img)}}

    # 情感分析(WPS)
    def sentiment_for_wps(self, text):
        data = {'data_type':'text','data_list':[text]}
        sentiment_res = self.make_request(data, 'sentiment_analysis')
        if not sentiment_res:
            return {'result':[]}

        res = [{'name':SEN_MAP[k], 'value':v} for k, v in sentiment_res[0].items() if v != 0]
        return {'result':res}

    # 关键词抽取
    def key_extract(self, text, method):
        if len(text) > 20000:
            keys = 30
        elif 10000 < len(text) <= 20000:
            keys = 20
        elif 5000 < len(text) <= 10000:
            keys = 10
        else:
            keys = 5
        data = {'data_type': 'text', 'data_list': [
            text], 'param': {'keys': keys}}
        key_extract_res = self.make_request(data, method)
        if not key_extract_res:
            return {'result':[]}

        res = [item['word'] for item in key_extract_res[0]]
        return {'result': res}

    # 敏感词过滤
    def key_scanner(self, text, method, user):
        data = {'data_type': 'text', 'data_list': [text]}
        key_scanner_res = self.make_request(data, method)
        if not key_scanner_res:
            return {'result':[]}

        if 'illegal' in key_scanner_res[0]:
            res = key_scanner_res[0]['illegal']['keys']
        else:
            res = []
        user_dict = self.user_dict_db._load_userdict(
            dict_type='sensitive', user=user)  # 用户敏感词词典
        res.extend([w for w in user_dict if w in text])
        return {'result': res}

    # 摘要
    def summary(self, text, method):
        data = {'data_type': 'text', 'data_list': [
            text], 'param': {'max': 300, 'rate': 0.3}}
        summary_res = self.make_request(data, method)
        if not summary_res:
            return {'result':''}

        return {'result': summary_res[0]}

    # 语种识别
    def lang_detect(self, text):
        index = self.dect.detect_text(text)
        return {'result': self.dect.id_to_chinese(index)}

    def smart_reading(self, text, method, user='_user'):
        if method == 'ictclas':
            res = self.ictclas(text, user)
        elif method == 'sentiment_analysis':
            res = self.sentiment_analysis(text, method)
        elif method == 'sentiment_for_wps':
            res = self.sentiment_for_wps(text)
        elif method == 'key_extract':
            res = self.key_extract(text, method)
        elif method == 'key_scanner':
            res = self.key_scanner(text, method, user)
        elif method == 'new_words_finder':
            res = self.new_words_finder(text, method)
        elif method == 'summary':
            res = self.summary(text, method)
        elif method == 'lang_detect':
            res = self.lang_detect(text)
        return json.dumps(res)


def draw(sen_res):
    fig = plt.figure()
    values = [v for v in sen_res.values() if v != 0]
    num = sum(values)
    labels = [SEN_MAP[k]+':  {}个'.format(v)
              for k, v in sen_res.items() if v != 0]
    explode = [0.01 for _ in range(len(values))]
    index = values.index(max(values))
    explode[index] = 0.1
    colors = ['red', 'orange', 'yellow', 'green', 'purple', 'blue', 'black']
    sizes = [v/num*100 for v in values]
    _, l_text, p_text = plt.pie(
        sizes, explode=explode, labels=labels, shadow=True, colors=colors, autopct='%1.2f%%')
    for t in l_text:
        t.set_size(14)
    for l in p_text:
        l.set_size(14)
    plt.axis('equal')
    # 将图片转换成二进制流
    canvas = fig.canvas
    buffer = io.BytesIO()
    canvas.print_png(buffer)
    img = buffer.getvalue()
    buffer.close()
    return img


def image_to_str(image):
    image_byte = base64.b64encode(image)
    image_str = image_byte.decode('ascii')  # byte类型转换为str
    return image_str
