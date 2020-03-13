#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

from api.errors import error_response
from models import User

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    """
    用于检查用户提供的用户名和密码
    :param username:
    :param password:
    :return:
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password(password)


@basic_auth.error_handler
def basic_auth_error():
    """
    认证错误的情况下返回错误的响应
    :return:
    """
    return error_response(401)


@token_auth.verify_token
def verify_token(token):
    """
    用于检查用户请求是否有token,并且token真实存在,还在有效期内
    :param token:
    :return:
    """
    g.current_user = User.check_token(token) if token else None
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    """
    用于token auth 认证失败的情况下返回错误响应
    :return:
    """
    return error_response(401)
