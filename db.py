from __future__ import division, print_function, unicode_literals


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
            n= yield Task(self.redis.get, P)
            self.last_post_id = int(n)
        else:
            yield Task(self.redis.set, P, value)
            app_log.debug('Posts counter do not exists')

        exists = yield Task(self.redis.exists, T)
        if exists:
            n = yield Task(self.redis.get, T)
            self.last_topic_id = int(n)
            app_log.debug('Topics counter do not exists')
        else:
            yield Task(self.redis.set, T, value)
        keys = yield Task(self.redis.keys, "t*")
        app_log.debug(keys)

    def __init__(self):
        self.redis = None
        self.posts = {}
        self.post_last_usage = {}
        self.topics = {}
        self.topic_last_usage = {}
        self.last_post_id =  1000
        self.last_topic_id = 1000


    def add_post(self, topic_id, post):
        self.last_post_id += 1
        self.posts[self.last_post_id] = post
        if not(topic_id in self.topics):
            app_log.error("Topic not in cache: {}".format())
        self.topics[topic_id].append(self.last_post_id)
        return self.last_post_id

    def add_topic(self, first_post):
        self.last_topic_id += 1
        new_topic = []
        self.topics[self.last_topic_id] = new_topic
        new_topic.append(self.add_post(self.last_topic_id, first_post))
        return self.last_topic_id



