# coding: utf-8
from __future__ import division, print_function, unicode_literals

import datetime
import io
from multiprocessing import cpu_count

import tornado.web
from PIL import Image
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.web import Application, HTTPError, RequestHandler
from tornado.websocket import WebSocketHandler

import arrow
import tornadoredis
from concurrent.futures import ThreadPoolExecutor
from db import P, T
from logs import app_log


def now():
    return datetime.datetime.now()
last_cleanup = now()

Task = gen.Task

delta = datetime.timedelta(seconds=2)


def build_key(topic_id, post_id):
    return "t{}#p{}".format(topic_id, post_id)


def build_topcic_key(topic_id):
    return "t{}".format(topic_id)


class BaseHandler(RequestHandler):

    def readable_data(self, dictionary):
        dictionary['date'] = arrow.get(dictionary['date']).to('Europe/Kiev').humanize(locale='ua')
        dictionary['images'] = [
            self.reverse_url('files', url) for url in dictionary['images'].split("#")]
        return dictionary

    def initialize(self, cache=None):
        self.cache = cache

    @property
    def redis(self):
        return self.application.settings['redis']


class IndexHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        self.render("index.html", text="Hello from tornado!")


class WsHandler(WebSocketHandler):

    def open(self):
        pass

    def on_message(self, message):
        self.write_message(u"Your message was: " + message)

    def on_close(self):
        pass


class ThreadHandler(BaseHandler):
    executor = ThreadPoolExecutor(max_workers=cpu_count())

    @gen.coroutine
    def get_topic(self, topic_id):
        topic = self.cache.topics.get(topic_id, False)
        self.cache.topic_last_usage[topic_id] = now()
        if topic:
            result = yield [self.get_post(x, topic_id) for x in set(topic)]
            raise tornado.gen.Return(result)
        else:
            app_log.info("Not in cache topic: {}".format(topic_id))
            key = build_topcic_key(topic_id)
            exist = yield Task(self.redis.exists, key)
            if exist:
                result = []
                for x in set(topic):
                    x = yield self.get_post(int(x))
                    result.append(x)
                raise tornado.gen.Return(result)
            else:
                raise HTTPError(404)

    @gen.coroutine
    def get_post(self, post_id, topic_id):
        post = self.cache.posts.get(post_id, None)
        self.cache.post_last_usage[post_id] = now()
        if post:
            raise tornado.gen.Return(post)
        else:
            app_log.info("Not in cache post: {}".format(post_id))
            key = build_key(topic_id, post_id)
            exist = yield Task(self.redis.exists, key)
            if exist:
                post = yield Task(self.redis.hgetall, key)
                app_log.debug("Key exist")
                raise tornado.gen.Return(post)
            else:
                raise tornado.gen.Return(None)

    def __init__(self, *args, **kwargs):
        super(ThreadHandler, self).__init__(*args, **kwargs)

        if last_cleanup < (now() - delta):
          #  self.save_to_redis()
            app_log.info('Not wait clean up')

    @gen.coroutine
    def get(self):
        post = {"date": now().isoformat(),
                "post": "test",
                "images": 'st#ff.p',
                }
        topic_id = self.cache.add_topic(post)
        # yield Task(self.redis.incr, T)

        # redis db
        for x in range(100):
            post = {"date": now().isoformat(),
                    "post": "test",
                    "images": 'st#ff.p',
                    }
            post_id = self.cache.add_post(topic_id, post)
      #      yield Task(self.redis.incr, P)
      # key = "t{}#p{}".format(t_id, post_id)
      #      yield Task(self.redis.hmset, key, post)

        post = ''

        app_log.debug("Key: {}".format(build_key(topic_id, post_id)))
        # exist = yield Task(self.redis.exists, key)
        # if exist:
        #     post = yield Task(self.redis.hgetall, key)
        #     app_log.debug("Key exist")

        # app_log.info("{}".format(self.get_topic(t_id)))
        self.get_topic(topic_id - 1)
        self.get_post(topic_id - 1)
        # self.get_post(1)
        posts = yield self.get_topic(topic_id)
        posts = tuple(self.readable_data(post) for post in posts)
        self.render(
            "thread.html", text="Hello from Thread", posts=posts)

    @gen.coroutine
    def save_to_redis(self):
        global delta
        app_log.info('Start cleanup')
        old = now() - delta
        for topic_id, date in self.cache.topic_last_usage.iteritems():
            if date < old:

                for post_id in self.cache.topics[topic_id]:
                    post = self.cache.posts[post_id]
                    key = build_key(topic_id, post_id)
                    yield Task(self.redis.hmset, key, post)
                    app_log.debug(
                        "Remove post {}".format(self.cache.posts[post_id]))
                del self.cache.posts[post_id]

                yield Task(self.redis.sadd, build_topcic_key(topic_id), *self.cache.topics[topic_id])
                app_log.debug(
                    "Remove topic {}".format(self.cache.topics[topic_id]))
                del self.cache.topics[topic_id]
        global last_cleanup
        last_cleanup = now()
        raise gen.Return(None)

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
