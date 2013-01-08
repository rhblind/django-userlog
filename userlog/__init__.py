# -*- coding: utf-8 -*-

import logging


class _UserLogConfig(object):
    
    logger = None
    
    @classmethod
    def get_logger(cls):
        """
        Instantiate and return a default logger.
        The NullHandler logger does nothing, and is supposed
        to be overridden in settings.py by creating a logger
        named 'gcharts'.
        """
        if cls.logger is None:
            class NullHandler(logging.Handler):
                def emit(self, record):
                    pass
            
            cls.logger = logging.getLogger("userlog")
            cls.logger.addHandler(NullHandler())

        return cls.logger

# Global logger
userlogger = _UserLogConfig.get_logger()
