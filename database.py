import psycopg2


class Database:
    def __init__(self, database: dict):
        self.username = database['username']
        self.password = database['password']
        self.hostname = database['hostname']
        self.database = database['database']
        self.port = database['port']
        pass

    def execute(self, query: str):
        connection = None
        try:
            connection = psycopg2.connect(user=self.username, password=self.password, host=self.hostname, database=self.database, port=self.port)
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connection.commit()
            cursor.close()
            return result
        except (Exception, psycopg2.DatabaseError) as e:
            print('Caught SQL Error: ', e)
        finally:
            if connection is not None:
                connection.close()
