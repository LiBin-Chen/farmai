import json
from flask import make_response
from app.api_v2.app import api


@api.representation('text/html')
def output_html(data, code, headers=None):
    # data: HTML 文档
    # code: HTTP 状态码
    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    return resp


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    # implement csv output!
    pass


@api.representation('text/xml')
def output_xml(data, code, headers=None):
    # implement xml output!
    pass


@api.representation('application/json')
def output_json(data, code, headers=None):
    # Makes a Flask response with a JSON encoded body
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp
