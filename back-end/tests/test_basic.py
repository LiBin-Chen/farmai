#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""

import unittest
from flask import current_app
from app import create_app, db
from tests import TestConfig


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        """
        每个测试之前执行
        :return:
        """
        # 创建flask应用
        self.app = create_app(TestConfig)
        # 激活(推送)flask应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        # 通过SQLAlchemy来使用sqlite内存数据库,db.create_all()快速创建所有的数据库表
        db.create_all()

    def tearDown(self):
        """
        每个测试之后执行的操作
        :return:
        """
        db.session.remove()
        # 删除所有的数据库表
        db.drop_all()
        # 退出flask上下文应用
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

