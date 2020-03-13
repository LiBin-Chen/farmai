#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''程序

@description
    说明
'''
import os
import sys
from flask_cors import CORS
from flask import Flask
from flask_migrate import Migrate

from flask_sqlalchemy import SQLAlchemy

try:
    from config import Config
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    from config import Config

# Flask-SALAlchemy plugin
db = SQLAlchemy()
# Flask-Migrate plugin
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # enable CORS
    CORS(app)
    # init flask-SQLAlchemy
    db.init_app(app)
    # init flask-Migrate
    migrate.init_app(app, db)

    # 注册blueprint
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


from app import models
