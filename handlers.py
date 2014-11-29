from __future__ import division, print_function, unicode_literals

import datetime
import io
from multiprocessing import cpu_count

import tornado.web
from concurrent.futures import ThreadPoolExecutor
from logs import app_log
from PIL import Image
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.web import Application, HTTPError, RequestHandler
Task = gen.Task



def now():
    """2014-11-29T07:57:53.840699"""
    return datetime.datetime.now().isoformat()


class BaseHandler(RequestHandler):

    @property
    def db(self):
        return self.application.settings['redis']


class IndexHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        self.render("index.html", text="Hello from tornado!")

class ThreadHandler(BaseHandler):
    executor = ThreadPoolExecutor(max_workers=cpu_count())

    @gen.coroutine
    def get(self):
        key = "t1#p1"

        yield Task(self.db.hmset, key, {"date": now(),
                                              "post": "test",
                                              "images": 'st#ff.p',
                                              })
        #exist = yield Task(self.db.hexists, key)
        post = ''
        if True:
            post = yield Task(self.db.hgetall, key)
        print(post)

        self.render("thread.html", text="Hello from Thread")

    @gen.coroutine
    def post(self):

        # file = self.request.files["file"][0]
        # try:
        #     thumbnail = yield self.make_thumbnail(file.body)
        # except OSError:
        #     raise tornado.web.HTTPError(400, "Cannot identify image file")
        # path = self.application.settings["media_path"]
        # (file.body, thumbnail)  # ToDo save
        # with open(path, "wb") as out:
        #     body = self.request.get_argument("data")
        #     out.write(bytes(body, "utf8"))
        self.render()

    @run_on_executor
    def make_thumbnail(self, content):
        im = Image.open(io.BytesIO(content))
        im.convert("RGB")
        im.thumbnail((128, 128), Image.ANTIALIAS)
        with io.BytesIO() as output:
            im.save(output, "PNG")
            return output.getvalue()
