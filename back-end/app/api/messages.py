from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.extensions import db
from app.models import User, Message
from app.utils.decorator import admin_required


@bp.route('/messages/', methods=['POST'])
@token_auth.login_required
def create_message():
    '''给其它用户发送私信'''
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    if 'body' not in data or not data.get('body'):
        return bad_request('Body is required.')
    if 'recipient_id' not in data or not data.get('recipient_id'):
        return bad_request('Recipient id is required.')

    user = User.query.get_or_404(int(data.get('recipient_id')))
    if g.current_user == user:
        return bad_request('You cannot send private message to yourself.')
    if user.is_blocking(g.current_user):
        return bad_request('You are in the blacklist of {}'.format(user.name if user.name else user.username))

    message = Message()
    message.from_dict(data)
    message.sender = g.current_user
    message.recipient = user
    db.session.add(message)
    # 给私信接收者发送新私信通知
    user.add_notification('unread_messages_count',
                          user.new_recived_messages())
    db.session.commit()
    response = jsonify(message.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_message', id=message.id)
    return response


@bp.route('/messages/', methods=['GET'])
@token_auth.login_required
def get_messages():
    '''返回私信集合，分页'''
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['MESSAGES_PER_PAGE'], type=int), 100)
    data = Message.to_collection_dict(
        Message.query.order_by(Message.timestamp.desc()), page, per_page,
        'api.get_messages')
    return jsonify(data)


@bp.route('/messages/<int:id>', methods=['GET'])
@token_auth.login_required
def get_message(id):
    '''返回单个私信'''
    message = Message.query.get_or_404(id)
    return jsonify(message.to_dict())


@bp.route('/messages/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_message(id):
    '''修改单个私信'''
    message = Message.query.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(403)
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    if 'body' not in data or not data.get('body'):
        return bad_request('Body is required.')
    message.from_dict(data)
    db.session.commit()
    return jsonify(message.to_dict())


@bp.route('/messages/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_message(id):
    '''删除单个私信'''
    message = Message.query.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(403)
    db.session.delete(message)
    # 给私信接收者发送新私信通知(需要自动减1)
    message.recipient.add_notification('unread_messages_count',
                                       message.recipient.new_recived_messages())
    db.session.commit()
    return '', 204


@bp.route('/send-messages/', methods=['POST'])
@token_auth.login_required
@admin_required
def send_messages():
    '''群发私信'''
    if g.current_user.get_task_in_progress('send_messages'):  # 如果用户已经有同名的后台任务在运行中时
        return bad_request('上一个群发私信的后台任务尚未结束')
    else:
        data = request.get_json()
        if not data:
            return bad_request('You must post JSON data.')
        if 'body' not in data or not data.get('body'):
            return bad_request(message={'body': 'Body is required.'})
        # 将 app.utils.tasks.send_messages 放入任务队列中
        g.current_user.launch_task('send_messages', '正在群发私信...', kwargs={'user_id': g.current_user.id, 'body': data.get('body')})
        return jsonify(message='正在运行群发私信后台任务')
