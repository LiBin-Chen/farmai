from flask import render_template_string
from flask_restful import Resource
from app.api_v2.common.utils import output_html


class Ping(Resource):
    def get(self):
        return {'message': 'Pong!'}
        # return output_html(render_template_string('<h1>测试 Flask-RESTful 返回 HTML 文档</h1>'), 200)
