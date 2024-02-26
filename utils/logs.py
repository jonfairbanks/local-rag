import logging
import sys

def setup_logger(log_file='local-rag.log', level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(level)

    log_format = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

log = setup_logger()