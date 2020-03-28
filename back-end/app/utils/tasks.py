#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""
import sys
import time

# RQ worker 在flask应用之外运行,需要创建应用实例
from rq import get_current_job

from app import create_app
from app.models import User, Message, Task
from app.utils.email import send_email
from config import Config
from app.extensions import db

app = create_app(Config)
# 后续会使用flask-sqlalchemy来查询数据库,所以需要推送一个上下文使应用成为"当前"的应用实例
app.app_context().push()


def _set_task_progress(progress):
    # 当前后台任务
    job = get_current_job()
    job.save_meta()
    # 通过任务id查询对应的Task对象
    task = Task.query.get(job.get_id())
    # 动态的发送给task的所属用户 她的后台任务的进度比
    task.user.add_notification('task_progress', {
        'task_id': job.get_id(),
        'description': task.description,
        'progress': progress
    })

    # 进度为百分之100时,更新Task对象为已完成
    if progress >= 100:
        task.complete = True
    db.session.commit()


def send_messages(*args, **kwargs):
    """
    群发私信
    :param args:
    :param kwargs:
    :return:
    """
    # 由于rq worker运行再单独的进程中,当它出现意外错误时,我们需要捕获异常
    try:
        _set_task_progress(0)
        i = 0
        # 发送方
        sender = User.query(kwargs.get('user_id'))
        # 接收方
        recipients = User.query.filter(User.id != kwargs.get('user_id'))
        total_recipients = recipients.count()
        for user in recipients:
            message = Message()
            message.body = kwargs.get('body')
            message.sender = sender
            message.recipient = user
            db.session.add(message)
            # 给 私信接受者发送新私信通知
            user.add_notification('unread_messages_count', user.new_recived_messages())
            db.session.commit()

            # 给接收者同时发送一封邮件
            text_body = '''
            Dear {},
            {}
            Sincerely,
            The Madblog Team
            Note: replies to this email address are not monitored.
            '''.format(user.username, message.body)

            html_body = '''
            <p>Dear {0},</p>
            <p>{1}</p>
            <p>Sincerely,</p>
            <p>The Madblog Team</p>
            <p><small>Note: replies to this email address are not monitored.</small></p>
            '''.format(user.username, message.body)
            # 后台任务已经是异步了，所以send_email()没必要再用多线程异步，所以这里指定了 sync=True
            send_email('[Madblog] 温馨提醒',
                       sender=app.config['MAIL_SENDER'],
                       recipients=[user.email],
                       text_body=text_body,
                       html_body=html_body,
                       sync=True)

            # 模拟长时间的后台任务
            time.sleep(1)
            i += 1
            _set_task_progress(100 * i // total_recipients)

        # 群发结束后,需要设置Task对象已完成
        # 当前后台任务
        job = get_current_job()
        # 通过任务ID查询对应的Task对象
        task = Task.query.get(job.get_id())
        task.complete = True

        # 群发结束后,由管理员给发送方发送一条已完成的提示私信
        message - Message()
        message.body = '[群发私信]已完成, 内容: \n\n' + kwargs.get('body')
        message.sender = User.query.filter_by(email=app.config['ADMINS'][0]).first()
        message.recipient = sender
        db.session.add(message)
        # 给发送方发送新私信通知
        sender.add_notification('unread_messages_count', sender.new_recived_messages())
        db.session.commit()

    except Exception:
        app.logger.error('[群发私信]后台任务出错了', exc_info=sys.exc_info())
