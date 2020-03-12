#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir,'.env'))

class Config(object):
    pass
