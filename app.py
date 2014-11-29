#!/usr/bin/env python
# coding: utf-8

from __future__ import division, print_function, unicode_literals

from os import path

from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, url

import tornadoredis
from db import DataManager
from handlers import IndexHandler, ThreadHandler, WsHandler
from logs import app_log


def make_app():
    base_dir = path.dirname(path.abspath(__file__))
    media_path = path.join(base_dir, "files")
    debug = True
    #redis = tornadoredis.ConnectionPool(max_connections=10, wait_for_available=True)
    redis = tornadoredis.Client()
    redis.connect()
    cache = DataManager()
    cache.redis = redis
    # cache.initialize()
    global_vars = dict(cache=cache)

    return Application([
        url(r"/", IndexHandler,global_vars, name="index"),
        url(r"/thread", ThreadHandler, global_vars,  name="thread"),
        url(r"/ws", WsHandler, global_vars, name="ws"),
        url(r'/files/(.*)', StaticFileHandler,
            {'path': media_path}, name="files"),
        # url(r"/(?P<param1>.*)", HelloHandler, global_vars, name='home'),
    ],
        debug=debug,
        xsrf_cookies=False,
        template_path=path.join(base_dir, "templates"),
        static_path=path.join(base_dir, "static"),
        media_path=media_path,
        cookie_secret='secret',
        redis=redis,
        cache=cache,
    )


def main():
    port = 8888
    app = make_app()
    app.listen(port)
    app_log.info('Application started on port {}'.format(port))
    IOLoop.current().start()

if __name__ == '__main__':
    main()
