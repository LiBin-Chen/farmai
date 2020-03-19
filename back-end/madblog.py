import os
import subprocess
import sys

import click

from app import create_app
from app.extensions import db
from app.models import User, Post
from config import Config

app = create_app(Config)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Post': Post}


# 创建coverage实例
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Run tests under code coverage.')
def test(coverage):
    """
    run the unit tests
    :return:
    """
    # 如果执行 flask test --coverage,但是FLASK_COVERAGE环境变量不存在时,给它配置上
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = str(1)  # 需要字符串的值
        sys.exit(subprocess.call(sys.argv))

    import unittest
    # 找到tests目录
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary: ')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        cov_dir = os.path.join(os.path.join(basedir, 'tmp'), 'coverage')
        COV.html_report(directory=cov_dir)
        print('')
        print('HTML report be stored in %s' % os.path.join(cov_dir, 'index.html'))
        COV.erase()
