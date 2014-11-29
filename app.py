#!/usr/bin/env python
# coding: utf-8

from __future__ import division, unicode_literals  # , print_function,

from os import path
from logs import app_log

from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, url
from handlers import IndexHandler
from db import DataManager
def make_app():
    base_dir = path.dirname(__file__)
    debug = True

    return Application( [
        url(r"/", IndexHandler, name="index"),
        url(r'/files/(.*)', StaticFileHandler,
            {'path': path.join(base_dir, "files")}, name="files"),
        # url(r"/(?P<param1>.*)", HelloHandler, global_vars, name='home'),
    ]
     ,
        debug=debug,
        xsrf_cookies=False,
        template_path=path.join(base_dir, "templates"),
        static_path=path.join(base_dir, "static"),
        cookie_secret='secret',
        db=DataManager(),
    )



def main():
    port = 8888
    app = make_app()
    app.listen(port)
    app_log.info('Application started on port {}'.format(port))
    IOLoop.current().start()

if __name__ == '__main__':
    main()
