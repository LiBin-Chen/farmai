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
from app.api.errors import error_response, bad_request
from app.models import Post, Comment, Permission
from app.utils.decorators import permission_required


@bp.route('/comments', methods=['POST'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def create_comment():
    """
    发表评论
    :return:
    """
    data = request.get_data()
    message = {}

    if not data:
        message['data'] = 'You must post JSON data.'
    if 'body' not in data or not data.get('body').strip():
        message['body'] = 'Body is required.'
    if 'post_id' not in data or not data.get('post_id'):
        message['post'] = 'Post is required.'

    if message:
        return bad_request(message)

    post = Post.query.get_or_404(int(data.get('post_id')))
    comment = Comment()
    comment.from_dict(data)
    comment.author = g.current_user
    comment.post = post
    # 必须先添加评论,后续给各用户发送通知时.User.new_recived_comments()才能使更新的值
    db.session.add(comment)
    db.session.commit()  # 更新数据库,添加评论记录
    # TODO 添加评论时
    # 1.如果是一级评论,只需要给文章作者发送新评论通知
    # 2.如果不是一级评论,则需要给文章作者和该评论的所有祖先的作者发送新评论通知
    users = set()
    users.add(comment.post.author)  # 将文章作者添加进集合中
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors

    # 给各用户发送新评论通知
    for u in users:
        u.add_notification('unread_recived_comments_count', u.new_recived_comments())

    db.session.commit()  # 更新数据库,写入新通知
    response = jsonify(comment.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的location头部
    response.headers['Location'] = url_for('api.get_comment', id=comment.id)
    return response


@bp.route('/comments/', methods=['GET'])
@token_auth.login_required
def get_comments():
    """
    返回评论集合,分页
    :return:
    """
    page = request.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', current_app.config['COMMENTS_PER_PAGE'], type=int), 100)
    data = Comment.to_collection_dict(Comment.query.order_by(Comment.timestamp.desc()), page, per_page,
                                      'api.get_comments')
    return jsonify(data)


@bp.route('/comments/<int:id>', methods=['GET'])
@token_auth.login_required
def get_comment(id):
    """
    返回单个评论
    :return:
    """
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_dict())


@bp.route('/comments/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_comment(id):
    """
    修改单个评论
    :param id:
    :return:
    """
    comment = Comment.query.get_or_404(id)
    if g.current_user != comment.author and g.current_user != comment.post.author:
        return error_response(403)
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    comment.from_dict(data)
    db.session.commit()
    return jsonify(comment.to_dict())


@bp.route('/comments/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_comment(id):
    """
    删除单个评论
    :param id:
    :return:
    """
    comment = Comment.query.get_or_404(id)
    if g.current_user != comment.author and g.current_user != comment.post.author and not g.current_user.can(
            Permission.ADMIN):
        return error_response(403)

    # 删除评论时:
    # 1. 如果是一级评论，只需要给文章作者发送新评论通知
    # 2. 如果不是一级评论，则需要给文章作者和该评论的所有祖先的作者发送新评论通知
    users = set()
    users.add(comment.post.author)  # 将文章作者添加进集合中
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors
    # 必须先删除该评论,后续给个用户发送通知时,User.new_recived_comments才是更新后的值
    db.session.delete(comment)
    db.session.commit()  # 更新数据库,删除评论记录
    for u in users:
        u.add_notification('unread_recived_comments_count', u.new_recived_comments())

    db.session.commit()
    return '', 204


'''
评论被点赞或取消点赞'''


@bp.route('/comments/<int:id>/like', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def like_comments(id):
    """
    点赞评论
    :param id:
    :return:
    """
    comment = Comment.query.get_or_404(id)
    comment.liked_by(g.current_user)
    db.session.add(comment)
    # 切记要先提交,先添加点赞记录到数据库,因为new_likes()会查询comments_likes关联表
    db.session.commit()
    # 给作者打算新点赞通知
    comment.author.add_notification('unread_likes_count', comment.author.new_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are nowo liking comment [id: %d].' % id
    })


@bp.route('/comments/<int:id>/unlike', methods=['GET'])
@token_auth.login_required
@permission_required(Permission.COMMENT)
def unlike_comment(id):
    """
    取消点赞评论
    :param id:
    :return:
    """
    comment = Comment.query.get_or_404(id)
    comment.unlike_by(g.current_user)
    db.session.add(comment)
    db.session.commit()

    # 给作者发送新点赞通知(需要自动减1)
    comment.author.add_notification('unread_likes_count', comment.author.new_likes())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not liking comment [id: %d] anymore.' % id
    })
