from flask import Blueprint
from flask_restful import Api


# Blueprint
bp = Blueprint('api_v2', __name__)
# Init Flask-RESTful
api = Api(bp)

# 统一注册路由
from app.api_v2 import urls
