#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

from flask import jsonify

from app.api import bp


@bp.route('/ping', methods=['GET'])
def ping():
    """
    前端vue.js用来测试与后端flask api的连通性
    :return:
    """
    return jsonify('pong')
