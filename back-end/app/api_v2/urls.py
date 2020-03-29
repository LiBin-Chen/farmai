from app.api_v2.app import api
from app.api_v2.resources.ping import Ping
from app.api_v2.resources.users import UserAPI, UserListAPI

# 统一注册路由
api.add_resource(Ping, '/', '/ping')
api.add_resource(UserListAPI, '/users', endpoint='users')
api.add_resource(UserAPI, '/users/<int:id>', endpoint='user')
