from __future__ import division, print_function, unicode_literals

import json

import tornadoredis
from logs import app_log
from tornado import gen

T = 'number_topics'
P = 'number_posts'
Task = gen.Task


class DataManager(object):

    @gen.coroutine
    def initialize(self, value=0):
        exists = yield Task(self.redis.exists, P)
        if exists:
            self.last_post_id = yield Task(self.redis.get, P)
        else:
            yield Task(self.redis.set, P, value)

        exists = yield Task(self.redis.exists, T)
        if exists:
            self.last_topic_id = yield Task(self.redis.get, T)
        else:
            yield Task(self.redis.set, T, value)
        keys = yield Task(self.redis.keys, "t*")
        print(keys)

    def __init__(self, redis):
        self.redis = redis
        self.posts = []
        self.topics = []
        self.last_post_id = 0
        self.last_topic_id = 0

        self.initialize()

    def add_post(self, post):
        return True

    def add_topic(self, topic):
        return True

    def get_post(self, key):
        if key in self.posts:
            return self.posts[key]
        return False

    def get_topic(self, key):
        if key in self.topics:
            return self.topics[key]
        return False

    def remove_old(self):
        return
