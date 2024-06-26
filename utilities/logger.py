from loguru import logger
import os
import sys

LOG_FILE = ".log"
ROTATION_TIME = "02:00"
SEARCHALL_LOG_FILE_NAME = 'searchallx'

class Logger:
    def __init__(self, name="x", log_dir="logs", debug=False):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, name+LOG_FILE)
        #print(f'{log_file_path}')
        # Remove default loguru handler
        logger.remove()

        # Add console handler with a specific log level
        level = "DEBUG" if debug else "INFO"
        logger.add(sys.stdout, level=level)
        # Add file handler with a specific log level and timed rotation
        logger.add(log_file_path, rotation=ROTATION_TIME, level="DEBUG", enqueue=True)
        self.logger = logger

# LOG = Logger(name='searchallx', debug=True).logger
#LOG = Logger().logger
#logger = LOG
#LOG_local = Logger(name='local', debug=True).logger

if __name__ == "__main__":
    log = Logger().logger

    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")

    #LOG.logger.debug("This is a debug message 1234.")
