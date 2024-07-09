import psycopg2 as psql
import configparser
import os
import datetime


def connectToSendData(code):
    code_hex = code.encode().hex()
    path = os.getcwd() + '/settings.ini'
    config = configparser.ConfigParser()
    config.read(path)
    host = config.get("DataBase", "host")
    dbname = config.get("DataBase", "dbname")
    user = config.get("DataBase", "user")
    password = config.get("DataBase", "password")
    port = config.get("DataBase", "port")
    stdout = []
    colnames = []

    try:
        connection = psql.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT DISTINCT * FROM codes_input i LEFT JOIN codes_input_ext e ON i.id = e.codes_input_id WHERE code_hex = '{code_hex}';"
        )
        colnames.append([desc[0] for desc in cursor.description])
        stdout.append(cursor.fetchall())

        cursor.execute(
            f"SELECT DISTINCT * FROM codes_output o LEFT JOIN codes_output_ext e ON o.element_id = e.codes_output_id WHERE code_hex = '{code_hex}';"
        )
        colnames.append([desc[0] for desc in cursor.description])
        stdout.append(cursor.fetchall())


        if len(stdout[0]) > len(stdout[1]):
            index = 0
            cursor.execute(f"SELECT * FROM products WHERE id = '{stdout[index][0][3]}';")
            to_out = cursor.fetchall()
            colnames.append([desc[0] for desc in cursor.description])
        elif len(stdout[1]) > len(stdout[0]):
            index = 1
            cursor.execute(f"SELECT * FROM products WHERE id = '{stdout[index][0][3]}';")
            to_out = cursor.fetchall()
            colnames.append([desc[0] for desc in cursor.description])
        else:
            return '<b>Информация об отсканированном коде отсутствует.</b>'
        output_text = 'Информация об отсканированном коде:\n'
        for i in range(len(stdout[index][0])):
            if stdout[index][0][i]:
                output_text += f'{colnames[index][i]} – {stdout[index][0][i]}\n'
        output_text += '\nИнформация о сопутствующем коду товаре:\n'
        for x in range(1, len(colnames[2])):
            if len(to_out) > 0:
                output_text += f'{colnames[2][x]} – {to_out[0][x]}\n'
            else:
                output_text += "Информация отсутсвует."
                break

        cursor.close()
        connection.close()

        return output_text

    except Exception:
        raise ConnectionError('<b>Не удалось подключиться к базе данных</b>')

    finally:
        connection.close()


# print(connectToSendData('0104607015490015215CEiB%-YJE4P>93qvtx'))
