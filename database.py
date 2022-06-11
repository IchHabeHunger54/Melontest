import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self, user: str, pw: str, host: str, db: str):
        self.user = user
        self.pw = pw
        self.host = host
        self.db = db
        pass

    def execute(self, query: str):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(user=self.user, password=self.pw, host=self.host, database=self.db)
            if connection.is_connected():
                cursor = connection.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                connection.commit()
                return result
        except Error as e:
            print('Caught SQL Error: ', e)
        finally:
            if connection is not None and connection.is_connected():
                if cursor is not None:
                    cursor.close()
                connection.close()
