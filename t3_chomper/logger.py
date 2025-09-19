import logging

def get_logger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(
        format="[%(levelname)s] %(asctime)s %(module)s:%(funcName)s:%(lineno)d %(msg)s",
        level=logging.INFO,
    )
    return logger
