"""Module sql_connection response for connection to local/remote SQL database"""

import datetime
import psycopg2 as psql
from dataclasses import dataclass
from collections import namedtuple


@dataclass
class Connection:
    dbname: str
    user: str
    password: str
    host: str
    port: str


class PostgresData(Connection):
    input_codes: namedtuple
    output_codes: namedtuple
    answer: str = "🛈 ИНФОРМАЦИЯ О КОДЕ\n\n"

    def fetch_data_from_sql_table(self, code: bytes) -> str:
        InputData = namedtuple('InputData',
                               ['id', 'added_date', 'added_time', 'product_id', 'code_hex', 'expiration_date', 'status',
                                'action_date', 'code_str', 'printing_job_id', 'order_num', 'product_gtin'])
        OutputData = namedtuple('OutputData',
                                ['id', 'product_gtin', 'registry_date', 'session_id', 'line_number', 'code_datamatrix',
                                 'code_hex', 'job_id', 'added_date', 'added_time', 'group_id', 'roll_id', 'uploaded',
                                 'product_id'])
        connection = psql.connect(dbname=self.dbname, user=self.user, password=self.password, host=self.host,
                                  port=self.port)
        code = code.decode('unicode-escape').encode()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM codes_input WHERE code_hex= '%s';" % code.hex())
        for i in map(InputData._make, cursor.fetchall()):
            self.input_codes = i
        cursor.execute("SELECT * FROM codes_output WHERE code_hex = '%s';" % code.hex())
        for i in map(OutputData._make, cursor.fetchall()):
            self.output_codes = i
        self.answer += "Входные данные:\n"
        for x, y in self.input_codes._asdict().items():
            self.answer += f"\t{x} :  {y}\n"
        self.answer += "Выходные данные:\n"
        for x, y in self.output_codes._asdict().items():
            self.answer += f"\t{x} :  {y}\n"

        cursor.close()
        connection.close()
        return self.answer
