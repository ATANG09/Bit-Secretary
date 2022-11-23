# -*- encoding: utf-8 -*-
'''
@File    :   quote_module.py
@Time    :   2022/08/08
@Author  :   ATANG_
@Version :   2.0
@Desc    :   引用模块
'''


import log_module as log
import torch
from transformers import BertTokenizer, MT5ForConditionalGeneration
import numpy as np
import jieba
import argparse
import os
import sys

sys.path.append('..')
os.environ["CUDA_VISIBLE_DEVICES"] = '0,1,2,3,4,5,6,7'


class T5PegasusTokenizer(BertTokenizer):

    def __init__(self, pre_tokenizer=lambda x: jieba.cut(x, HMM=False), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pre_tokenizer = pre_tokenizer

    def _tokenize(self, text, *arg, **kwargs):
        split_tokens = []
        for text in self.pre_tokenizer(text):
            if text in self.vocab:
                split_tokens.append(text)
            else:
                split_tokens.extend(super()._tokenize(text))
        return split_tokens


class PromptWritingModule(object):

    def __init__(self):
        self.args = self._set_args()
        log.INFO('引用模块参数: {}'.format(self.args.__repr__))

        self.tokenizer = T5PegasusTokenizer.from_pretrained(
            self.args.model_path)
        self.model = MT5ForConditionalGeneration.from_pretrained(
            self.args.model_path)
        self.model.eval()

        self.device = torch.device('cuda:{}'.format(
            self.args.device) if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def _set_args(self):
        """设置生成样本所需参数"""
        parser = argparse.ArgumentParser()

        parser.add_argument('--device', default='0', type=str, required=False)
        parser.add_argument(
            '--model_path', default='./model/t5_pegasus_base/', type=str)
        parser.add_argument('--max_output_length',
                            default=256, type=int, required=False)
        parser.add_argument(
            '--do_sample', action='store_true', help='生成策略是否采样')
        parser.add_argument('--num_beams', default=1,
                            type=int, required=False, help='集束搜索')
        parser.add_argument('--repetition_penalty', default=1.0,
                            type=float, required=False, help="重复生成惩罚")
        parser.add_argument('--temperature', default=1.0,
                            type=float, required=False, help='温度采样')
        parser.add_argument('--top_k', default=0, type=int,
                            required=False, help='top k')
        parser.add_argument('--top_p', default=0.0,
                            type=float, required=False, help='top p')
        parser.add_argument(
            '--save_path', default='./output/', type=str, required=False)

        return parser.parse_args()

    def prompt_writing(self, text):
        input_ids = self.tokenizer.encode(text,
                                          return_tensors='pt',
                                          max_length=512,
                                          truncation='only_first').to(self.device)
        if self.args.do_sample:
            output = self.model.generate(input_ids,
                                         max_length=self.args.max_output_length,
                                         eos_token_id=self.tokenizer.sep_token_id,
                                         decoder_start_token_id=self.tokenizer.cls_token_id,
                                         do_sample=True,
                                         temperature=self.args.temperature,
                                         top_k=self.args.top_k,
                                         top_p=self.args.top_p,
                                         repetition_penalty=self.args.repetition_penalty,
                                         ).cpu().numpy()[0][1:]
        else:
            output = self.model.generate(input_ids,
                                         max_length=self.args.max_output_length,
                                         eos_token_id=self.tokenizer.sep_token_id,
                                         decoder_start_token_id=self.tokenizer.cls_token_id,
                                         do_sample=False,
                                         num_beams=self.args.num_beams,
                                         repetition_penalty=self.args.repetition_penalty,
                                         ).cpu().numpy()[0][1:]
        output = self.tokenizer.decode(
            output, skip_special_tokens=True).replace(' ', '')
        end_pos = output.rfind('。')
        res = output[:end_pos+1]
        return res
