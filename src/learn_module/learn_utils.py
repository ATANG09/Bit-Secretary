# -*- encoding: utf-8 -*-
'''
@File    :   learn_utils.py
@Time    :   2022/03/24
@Author  :   ATANG_
@Version :   1.0
@Desc    :   模板学习工具
'''

import sys

import numpy as np
from scipy.linalg import norm
from sklearn.feature_extraction.text import CountVectorizer

sys.path.append('..')
import log_module as log


class Stack(object):
    
    def __init__(self):
        self.stack = []
        self.top = -1

    def push(self, x):
        self.stack.append(x)
        self.top = self.top + 1

    def pop(self):
        if self.is_empty(): log.ERROR('Stack is empty.')
        else:
            self.top = self.top - 1
            x = self.stack.pop()
            return x

    def is_empty(self):
        return self.top == -1

    def get_top(self):
        return self.stack[self.top]

    def transfer(self, target: list):
        while not self.is_empty():
            target.append(self.pop())

    def show_stack(self):
        log.INFO(self.stack)


class ParametersManager(object):
    """ 参数管理 -
    """


    name = '<_paramX_>'
    
    def __init__(self):
        self.params_num = 0
        self.params_set = set()
        self.params_list = []

    def copy(self):
        return self.params_list.copy()

    def create(self, word):
        self.params_num += 1
        self.params_set.add(word)
        param_name = self.name.replace('X', str(self.params_num))
        self.params_list.append({
            'name':param_name,
            'value':word,
            'freq':1,
            })
        return param_name

    def update(self, word):
        for param in self.params_list:
            if word == param['value']:
                param['freq'] += 1
                return param['name']

    def delete(self, word):
        for param in self.params_list:
            if word == param['value']:
                self.params_num -= 1
                self.params_set.discard(word)
                self.params_list.remove(param)
                return

    def clear(self):
        self.params_num = 0
        self.params_list.clear()
        self.params_set.clear()

    def is_exist(self, word):
        if word in self.params_set:
            return True
        return False


def is_float(word):
    """ 是否为浮点数 -
    """

    if word.count('.') == 1:
        w_cut = word.split('.')
        w_l, w_r = w_cut[0], w_cut[1]
        if w_l.startswith('-') and w_l.count('-') == 1 and w_r.isdigit():
            if w_l.split('-')[1].isdigit():
                return True
        elif w_l.isdigit() and w_r.isdigit():
            return True
    return False


def tf_similarity(s1, s2):
    """ TF文本相似度 -
    """

    def add_space(s):
        return ' '.join(list(s))           
    s1, s2 = add_space(s1), add_space(s2)
    cv = CountVectorizer(tokenizer=lambda s: s.split())
    corpus = [s1, s2]
    vectors = cv.fit_transform(corpus).toarray()
    return np.dot(vectors[0], vectors[1]) / (norm(vectors[0]) * norm(vectors[1]))


if __name__ == '__main__':
    pass
