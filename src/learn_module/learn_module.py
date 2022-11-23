# -*- encoding: utf-8 -*-
'''
@File    :   learn_module.py
@Time    :   2022/03/24
@Author  :   ATANG_
@Version :   1.0
@Desc    :   文档学习模块
'''

import log_module as log
import json
import os
import re
import sys
import warnings

from docx import Document
from LAC import LAC
# from text2vec import Similarity

from learn_module import learn_utils
# import learn_utils
sys.path.append('..')


# CACHE_DIR = '../../cache/learn_module'
# STOPWORDS_PATH = './stopwords.txt'
CACHE_DIR = './cache/learn_module'
STOPWORDS_PATH = './src/stopwords.txt'


class LearnWord(object):
    """ 字词学习 -
    """
    pass


class LearnSentence(object):
    """ 句子学习 -
    """

    stopwords = [line.strip() for line in open(
        STOPWORDS_PATH, 'r', encoding='utf-8').readlines()]
    infowords = ['TIME', 'm']
    filter_pattern = {
        '政府报告': {
            'TIME': ['\d'],
            'm': ['\d', '第[一二三四五六七八九十]+[次|届]'],
        },
        '学术论文': {
            'TIME': ['\d'],
        },
    }

    def __init__(self):
        # 分词器
        self.lac = LAC(mode='lac')
        self.params_manager = learn_utils.ParametersManager()

    def cut_paragraph(self, docs):
        doc_sentences = list()
        for doc in docs:
            sentence_num = 0
            sentences = list()
            for paragraph in doc['docText']:
                res = paragraph.split('。')
                if res[-1] == "":
                    res = res[:-1]
                    res[-1] += '。'
                sentences.append(res)
                sentence_num += len(res)
            doc_sentences.append({
                'docName': doc['docName'],
                'sentences': sentences,
                'sentence_num': sentence_num
            })
        return doc_sentences

    def concat_sentences(self, pattern_doc):
        new_pattern_doc = {
            'paragraphs': [],
            'params': pattern_doc['params'],
        }
        for paragraph in pattern_doc['sentences']:
            new_pattern_doc['paragraphs'].append('。'.join(paragraph))
        return new_pattern_doc

    # 分析参数信息
    # def _analyze_info(self, vocab, idx):
    #     pass

    # 停用词过滤
    # def _filter_stopwords(self, vocab):
    #     new_vocab = [word for word in zip(vocab[0], vocab[1]) if word[0] not in LearnSentence.stopwords]
    #     return new_vocab

    # 信息词后过滤
    def _post_filter(self, word, tag, doc_type):
        for pattern in LearnSentence.filter_pattern[doc_type][tag]:
            if bool(re.search(pattern, word)):
                return True
        return False

    # 生成参数
    def _create_param(self, word):
        if self.params_manager.is_exist(word):
            param_name = self.params_manager.update(word)
        else:
            param_name = self.params_manager.create(word)
        return param_name

    def _extract_pattern(self, sentence, doc_type):
        vocab = self.lac.run(sentence)
        infos = [idx for idx, tag in enumerate(
            vocab[1]) if tag in LearnSentence.infowords]
        for idx in infos:
            if self._post_filter(vocab[0][idx], vocab[1][idx], doc_type):
                param_name = self._create_param(vocab[0][idx])
                # 参数替换信息词
                vocab[0][idx] = param_name
        new_sentence = ''.join(vocab[0])
        return new_sentence

    # 句式学习
    def learn_pattern(self, merge_doc, doc_type):
        pattern_doc, pa = {'sentences': []}, []
        for paragraph in merge_doc:
            for sentence in paragraph:
                pa.append(self._extract_pattern(sentence, doc_type))
            pattern_doc['sentences'].append(pa.copy())
            pa.clear()
        pattern_doc['params'] = self.params_manager.copy()
        self.params_manager.clear()
        return pattern_doc


class LearnDiscourse(object):
    """ 篇章学习 -
    """

    # 标题模板
    title_pattern = {
        '政府报告': {
            1: '\s*[一二三四五六七八九十]+、',
            2: '\s*(（[一二三四五六七八九十]+）)',
            3: '\s*[0-9]+\.',
            4: '\s*(（[0-9]+）)',
            5: '\s*([①②③④⑤⑥⑦⑧⑨⑩]|([0-9]+）))',
            6: '\s*(([A-Z]\.)|(（[A-Z]）))',
            7: '\s*(([a-z]\.)|(（[a-z]）))',
        },
        '学术论文': {}
    }
    # 标题序号
    title_number = '({}级标题)'
    # 结尾模板
    ending_pattern = {
        '政府报告': '\s*(各位代表|来源)',
        '学术论文': '',
    }

    def __init__(self):
        pass

    # 标题匹配
    def _match_title(self, paragraph, doc_type):
        for level, pattern in LearnDiscourse.title_pattern[doc_type].items():
            res = re.match(pattern, paragraph)
            if res != None:
                return level, res.span()
        return 0, None

    # 特殊标题切割
    def _special_title_cut(self, paragraph):
        pos = paragraph.find('。')
        return [paragraph] if pos == -1 else [paragraph[:pos], paragraph[pos+1:]]

    # 划分文档标题
    def _title_partition(self, paragraphs):
        if not paragraphs:
            return ''
        title = paragraphs[0]
        paragraphs.remove(title)
        return title

    # 划分结尾
    def _ending_partition(self, paragraphs, doc_type):
        ending = []
        if not paragraphs:
            return ending, []
        for idx, paragraph in enumerate(reversed(paragraphs)):
            if re.match(LearnDiscourse.ending_pattern[doc_type], paragraph):
                ending.insert(0, paragraph)
            else:
                break
        sep = len(paragraphs) if idx == 0 else idx * -1
        return ending, paragraphs[:sep]

    # 段落正文划分
    def _paragraph_partition(self, paragraphs_body, doc_type):
        partition, openning, pa, level_list, flag = [], [], [], [], False
        for paragraph in paragraphs_body:
            level, span = self._match_title(paragraph, doc_type)
            if level > 0:
                paragraph = LearnDiscourse.title_number.format(
                    level) + paragraph[span[1]:]
                if len(pa) > 0:
                    if not flag:
                        flag = True
                        openning = pa.copy()
                    else:
                        partition.append(pa.copy())
                    pa.clear()
                level_list.append(level)
                pa.extend(self._special_title_cut(paragraph))
            else:
                pa.append(paragraph)
        if pa is not []:
            partition.append(pa.copy())
        assert len(partition) == len(level_list)
        return openning, partition, level_list

    def _create_node(self, part, level):
        paragraphs = part[1:] if len(part) > 1 else list()
        node = {
            'title': part[0],
            'level': level,
            'paragraphs': paragraphs,
            'child': [],
        }
        return node

    # 结构生成
    def _generate_structure(self, partition, level_list):
        child = []
        title_stack, temp_stack = learn_utils.Stack(), learn_utils.Stack()
        for idx, part in enumerate(partition):
            title_stack.push(self._create_node(part, level_list[idx]))
        while not title_stack.is_empty():
            title = title_stack.pop()
            while not temp_stack.is_empty():
                if title['level'] < temp_stack.get_top()['level']:
                    title['child'].append(temp_stack.pop())
                    continue
                break
            temp_stack.push(title)
        temp_stack.transfer(child)
        return child

    # 篇章结构学习
    def learn_structure(self, pattern_doc, doc_type):
        template_doc = {}
        paragraphs = pattern_doc['paragraphs'].copy()
        template_doc['title'] = self._title_partition(paragraphs)
        template_doc['level'] = 0
        template_doc['ending'], paragraphs_body = \
            self._ending_partition(paragraphs, doc_type)
        template_doc['openning'], partition, level_list = \
            self._paragraph_partition(paragraphs_body, doc_type)
        template_doc['child'] = self._generate_structure(partition, level_list)
        template_doc['params'] = pattern_doc['params']
        return template_doc


class DocLearnModule(object):
    """ 文档学习模块 -
    """

    merge_similarity_threshold = 0.6
    merge_sentence_length_threshold = 90

    def __init__(self):
        # 计算文本相似度
        # self.sim = Similarity()
        self.ls = LearnSentence()
        self.ld = LearnDiscourse()

    def _get_docs(self, paths):
        def get_doc(path):
            doc = Document(path)
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip() == '':
                    continue
                paragraphs.append(paragraph.text.strip())
            return {'docName': os.path.basename(path), 'docText': paragraphs}

        docs = []
        if isinstance(paths, str):
            docs.append(get_doc(paths))
            return docs, 1
        elif isinstance(paths, list) or isinstance(paths, tuple):
            for path in paths:
                docs.append(get_doc(path))
            return docs, len(paths)

    def _to_json(self, data):
        return json.dumps(data, ensure_ascii=False, indent=4)

    def _save_data(self, data, path):
        with open(path, 'w') as f:
            f.write(self._to_json(data))

    # 通过文本相似度计算是否融合，保留每个文档都出现的相似句子
    def _is_merge(self, base_sentence, refer_docs):
        def is_similar(refer_doc):
            for paragraph in refer_doc['sentences']:
                for sentence in paragraph:
                    # score = self.sim.get_score(base_sentence, sentence)
                    score = learn_utils.tf_similarity(base_sentence, sentence)
                    if score > DocLearnModule.merge_similarity_threshold:
                        log.INFO('【相似度得分】:{}\n【基准句】:{}\n【参考句】:{}'.
                                 format(score, base_sentence, sentence))
                        paragraph.remove(sentence)
                        return True
            return False
        for refer_doc in refer_docs:
            if not is_similar(refer_doc):
                return False
        return True

    # 文档融合
    def _merge_docs(self, docs, doc_num):
        if doc_num == 1:
            return docs[0]['sentences']
        num_list = [item['sentence_num'] for item in docs]
        # 选取句子数最多的文档为base，其余为refer
        base_idx = num_list.index(max(num_list))
        base_doc = docs[base_idx]
        docs.remove(base_doc)
        refer_docs = docs.copy()
        log.INFO('已选取基准文档:{}'.format(base_doc['docName']))

        merge_doc, pa = [], []
        for paragraph in base_doc['sentences']:
            for sentence in paragraph:
                if self._is_merge(sentence, refer_docs):
                    pa.append(sentence)
            if len(pa) != 0:
                merge_doc.append(pa.copy())
                pa.clear()
        return merge_doc

    # 文档学习
    def learn_docs(self, doc_type, doc_paths):
        warnings.filterwarnings('ignore')

        log.INFO('文档类型: {}'.format(doc_type))
        log.INFO('文档列表: {}'.format(json.dumps(doc_paths, ensure_ascii=False)))
        docs, doc_num = self._get_docs(doc_paths)

        merge_doc = self._merge_docs(self.ls.cut_paragraph(docs), doc_num)
        self._save_data(merge_doc, os.path.join(CACHE_DIR, 'merge_doc.json'))
        # log.INFO('文档融合结果:{}'.format(self._to_json(merge_doc)))
        log.INFO('文档融合完成')

        pattern_doc = self.ls.learn_pattern(merge_doc, doc_type)
        self._save_data(pattern_doc, os.path.join(
            CACHE_DIR, 'pattern_doc.json'))
        # log.INFO('句子学习结果:{}'.format(self._to_json(pattern_doc)))
        log.INFO('句子学习完成')

        template_doc = self.ld.learn_structure(
            self.ls.concat_sentences(pattern_doc),
            doc_type)
        self._save_data(template_doc, os.path.join(
            CACHE_DIR, 'template_doc.json'))
        # log.INFO('篇章学习结果:{}'.format(self._to_json(template_doc)))
        log.INFO('篇章学习完成')

        log.INFO('文档学习完成')
        return template_doc


if __name__ == '__main__':
    pass
