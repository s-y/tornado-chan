# coding: utf-8
from __future__ import division, print_function, unicode_literals

import datetime
import errno
import io
import os
from multiprocessing import cpu_count
from os import path

import tornado.web
from PIL import Image
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.util import ObjectDict
from tornado.web import HTTPError, RequestHandler
from tornado.websocket import WebSocketHandler

import arrow
from concurrent.futures import ThreadPoolExecutor
from logs import app_log


# from db import P, T


def now():
    return datetime.datetime.now()
last_cleanup = now()

Task = gen.Task

delta = datetime.timedelta(seconds=2)


def build_key(topic_id, post_id):
    return "t{}#p{}".format(topic_id, post_id)


def build_topcic_key(topic_id):
    return "t{}".format(topic_id)


def mkdir_p(dir_path):
    """
    :param dir_path:
    :raise "Something wrong":
    """
    try:
        os.makedirs(dir_path)
        app_log.info("Dir created {}".format(dir_path))
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else:
            app_log.error('Dir path have OSError: {}'.format(dir_path))


class BaseHandler(RequestHandler):
    executor = ThreadPoolExecutor(max_workers=cpu_count())
    cache = None

    def readable_data(self, dictionary):
        dictionary['date'] = arrow.get(dictionary['date']).to(
            'Europe/Kiev').humanize(locale='ua')
        dictionary['images'] = [
            self.reverse_url('files', url) for url in dictionary['images'].split("#")]
        return ObjectDict(dictionary)

    def initialize(self, cache=None):
        self.cache = cache

    @property
    def redis(self):
        """
        :return:  the :class:`tornadoredis.Client`
        """
        return self.application.settings['redis']

    def make_image_paths(self, image, topic_id, post_id):
        directory = path.join(
            self.application.settings["media_path"], str(topic_id) + '__' + str(post_id))
        save_path = path.join(directory, image['filename'])
        mkdir_p(directory)
        image_name = image['filename'].split('.')
        if len(image_name) > 1:
            image_name = ''.join(image_name[:-1])
        else:
            image_name = ''.join(image_name)

        thumbnail_path = path.join(
            directory,  'thumbnail_' + image_name + '.png')
        return save_path,  thumbnail_path

    @run_on_executor
    def make_thumbnail(self, image, topic_id, post_id):
        content = image['body']
        save_path,  thumbnail_path = self.make_image_paths(
            image, topic_id, post_id)

        with open(save_path, mode='w') as output:
            output.write(content)
        im = Image.open(io.BytesIO(content))
        im.convert("RGB")
        im.thumbnail((128, 128), Image.ANTIALIAS)

        im.save(thumbnail_path, "PNG")
        return save_path,  thumbnail_path

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


class IndexHandler(BaseHandler):

    #@gen.coroutine
    def get(self):
        self.render("index.html", text="Hello from tornado!")

    def post(self):
        # import ipdb; ipdb.set_trace()
        images = []
        post = {"date": now().isoformat(),
                 "comment": self.get_argument('comment'),
                 "subject": self.get_argument('subject'),
              }
        topic_id, post_id = self.cache.add_topic(post)
        for file_ in self.request.files['file']:
            # ['body', 'content_type', 'filename']
            images.append(self.make_thumbnail(file_, topic_id, post_id))


        self.render("index.html", text="Hello from tornado!")


class WsHandler(WebSocketHandler):

    def open(self):
        pass

    def on_message(self, message):
        self.write_message(u"Your message was: " + message)

    def on_close(self):
        pass


class ThreadHandler(BaseHandler):

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
        topic_id, post_id = self.cache.add_topic(post)
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

        #post = ''

        #app_log.debug("Key: {}".format(build_key(topic_id, post_id)))
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
    def post(self):
        #
        # file = self.request.files["file"][0]
        #
        # try:
        #     thumbnail = yield self.make_thumbnail(file.body)
        # except OSError:
        #     raise tornado.web.HTTPError(400, "Cannot identify image file")
        # ToDo save
        # with open(path, "wb") as out:
        #     body = self.request.get_argument("data")
        #     out.write(bytes(body, "utf8"))
        self.render('thread.html')
