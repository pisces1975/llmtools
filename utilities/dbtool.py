import sys
import mysql.connector
# from loguru import logger
import os
import logging
from logging.handlers import TimedRotatingFileHandler

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Logger:
    def __init__(self, name="db_logger", log_dir="logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        file_handler = TimedRotatingFileHandler(filename=f'{log_dir}/{name}.log', when='midnight', interval=1, backupCount=7)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

# LOG_FILE = ".log"
# ROTATION_TIME = "02:00"
# DB_LOG_FILE_NAME = 'dblog'

# class DBLogger:
#     def __init__(self, name="db_access", log_dir="logs", debug=False):
#         if not os.path.exists(log_dir):
#             os.makedirs(log_dir)
#         log_file_path = os.path.join(log_dir, name+LOG_FILE)
#         #print(f'{log_file_path}')
#         # Remove default loguru handler
#         logger.remove()

#         # Add console handler with a specific log level
#         level = "DEBUG" if debug else "INFO"
#         logger.add(sys.stdout, level=level)
#         # Add file handler with a specific log level and timed rotation
#         logger.add(log_file_path, rotation=ROTATION_TIME, level="DEBUG", enqueue=True)
#         self.logger = logger

class DBHandler:
    def __init__(self, dbname) -> None:        
        mysql_db_config = {
            "host": '10.101.9.50',
            "user": 'root',
            "password": 'newpass',
            "database": dbname
        }
        self.db_connection = mysql.connector.connect(**mysql_db_config)
        self.db_cursor = self.db_connection.cursor()
        self.error_flag = False
        self.error_message = ''
        self.LOG = Logger(name="db_access", log_dir="logs").logger

        if self.db_connection.is_connected():
            self.error_flag = True
            self.error_message = f"Successfully connect mysql database {dbname}"
            self.LOG.debug(f"Successfully connect mysql database - {dbname}")
        else:
            self.error_flag = False
            self.error_message = f"Something goes wrong with MySQL DB {dbname}"
            self.LOG.debug(f"Something goes wrong with MySQL DB - {dbname}")
            #sys.exit(1)

    def geterror(self):
        return self.error_flag, self.error_message
    
    def execute_query(self, query, params=()):
        if not self.db_connection.is_connected():
            self.LOG.debug(f'Connection is lost, reconnect')    
            self.db_connection.reconnect()
            self.db_cursor = self.db_connection.cursor()

        self.db_cursor.execute(query, params)
        if query.strip().startswith("SELECT"):
            pass
        else:
            self.db_connection.commit()
        self.LOG.debug(f"query is [{query}], param is [{params}]")    

    def fetchall(self):
        return self.db_cursor.fetchall()
    
    def fetchone(self):
        return self.db_cursor.fetchone()

if __name__ == '__main__':
    dbh = DBHandler('codebase')
    dbh.db_connection.close()
    query = 'SELECT * FROM method_info WHERE ID=1234'
    dbh.execute_query(query)
    
    res = dbh.fetchone()
    if res:
        dbh.LOG.debug('query is OK')
    else:
        dbh.LOG.debug('query failed')