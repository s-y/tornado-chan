import tornado.web
from tornado import gen
from tornado.web import (Application, HTTPError, RequestHandler,
                         StaticFileHandler, )
from logs import app_log
import tornado.web
from tornado import gen
class BaseHandler(RequestHandler):

    @property
    def db(self):
        print(self.application.db)
        return self.application.db


class IndexHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        self.render("index.html", text="Hello from tornado!")
