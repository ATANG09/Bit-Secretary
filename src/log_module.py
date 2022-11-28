# -*- encoding: utf-8 -*-
'''
@File    :   log_module.py
@Time    :   2022/03/24
@Author  :   ATANG_
@Version :   1.0
@Desc    :   日志模块
'''

import logging


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def INFO(msg):
    LOGGER.info(msg)


def DEBUG(msg):
    LOGGER.debug(msg)


def WARNING(msg):
    LOGGER.warning(msg)


def ERROR(msg):
    LOGGER.error(msg)
