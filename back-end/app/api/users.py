import datetime
import re
from operator import itemgetter

from flask import request, jsonify, url_for, g, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
from app.extensions import db
from app.models import User, Notification, Post, Comment, comments_likes, Message, posts_likes


@bp.route('/users', methods=['POST'])
def create_user():
    '''注册一个新用户'''
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')

    message = {}
    if 'username' not in data or not data.get('username', None):
        message['username'] = 'Please provide a valid username.'
    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' not in data or not re.match(pattern, data.get('email', None)):
        message['email'] = 'Please provide a valid email address.'
    if 'password' not in data or not data.get('password', None):
        message['password'] = 'Please provide a valid password.'

    if User.query.filter_by(username=data.get('username', None)).first():
        message['username'] = 'Please use a different username.'
    if User.query.filter_by(email=data.get('email', None)).first():
        message['email'] = 'Please use a different email address.'
    if message:
        return bad_request(message)

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    '''返回用户集合，分页'''
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    '''返回一个用户'''
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return jsonify(user.to_dict(include_email=True))
    return jsonify(user.to_dict())


@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    '''修改一个用户'''
    user = User.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')

    message = {}
    if 'username' in data and not data.get('username', None):
        message['username'] = 'Please provide a valid username.'

    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' in data and not re.match(pattern, data.get('email', None)):
        message['email'] = 'Please provide a valid email address.'

    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        message['username'] = 'Please use a different username.'
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        message['email'] = 'Please use a different email address.'

    if message:
        return bad_request(message)

    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    '''删除一个用户'''
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    db.session.delete(user)
    db.session.commit()
    return '', 204


@bp.route('/users/<int:id>/notifications', methods=['GET'])
@token_auth.login_required
def get_user_notifications(id):
    """
    返回用户的新通知
    :param id:
    :return:
    """
    user = User.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    # 只返回上次看到的通知以来发生的新通知
    # 比如用户再 10:00:00 请求一次该API,再10:00:10 再次请求该API只会返回10:00:00之后产生的新通知
    since = request.args.get('since', 0.0, type=float)
    notifications = user.notifications.filter(Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([n.to_dict() for n in notifications])


'''
关注/取消关注'''


@bp.route('/follow/<int:id>', methods=['GET'])
@token_auth.login_required
def follow(id):
    """
    关注一个用户
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot follow yourself')
    if g.current_user.is_following(user):
        return bad_request('You have already followed that user.')
    g.current_user.follow(user)
    # 给该用户发送新粉丝通知
    user.add_notification('unread_follows_count', user.new_follows())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are now following %s.' % (user.name if user.name else user.username)
    })


@bp.route('/unfollow/<int:id>', methods=['GET'])
@token_auth.login_required
def unfollow(id):
    """
    取消关注一个用户
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot unfollow yourself.')
    if not g.current_user.is_following(user):
        return bad_request('You are enot following this user')
    g.current_user.unfollow(user)
    # 给该用户发送新粉丝通知(需要自动减1)
    user.add_notification('unread_follows_count', user.new_follows())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not following %s anymore.' % (user.name if user.name else user.username)
    })


'''
用户关注了谁,用户的粉丝'''


@bp.route('/users/<int:id>/followeds/', methods=['GET'])
@token_auth.login_required
def get_followeds(id):
    """
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)

    data = User.to_collection_dict(user.followeds, page, per_page, 'api.get_followeds', id=id)

    for item in data['items']:
        item['is_following'] = g.current_user.is_following(User.query.get(item['id']))
        # 获取用户开始关注followed的时间
        res = db.engine.execute(
            "select * from followers where follower_id={} and followed_id={}".format(user.id, item['id']))
        item['timestamp'] = datetime.datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')

    # 按timestamp排序一个字典列表(倒序,最新关注的人在最前面)
    data['items'] = sorted(data['items'], key=itemgetter('timestamp'), reverse=True)
    return jsonify(data)


@bp.route('/users/<int:id>/followers/', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    """
    返回用户的粉丝列表
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)
    data = User.to_collection_dict(user.followeds, page, per_page, 'api.get_followers', id=id)
    # 为每个follower添加is_following标志位
    for item in data['items']:
        item['is_following'] = g.current_user.is_following(User.query.get(item['id']))
        # 获取follower开始关注该用户的时间
        res = db.engine.execute(
            'select * from followers where follower_id={} and followed_id={}'.format(item['id'], user.id))
        item['timestamp'] = datetime.datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')

        # 按timestamp排序第一个字典列表(倒序,最新的粉丝在最前面)
        data['items'] = sorted(data['items'], key=itemgetter('timestamp'), reverse=True)
        # 标记哪些粉丝是新的
        last_read_time = user.last_follows_read_time or datetime.datetime(1900, 1, 1)
        for item in data['items']:
            if item['timestamp'] > last_read_time:
                item['is_new'] = True

        # 更新last_follows_read_time属性值
        user.last_follows_read_time = datetime.datetime.utcnow()
        # 将新粉丝通知的计数归0
        user.add_notification('unread_follows_count', 0)
        db.session.commit()
        return jsonify(data)


'''
与用户资源相关的资源'''


@bp.route('/users/<int:id>/posts/', methods=['GET'])
def get_user_posts(id):
    """
    返回该用户的所有博客文章列表
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Post.to_collection_dict(user.posts, page, per_page, 'api.get_user_posts', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/followeds-posts/', methods=['GET'])
@token_auth.login_required
def get_user_followeds_posts(id):
    """
    返回该用户关注的大神的所有博客文章列表
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Post.to_collection_dict(user.followeds_posts().order_by(Post.timestamp.desc()), page, per_page,
                                   'api.get_user_followeds_posts', id=id)
    # 标记哪些文章是新的
    last_read_time = user.last_followeds_posts_read_time or datetime.datetime(1990, 1, 1)
    for item in data['items']:
        if item['timestamp'] > last_read_time:
            item['is_new'] = True

    # 更新last_followeds_post_read_time值
    user.last_followeds_posts_read_time = datetime.datetime.utcnow()
    # 将新文章的通知计数归0
    user.add_notification('unread_followeds_posts_count', 0)
    db.session.commit()
    return jsonify(data)


@bp.route('/users/<int:id>/comments/', methods=['GET'])
@token_auth.login_required
def get_user_comments(id):
    """
    返回该用户发表过的所有评论列表
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)

    data = Comment.to_collection_dict(user.comments.order_by(Comment.timestamp.desc()), page, per_page,
                                      'api.get_user_comments', id=id)
    return jsonify(data)


@bp.route('/user/<int:id>/recived-comments', methods=['GET'])
@token_auth.login_required
def get_user_recived_comments(id):
    """
    返回该用户收到的所有评论
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)

    # 用户发布的所有文章id集合
    user_post_ids = [post.id for post in user.posts.all()]
    # 用户文章下面的新评论,即评论的post_id在user_post_ids集合中,且评论的author不是自己(文章的作者)

    q1 = Comment.query.filter(Comment.post_id.in_(user_post_ids), Comment.author != user)
    # 用户发表的评论被人回复了
    descendants = set()
    for c in user.comments:
        descendants = descendants | c.get_descendants()
    # 减去自己在底下回复的
    descendants = descendants - set(user.comments.all())
    descendants_ids = [c.id for c in descendants]
    q2 = Comment.query.filter(Comment.id.in_(descendants_ids))
    # 按时间排序排列构成用户收到的所有评论
    recived_comments = q1.union(q2).order_by(Comment.mark_read, Comment.timestamp.desc())
    # 分页后的JSON数据
    data = Comment.to_collection_dict(recived_comments, page, per_page, 'api.get_user_recived_comment', id=id)
    # 标记哪些评论是 新的
    last_read_time = user.last_recived_comments_read_time or datetime.datetime(1990, 1, 1)
    for item in data['items']:
        if item['timestamp'] > last_read_time:
            item['is_new'] = True

    user.last_recived_comments_read_time = datetime.datetime.utcnow()
    # 将新评论通知的计数归0
    user.add_notification('unread_recived_comments_count', 0)
    db.session.commit()
    return jsonify(data)


@bp.route('/users/<int:id>/recived-likes', methods=['GET'])
@token_auth.login_required
def get_user_recived_likes(id):
    """
    返回该用户收到的赞和喜欢
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)

    # 用户哪些评论被点赞了,分页
    comments = user.comments.join(comments_likes).paginate(page, per_page)
    # 点赞记录
    records = {
        'items': [],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': comments.pages,
            'total_items': comments.total
        },
        '_links': {
            'self': url_for('api.get_user_recived_likes', page=page, per_page=per_page, id=id),
            'next': url_for('api.get_user_recived_likes', page=page + 1, per_page=per_page,
                            id=id) if comments.has_next else None,
            'prev': url_for('api.get_user_recived_likes', page=page - 1, per_page=per_page,
                            id=id) if comments.has_prev else None
        }
    }
    for c in comments.items:
        # 重组数据,变成 谁 什么时间 点赞了您的 哪条评论
        for u in c.likes:
            if u != user:
                data = {}
                data['user'] = u.to_dict()
                data['comment'] = c.to_dict()
                # 获取点赞时间
                res = db.engine.execute(
                    'select * from comments_likes where user_id={} and comment_id={}'.format(u.id, c.id))
                data['timestamp'] = datetime.datetime.strftime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                # 标记本条点赞记录是否为新的
                last_read_time = user.last_likes_read_time or datetime.datetime(1990, 1, 1)
                if data['timestamp'] > last_read_time:
                    data['is_new'] = True
                records['items'].append(data)

    # 按照timestamp排序一个字典列表(倒序,最新点赞的人在最前面)
    records['items'] = sorted(records['items'], key=itemgetter('timestamp'), reverse=True)
    # 更新last_likes_read_time的属性值
    user.last_likes_read_time = datetime.datetime.utcnow()
    # 将新点赞通知的计数归0
    user.add_notification('unread_likes_count', 0)
    db.session.commit()
    return jsonify(records)


@bp.route('/users/<int:id>/messages-senders/', methods=['GET'])
@token_auth.login_required
def get_user_messages_recipients(id):
    """
    我给那些用户发过私信,按照用户分组,返回我给各用户最后一次发送的私信
    即:我 给 谁最后一次 发送了什么私信
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['MESSAGES_PER_PAGE'], type=int), 100)

    data = Message.to_collection_dict(
        user.messages_sent.group_by(Message.recipient_id).order_by(Message.timestamp.desc()), page, per_page,
        'api.get_user_messages_recipients', id=id
    )
    # 我给每个用户发的私信,他们有没有未读的
    for item in data['items']:
        # 发了给谁
        recipient = User.query.get(item['recipient']['id'])
        # 总共给他发过多少条
        item['total_count'] = user.messages_sent.filter_by(recipient_id=item['recipient']['id']).count()
        # 他最后一次查看收到的私信的时间
        last_read_time = recipient.last_message_read_time or datetime.datetime(1990, 1, 1)
        # item是发给他的最后一条,如果最后一条不是新的,肯定就没有了
        if item['timestamp'] > last_read_time:
            item['is_new'] = True
            # 继续获取发给这个用户的私信有几条是新的
            item['new_count'] = user.messages_sent.filter_by(recipient_id=item['recipient']['id']).filter(
                Message.timestamp > last_read_time).count()

    return jsonify(data)


@bp.route('/users/<int:id>/history-messages/', methods=['GET'])
@token_auth.login_required
def get_user_history_messages(id):
    '''返回我与某个用户(由查询参数 from 获取)之间的所有私信记录'''
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['MESSAGES_PER_PAGE'], type=int), 100)
    from_id = request.args.get('from', type=int)
    if not from_id:  # 必须提供聊天的对方用户的ID
        return bad_request('You must provide the user id of opposite site.')
    # 对方发给我的
    q1 = Message.query.filter(Message.sender_id == from_id, Message.recipient_id == id)
    # 我发给对方的
    q2 = Message.query.filter(Message.sender_id == id, Message.recipient_id == from_id)
    # 按时间正序排列构成完整的对话时间线
    history_messages = q1.union(q2).order_by(Message.timestamp)
    data = Message.to_collection_dict(history_messages, page, per_page, 'api.get_user_history_messages', id=id)
    # 现在这一页的 data['items'] 包含对方发给我和我发给对方的
    # 需要创建一个新列表，只包含对方发给我的，用来查看哪些私信是新的
    recived_messages = [item for item in data['items'] if item['sender']['id'] != id]
    sent_messages = [item for item in data['items'] if item['sender']['id'] == id]
    # 然后，标记哪些私信是新的
    last_read_time = user.last_messages_read_time or datetime(1900, 1, 1)
    new_count = 0
    for item in recived_messages:
        if item['timestamp'] > last_read_time:
            item['is_new'] = True
            new_count += 1
    if new_count > 0:
        # 更新 last_messages_read_time 属性值为收到的私信列表最后一条(最近的)的时间
        user.last_messages_read_time = recived_messages[-1]['timestamp']
        db.session.commit()  # 先提交数据库，这样 user.new_recived_messages() 才会变化
        # 更新用户的新私信通知的计数
        user.add_notification('unread_messages_count', user.new_recived_messages())
        db.session.commit()
    # 最后，重新组合 data['items']，因为收到的新私信添加了 is_new 标记
    messages = recived_messages + sent_messages
    messages.sort(key=data['items'].index)  # 保持 messages 列表元素的顺序跟 data['items'] 一样
    data['items'] = messages
    return jsonify(data)


'''
拉黑与取消拉黑'''


@bp.route('/users/block/<int:id>', methods=['GET'])
@token_auth.login_required
def block(id):
    """
    开始拉黑一个用户
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot block yourself')
    if g.current_user.is_blocking(user):
        return bad_request('You have already blocked that user.')

    g.current_user.block(user)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You are now blocking %s.' % (user.name if user.name else user.username)
    })


@bp.route('/users/unblock/<int:id>', methods=['GET'])
@token_auth.login_required
def unblock(id):
    '''取消拉黑一个用户'''
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot unblock yourself.')
    if not g.current_user.is_blocking(user):
        return bad_request('You are not blocking this user.')
    g.current_user.unblock(user)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not blocking %s anymore.' % (user.name if user.name else user.username)
    })


'''
谁喜欢了你的文章'''


@bp.route('users/<int:id>/recived-posts-likes', methods=['GET'])
@token_auth.login_required
def get_user_recived_posts_likes(id):
    """
    返回该用户收到的文章喜欢
    :param id:
    :return:
    """

    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)

    posts = user.posts.join(posts_likes).paginate(page, per_page)
    # 喜欢记录
    records = {
        'items': [],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': posts.pages,
            'total_items': posts.total
        },
        '_links': {
            'self': url_for('api.get_user_recived_posts_likes', page=page, per_page=per_page, id=id),
            'next': url_for('api.get_user_recived_posts_likes', page=page + 1, per_page=per_page,
                            id=id) if posts.has_next else None,
            'prev': url_for('api.get_user_recived_posts_likes', page=page - 1, per_page=per_page,
                            id=id) if posts.has_prev else None,
        }
    }

    for p in posts.items:
        # 重组数据,变成 谁 什么时间 喜欢了你的 哪篇文章
        for u in p.likes:
            if u != user:
                data = {}
                data['user'] = u.to_dict()
                data['post'] = p.to_dict()
                # 获取喜欢时间
                res = db.engine.execute('select * from posts_likes where user_id={} and post_id={}'.format(u.id, p.id))
                data['timestamp'] = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                # 标记本条喜欢记录是否为新的
                last_read_time = user.last_posts_likes_read_time or datetime(1900, 1, 1)
                if data['timestamp'] > last_read_time:
                    data['is_new'] = True
                records['items'].append(data)

    # 按timestamp倒序
    records['items'] = sorted(records['items'], key=itemgetter('timestamp'), reverse=True)
    # 更新last_posts_likes_read_time
    user.last_posts_like_read_time = datetime.datetime.utcnow()
    user.add_notification('unread_posts_likes_count', 0)
    db.session.commit()
    return jsonify(records)


def get_user_liked_posts(id):
    """
    返回用户喜欢的文章
    :param id:
    :return:
    """
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return error_response(403)

    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)

    data = Post.to_collection_dict(user.liked_posts.order_by(Post.timestamp.desc()), page, per_page,
                                   'api.get_user_liked_posts', id=id)

    return jsonify(data)

