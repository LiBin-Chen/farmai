#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''


try:
    from app import create_app
except ImportError:
    from .app import create_app

app = create_app()
