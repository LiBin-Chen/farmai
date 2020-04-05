#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
