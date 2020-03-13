#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
from flask import jsonify, g

from api import bp
from api.auth import basic_auth, token_auth
from app import db


@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_token()
    db.session.commit()
    return jsonify({'token': token})


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
