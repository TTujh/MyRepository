"""Module sql_connection response for connection to local/remote SQL database"""

import psycopg2 as psql
import datetime


class RemotePostgresDatabase:
    connection: psql.connect

    def __init__(self, dbname: str, user: str, password: str, host: str, port: str) -> None:
        self.connection = psql.connect(dbname=dbname,
                                       user=user,
                                       password=password,
                                       host=host,
                                       port=port)

        self._information, self._columns = [], []
        self.cursor = self.connection.cursor()

    def _get_code_information(self, code: bytes) -> None:
        code = code.decode('unicode_escape').encode()
        self.cursor.execute(
            f"SELECT DISTINCT * FROM codes_input i LEFT JOIN codes_input_ext e ON i.id = e.codes_input_id WHERE code_hex = '{code.hex()}';"
        )
        self._put_code_information()

        self.cursor.execute(
            f"SELECT DISTINCT * FROM codes_output WHERE code_hex = '{code.hex()}';"
        )
        self._put_code_information()

    def _put_code_information(self) -> None:
        fetchall = self.cursor.fetchall()
        if len(fetchall) != 0:
            self._columns.append([desc[0] for desc in self.cursor.description])
            self._information.append(fetchall)
            self.cursor.execute(f"SELECT * FROM products WHERE id = '{self._information[0][0][3]}';")
            self._columns.append([desc[0] for desc in self.cursor.description])
            self._information.append(self.cursor.fetchall())

    def get_answer(self, code: bytes) -> str:
        self._get_code_information(code=code)
        answer = 'ИНФОРМАЦИЯ О КОДЕ:\n'
        if len(self._columns) != 0:
            for i in range(len(self._columns[0])):
                if self._information[0][0][i]:
                    answer += f'{self._columns[0][i]} — {self._information[0][0][i]}\n'
        else:
            answer += 'ИНФОРМАЦИЯ ОТСУТСВУЕТ В ВЫБРАННОЙ БАЗЕ ДАННЫХ.\n'
        answer += '----------------------------------------------------------------------------'
        return answer
