#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

from flask import Blueprint

bp = Blueprint('api', __name__)

# 写在最后是为了防止循环导入,ping.py文件也会导入bp
from app.api import ping
