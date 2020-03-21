#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
from flask import g, jsonify

from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response
from app.models import Notification


@bp.route('/notification/<int:id>', methods=['GET'])
@token_auth.login_required
def get_notification(id):
    """
    返回一个用户通知
    :param id:
    :return:
    """
    notification = Notification.query.get_or_404(id)
    if g.current_user != notification.user:
        return error_response(403)

    data = notification.to_dict()
    return jsonify(data)
