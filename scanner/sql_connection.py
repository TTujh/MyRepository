"""Module sql_connection response for connection to local/remote SQL database"""

import datetime
import psycopg2 as psql
from dataclasses import dataclass


@dataclass
class Connection:
    dbname: str
    user: str
    password: str
    host: str
    port: str


class PostgresData(Connection):

    def fetch_data_from_sql_table(self, code: bytes) -> str:
        connection = psql.connect(dbname=self.dbname, user=self.user, password=self.password, host=self.host,
                                  port=self.port)
        code = code.decode('unicode-escape').encode()
        cursor = connection.cursor()
        answer = "CODE INPUT:\n"
        cursor.execute("SELECT * FROM codes_input WHERE code_hex= '%s';" % code.hex())
        input_codes = cursor.fetchone()
        input_codes_desc = cursor.description
        cursor.execute("SELECT * FROM codes_output WHERE code_hex = '%s';" % code.hex())
        output_codes = cursor.fetchone()
        output_codes_desc = cursor.description
        for i in range(1, len(input_codes)):
            answer += f"\t{input_codes_desc[i][0]} --- {input_codes[i]}\n"
        answer += "CODE OUTPUT:\n"
        for i in range(1, len(output_codes)):
            answer += f"\t{output_codes_desc[i][0]} --- {output_codes[i]}\n"
        cursor.close()
        connection.close()
        return answer
