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
from tornado.websocket import WebSocketHandler
Task = gen.Task
import arrow
import tornadoredis

def now():
    return datetime.datetime.now()

def readable_data(dictionary):
    dictionary['date'] = arrow.get(dictionary['date']).to('Europe/Kiev').humanize(locale='ua')
    return dictionary

class BaseHandler(RequestHandler):

    def initialize(self, cache=None):
        self.cache=cache

    @property
    def redis(self):
        return self.application.settings['redis']




from db import T, P

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
last_cleanup = now()
delta = datetime.timedelta(seconds=18)

class ThreadHandler(BaseHandler):
    executor = ThreadPoolExecutor(max_workers=cpu_count())
    def get_topic(self, t_id):
        #import ipdb; ipdb.set_trace()
        topic = self.cache.topics.get(t_id, False)
        if topic:
            return [self.get_post(x) for x in topic]
        else:
            app_log.warning("Not in cache topic: {}".format(t_id))
        self.cache.topic_last_usage[t_id] = now()

    def get_post(self, post_id):
        self.cache.post_last_usage[post_id] = now()
        return self.cache.posts.get(post_id, None)
    def __init__(self, *args, **kwargs):
        super(ThreadHandler, self).__init__(*args, **kwargs)

        if last_cleanup < (now()-delta):
            self.save_to_redis()
            app_log.info('Not wait clean up')




    @gen.coroutine
    def get(self):
        post = {"date": now().isoformat(),
                                              "post": "test",
                                              "images": 'st#ff.p',
                                              }
        t_id = self.cache.add_topic(post)
        # yield Task(self.redis.incr, T)
        # import ipdb; ipdb.set_trace()


        # redis db
        for x in range(100):
            post_id = self.cache.add_post(t_id, post)
      #      yield Task(self.redis.incr, P)
      #       key = "t{}#p{}".format(t_id, post_id)
      #      yield Task(self.redis.hmset, key, post)

        post = ''
        key = "t{}#p{}".format(t_id, post_id)
        app_log.debug("Key: {}".format(key))
        # exist = yield Task(self.redis.exists, key)
        # if exist:
        #     post = yield Task(self.redis.hgetall, key)
        #     app_log.debug("Key exist")
        # app_log.debug(post)
        # app_log.debug(self.get_topic(t_id))
        self.render("thread.html", text="Hello from Thread", posts=self.get_topic(t_id))

    @gen.coroutine
    def save_to_redis(self):
        global delta
        app_log.info('Start cleanup')
        old = now()-delta
        for topic_id, date in self.cache.topic_last_usage.iteritems():
            if date < old:
                for post_id in self.cache.topics[topic_id]:
                    post = self.cache.posts[post_id]
                    key = "t{}#p{}".format(topic_id, post_id)
                    yield Task(self.redis.hmset, key, post)
                    del self.cache.posts[post_id]
                yield Task(self.redis.sadd, "t{}".format(topic_id), *self.cache.topics[topic_id])
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
