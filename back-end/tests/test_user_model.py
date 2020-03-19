#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    测试用户数据模型
"""

import unittest
from app import create_app, db
from app.models import User
from tests import TestConfig


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='john')
        u.set_password('pass1234')
        self.assertTrue(u.check_password('pass1234'))
        self.assertFalse(u.check_password('1234'))

    def test_avatar(self):
        u = User(username='john', email='john@163.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         '5ad2197b80f2010461c700d80fd35e9d'
                                         '?d=identicon&s=128'))
