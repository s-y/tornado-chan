#!/usr/bin/env python
# coding: utf-8

from __future__ import division, print_function, unicode_literals

from os import path

import tornadoredis
from db import DataManager
from handlers import IndexHandler, ThreadHandler
from logs import app_log
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, url


def make_app():
    base_dir = path.dirname(path.abspath(__file__))
    debug = True

    return Application([
        url(r"/", IndexHandler, name="index"),
        url(r"/thread", ThreadHandler, name="thread"),
        url(r'/files/(.*)', StaticFileHandler,
            {'path': path.join(base_dir, "files")}, name="files"),
        # url(r"/(?P<param1>.*)", HelloHandler, global_vars, name='home'),
    ],
        debug=debug,
        xsrf_cookies=False,
        template_path=path.join(base_dir, "templates"),
        static_path=path.join(base_dir, "static"),
        media_path=path.join(base_dir, "data"),
        cookie_secret='secret',
        redis=tornadoredis.Client(),
    )


def main():
    port = 8888
    app = make_app()
    app.listen(port)
    app_log.info('Application started on port {}'.format(port))
    IOLoop.current().start()

if __name__ == '__main__':
    main()
