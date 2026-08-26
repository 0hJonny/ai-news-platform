import logging
from logging import handlers


class Logger:
    def __init__(self, filename, level=logging.DEBUG):
        self.logger = self.get_logger(filename, level)

    @staticmethod
    def get_logger(filename, level):
        logger = logging.getLogger(__name__)
        logger.setLevel(level)

        handler = handlers.RotatingFileHandler(
            filename, maxBytes=10 * 1024 * 1024, backupCount=5)
        handler.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)


