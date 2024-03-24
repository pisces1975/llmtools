import sys
from .logger import LOG
import mysql.connector

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

        if self.db_connection.is_connected():
            LOG.debug(f"Successfully connect mysql database {dbname}")
        else:
            LOG.error(f"Something goes wrong with MySQL DB {dbname}")    
            sys.exit(1)

    def execute_query(self, query, params=()):
        self.db_cursor.execute(query, params)
        if query.strip().startswith("SELECT"):
            pass
        else:
            self.db_connection.commit()

    def fetchall(self):
        return self.db_cursor.fetchall()
    
    def fetchone(self):
        return self.db_cursor.fetchone()