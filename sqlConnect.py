import psycopg2 as psql
import configparser
import os


def connectToSendData(code):
    path = os.getcwd() + '/settings.ini'
    config = configparser.ConfigParser()
    config.read(path)
    host = config.get("DataBase", "host")
    dbname = config.get("DataBase", "dbname")
    user = config.get("DataBase", "user")
    password = config.get("DataBase", "password")
    port = config.get("DataBase", "port")
    all_tables = ['codes_input', 'codes_output']
    where_code = []
    try:
        connection = psql.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        # connection.autocommit = True
        cursor = connection.cursor()
        for i in all_tables:
            cursor.execute(f"SELECT * FROM {i} WHERE code_hex = '{code}';")
            where_code.append(cursor.fetchall())
        cursor.close()
        connection.close()
        return max(where_code)
    except Exception as err:
        raise ConnectionError('Не удалось подключиться к базе данных')

    finally:
        connection.close()


connectToSendData('3031303436373030313933353031393732313571674657505836635468724b1d39334975477a')
