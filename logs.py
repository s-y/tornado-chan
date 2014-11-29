import logging

from tornado.log import enable_pretty_logging

access_log = logging.getLogger("tornado.access")
app_log = logging.getLogger("tornado.application")
gen_log = logging.getLogger("tornado.general")
app_log.setLevel(logging.INFO)
enable_pretty_logging()
