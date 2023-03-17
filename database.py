import psycopg2


class Database:
    def __init__(self, database: dict):
        self.username = database['username']
        self.password = database['password']
        self.hostname = database['hostname']
        self.database = database['database']
        self.port = database['port']

    def execute(self, query: str, *args) -> list[tuple]:
        try:
            with psycopg2.connect(user=self.username, password=self.password, host=self.hostname, database=self.database, port=self.port) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, args)
                    try:
                        result = cursor.fetchall()
                    except psycopg2.ProgrammingError as e:
                        result = None
                    connection.commit()
                    return result
        except (Exception, psycopg2.DatabaseError) as e:
            print('Caught SQL Error:', e)
