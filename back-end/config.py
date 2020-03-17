#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

# import os
#
# from dotenv import load_dotenv
#
# basedir = os.path.abspath(os.path.dirname(__file__))
# load_dotenv(os.path.join(basedir, '.env'))
#
#
# class Config(object):
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False


import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class Pro(Config):
    pass
    DEBUG = False
    TEST = False


class Dev(Config):
    pass


class Test(Config):
    pass


config = {
    'pro': Pro,
    'dev': Dev,
    'test': Test,
}
