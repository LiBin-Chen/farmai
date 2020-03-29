from flask import url_for, request
from flask_restful import Resource, reqparse, inputs, fields, marshal_with
from app.api.auth import token_auth
from app.extensions import db
from app.models import User, Role


class RoleItem(fields.Raw):
    def format(self, value):
        return Role.query.get_or_404(value).name


class AvatarItem(fields.Raw):
    def output(self, key, obj):
        return obj.avatar(128)


resource_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'name': fields.String(default='Common User'),
    'email': fields.String,
    'timestamp': fields.DateTime(dt_format='rfc822', attribute='member_since'),
    'role_name': RoleItem(attribute='role_id'),
    '_links': {
        'avatar': AvatarItem,
        'self': fields.Url('api_v2.user')
    }
}


# User: shows a single user item and lets you delete a user item
class UserAPI(Resource):
    method_decorators = [token_auth.login_required]   # applies to all inherited resources

    @marshal_with(resource_fields)
    def get(self, id):
        '''返回单个用户'''
        # return User.query.get_or_404(id).to_dict()
        # return marshal(User.query.get_or_404(id), resource_fields), 200
        return User.query.get_or_404(id)

    def delete(self, id):
        '''删除单个用户'''
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return '', 204

    def put(self, id):
        '''修改单个用户，只能修改用户名或邮箱，修改密码后续在其它资源中实现'''
        user = User.query.get_or_404(id)

        # 验证传入的参数值，如果 username 未传值默认使用该用户的原用户名，如果 email 未传值默认使用该用户的原邮箱
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('username', default=user.username, type=str, help='Please provide a valid username.', location='json')
        parser.add_argument('email', default=user.email, type=inputs.regex('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'), help='Please provide a valid email address.', location='json')
        args = parser.parse_args(strict=True)

        # 如果用户名或邮箱地址已被占用，返回错误提示
        message = {}
        if 'username' in args and args['username'] != user.username and \
                User.query.filter_by(username=args['username']).first():
            message['username'] = 'Please use a different username.'
        if 'email' in args and args['email'] != user.email and \
                User.query.filter_by(email=args['email']).first():
            message['email'] = 'Please use a different email address.'
        if message:
            return {'message': message}, 400

        # 修改数据库
        user.from_dict(args, new_user=False)
        db.session.commit()
        return user.to_dict(), 201


# UserList: shows a list of all users, and lets you POST to add new user
class UserListAPI(Resource):
    method_decorators = {'get': [token_auth.login_required]}

    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('username', type=str, required=True, help='Please provide a valid username.', location='json')
        self.parser.add_argument('email', type=inputs.regex('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'), required=True, help='Please provide a valid email address.', location='json')
        self.parser.add_argument('password', type=str, required=True, help='Please provide a valid password.', location='json')
        super(UserListAPI, self).__init__()

    def get(self):
        '''返回用户列表'''
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        return User.to_collection_dict(User.query, page, per_page, 'api_v2.users')

    def post(self):
        '''注册新用户'''
        args = self.parser.parse_args(strict=True)

        # 如果用户名或邮箱地址已被占用，返回错误提示
        message = {}
        if User.query.filter_by(username=args.get('username', None)).first():
            message['username'] = 'Please use a different username.'
        if User.query.filter_by(email=args.get('email', None)).first():
            message['email'] = 'Please use a different email address.'
        if message:
            return {'message': message}, 400

        # 写入数据库
        user = User()
        user.from_dict(args, new_user=True)
        db.session.add(user)
        db.session.commit()

        return user.to_dict(), 201, {'Location': url_for('api_v2.user', id=user.id)}
