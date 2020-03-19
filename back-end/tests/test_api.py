#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    flask 内建了一个测试客户端,app.test_client().它能复现程序运行在web服务器中的环境,扮演成客户端从而发送 请求
"""
import json
import unittest
from base64 import b64encode

from app import create_app, db
from app.models import User
from tests import TestConfig


class APITestCase(unittest.TestCase):
    def setUp(self):
        """
        每个测试之前执行
        :return:
        """
        # 创建app
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # flask内建的测试客户端,模拟浏览器行为
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    '''404等错误处理'''

    def test_404(self):
        """
        测试请求不存在的api时
        :return:
        """
        response = self.client.get('/api/wrong/url')
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['error'], 'Not Found')

    '''用户认证相关测试'''

    def get_basic_auth_headers(self, username, password):
        """
        创建basic auth 认证的headers
        :return:
        """
        return {
            'Authorization': 'Basic ' + b64encode((username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_token_auth_headers(self, username, password):
        """
        创建json web token 认证的headers
        :param username:
        :param password:
        :return:
        """
        headers = self.get_basic_auth_headers(username=username, password=password)
        response = self.client.post('/api/tokens', headers=headers)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']
        return {
            'Authorization': 'Bearer' + token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_get_token(self):
        """
        测试用户登录,即获取jwt,需要输入正确的用户名和密码,通过basic auth 之后发放jwt令牌
        :return:
        """
        # 第一个测试用户
        u = User(username='john', email='john@163.com')
        u.set_password('123')
        db.session.add(u)
        db.session.commit()

        # 输入错误的用户密码
        headers = self.get_basic_auth_headers('john', '456')
        response = self.client.post('/api/tokens', headers=headers)
        self.assertEqual(response.status_code, 401)

        # 输入正确的用户密码
        headers = self.get_basic_auth_headers('john', '123')
        response = self.client.post('/api/tokens', headers=headers)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        self.assertTrue(r'(.+)\.(.+)\.(.+)', json_response.get('token'))

    def test_not_attach_jwt(self):
        """
        测试请求头Authorization中没有附带JWT时,会返回401错误
        :return:
        """
        response = self.client.get('/api/users/')
        self.assertTrue(response.status_code, 401)

    def test_attach_jwt(self):
        """
        测试请求头Authorization中有附带JWT时,允许访问需要认证的API
        :return:
        """
        # 先建立一个测试用户
        u = User(username='john', email='john@163.com')
        u.set_password('123')
        db.session.add(u)
        db.session.commit()

        # 附带jwt到请求头中
        headers = self.get_token_auth_headers('john', '123')
        response = self.client.get('/api/users/', headers=headers)
        self.assertTrue(response.status_code, 200)

    def test_anonymous(self):
        """
        有些apu不需要认证,比如/apis/posts
        :return:
        """

        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, 200)
