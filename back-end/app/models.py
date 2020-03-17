#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
import base64
from _md5 import md5
from datetime import datetime, timedelta
import os

import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for, current_app
from app import db


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


# 用户模型
class User(PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    # token = db.Column(db.String(32), index=True, unique=True)
    # token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'location': self.location,
            'about_me': self.about_me,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        # if self.token and self.token_expiration > now + timedelta(seconds=60):
        #     return self.token
        # self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        # self.token_expiration = now + timedelta(seconds=expires_in)
        # db.session.add(self)
        # return self.token
        payload = {
            'user_id': self.id,
            'name': self.name if self.name else self.username,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'.decode('utf-8')
        )

    @staticmethod
    def verify_jwt(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except (jwt.exceptions.ExpiredSignature, jwt.exceptions.InvalidSignatureError) as e:
            # token过期 或被人修改,那么签名验证码也会失败
            return None
        return User.query.get(payload.get('user_id'))

    def avatar(self, size):
        """
        头像
        :param size:
        :return:
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    # def revoke_token(self):
    #     self.token_expiration = datetime.utcnow() - timedelta(seconds=1)
    #
    # @staticmethod
    # def check_token(token):
    #     user = User.query.filter_by(token=token).first()
    #     if user is None or user.token_expiration < datetime.utcnow():
    #         return None
    #     return user
