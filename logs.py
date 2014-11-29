import logging

from tornado.log import enable_pretty_logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


access_log = logging.getLogger("tornado.access")
app_log = logging.getLogger("tornado.application")
gen_log = logging.getLogger("tornado.general")
enable_pretty_logging()
