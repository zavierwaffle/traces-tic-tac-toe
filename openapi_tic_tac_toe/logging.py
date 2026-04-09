import logging
import os
import sys

from logging import Handler, StreamHandler, FileHandler
from logging import Formatter

from openapi_tic_tac_toe.util import _yes
from typing import List

def logging_configure():
    formatter = Formatter("%(asctime)s [%(levelname)s from %(name)s] %(message)s")
    handlers: List[Handler] = []

    app_to_stdout_deactivate = os.getenv("TTT_LOGGING_DEACTIVATE_APP_TO_STDOUT")
    if not _yes(app_to_stdout_deactivate):
        handlers.append(StreamHandler(sys.stdout))

    log_file_path = os.getenv("TTT_LOGGING_FILE_PATH")
    if log_file_path:
        log_directory = os.path.dirname(log_file_path)
        if log_directory:
            os.makedirs(log_directory, exist_ok = True)
        handlers.append(FileHandler(log_file_path))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    werkzeug_deactivate = os.getenv("TTT_LOGGING_DEACTIVATE_WERKZEUG")
    if _yes(werkzeug_deactivate):
        werkzeug = logging.getLogger("werkzeug")
        werkzeug.disabled = True
