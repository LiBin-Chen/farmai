#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
from functools import wraps

from flask import g

from app.api.errors import error_response
from app.models import Permission


def permission_required(permission):
    """
    检查常规权限
    :param permission:
    :return:
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 用户通过 Basic Auth认证后,就会在当前会话中附带g.current_user
            if not g.current_user.can(permission):
                return error_response(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    """
    检查管理员权限
    :param f:
    :return:
    """
    return permission_required(Permission.ADMIN)(f)

