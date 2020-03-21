#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
from flask import request, g, jsonify, url_for, current_app
from app.extensions import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
from app.models import User, Message


@bp.route('/message/', methods=['POST'])
@token_auth.login_required
def create_message():
    """
    给其它用户发送私信
    :return:
    """
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data')
    if 'body' not in data or not data.get('body'):
        return bad_request('Body is required.')
    if 'recipient_id' not in data or not data.get('recipient_id'):
        return bad_request('Recipient is required.')

    user = User.query.get_or_404(int(data.get('recipient_id')))
    if g.current_user == user:
        return bad_request('You cannot send private message to yourself')

    message = Message()
    message.from_dict(data)
    message.sender = g.current_user
    message.recipient = user
    db.session.add(message)
    # 给私信接收者发送新私信通知
    user.add_notification('unread_message_count', user.new_recived_comments())
    db.session.commit()
    response = jsonify(message.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_message', id=message.id)
    return response


@bp.route('/messages/', methods=['GET'])
@token_auth.login_required
def get_messages():
    """
    返回私信集合,分页
    :return:
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['MESSAGES_PER_PAGE'], type=int), 100)
    data = Message.to_collection_dict(Message.query.order_by(Message.timestamp.desc()), page, per_page,
                                      'api.get_message')
    return jsonify(data)


@bp.route('/messages/<int:id>', methods=['GET'])
@token_auth.login_required
def get_message(id):
    """
    获取指定单个私信
    :return:
    """
    message = Message.get_or_404(id)
    return jsonify(message.to_dict())


@bp.route('/messages/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_message(id):
    """
    修改单个私信
    :return:
    """
    message = Message.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(403)
    data = request.get_json()

    if not data:
        return bad_request('You must post JSON data')
    if 'body' not in data or not data.get('body'):
        return bad_request('Body is required.')
    if 'recipient_id' not in data or not data.get('recipient_id'):
        return bad_request('Recipient is required.')

    message.from_dict(data)
    db.session.commit()
    return jsonify(message.to_dict())


@bp.route('/messages/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_message(id):
    """
    删除单个私信
    :param id:
    :return:
    """
    message = Message.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(404)
    db.session.delete(message)
    # 给私信接收者发送新私信通知(需要自动减1)
    message.recipient.add_notification('unread_messages_count', message.recipient.new_recived_messages())
    db.session.commit()
    return '', 204
