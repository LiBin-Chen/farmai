#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''

from .app import create_app, db
from .app import models

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'models': models}
