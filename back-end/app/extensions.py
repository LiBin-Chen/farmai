#!/usr/bin/env python3
# -*- coding: utf-8 -*-
''' Create instance of these flask extensions '''
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Flask-Cors plugin
from sqlalchemy import MetaData

cors = CORS()
# Flask-SQLAlchemy plugin
#使用自定义的元数据和命名约定
#这样做对数据库的迁移是很重要的。因为 SQL 没有定义一个标准的命名约定，无法保证数据库之间实现是兼容的
naming_convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'
}
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
# Flask-Migrate plugin
migrate = Migrate(render_as_batch=True)
