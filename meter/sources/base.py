import logging

from meter import config


class BaseSource:
    OPTIONS = []
    
    def __init__(self, options, min_cycle=4.0):
        argparser = config.DefaultArgumentParser(
            source=self.__class__.__name__
        )
        for args, kwargs in self.OPTIONS:
            argparser.add_argument(*args, **kwargs)
        self.opts = argparser.parse_args(options)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.min_cycle = min_cycle
        if hasattr(self, 'init'):
            self.init()

    def log(self, *args, level=logging.INFO):
        self.logger.log(level, *args) #stacklevel=2 ... py3.8
