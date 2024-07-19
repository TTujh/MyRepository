"""Module scanner response for initialization GUI and connection to scanning device"""

import time
import serial
import os
import configparser
import threading
import sql_connection
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton, QMessageBox


class MainWindow(QWidget):
    ini_port: serial.Serial

    def __init__(self) -> None:
        super().__init__()
        self.initialize_ui()
        self.config = self.read_config()
        self.is_ini_exists()

    def initialize_ui(self) -> None:
        self.setFixedSize(720, 180)
        self.setStyleSheet('background-color: grey')
        self.setWindowTitle('Сканнер кода с datamatrix')
        self.set_up_window()
        self.show()

    def read_config(self) -> tuple:
        path = os.getcwd() + '/settings.ini'
        config = configparser.ConfigParser()
        config.read(path)
        self.dbname = config.get("DataBase", "dbname")
        self.user = config.get("DataBase", "user")
        self.password = config.get("DataBase", "password")
        self.host = config.get("DataBase", "host")
        self.port = config.get("DataBase", "port")
        return config.get("COM", "path"), config.get("BAUD", "baudrate")

    def initialize_port(self) -> None:
        while self.ini_port.is_open:
            data = self.ini_port.readline().decode().strip()
            if data:
                self.scanner_field.setText(data)

        self.start_checking_for_connection()
        self.process.join()

    def set_up_window(self) -> None:
        self.grid = QGridLayout()

        self.curr_lable = QLabel('<font color="#b0afaf"> Подключение: </front><font color="red"> НЕТ </font>')
        self.grid.addWidget(self.curr_lable, 0, 0)

        self.lable = QLabel('Полученный код с устройства сканирования')
        self.lable.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.lable, 2, 0, 1, 4)

        self.scanner_field = QLineEdit()
        self.grid.addWidget(self.scanner_field, 3, 0, 1, 4)

        self.showInformation = QPushButton('🛈 Информация о коде')
        self.showInformation.setFixedSize(170, 35)
        self.showInformation.setStyleSheet('background-color: #808080')
        self.showInformation.clicked.connect(self.grab_from_database)
        self.grid.addWidget(self.showInformation, 4, 0)

        self.clipboard = QPushButton('⊂–⊃ Скопировать')
        self.clipboard.setFixedSize(170, 35)
        self.clipboard.setStyleSheet('background-color: #808080')
        self.clipboard.clicked.connect(self.clipboard_copy)
        self.grid.addWidget(self.clipboard, 4, 1)

        self.reset_button = QPushButton('Сброс')
        self.reset_button.setFixedSize(170, 35)
        self.reset_button.setStyleSheet('background-color: #808080')
        self.reset_button.clicked.connect(self.scanner_field.clear)
        self.grid.addWidget(self.reset_button, 4, 2)

        self.exit_button = QPushButton('Выход')
        self.exit_button.setFixedSize(170, 35)
        self.exit_button.setStyleSheet('background-color: #ff0f00')
        self.exit_button.clicked.connect(self.close_application)
        self.grid.addWidget(self.exit_button, 4, 3)

        self.setLayout(self.grid)

    def close_application(self) -> None:
        self.ini_port.close()
        self.closeEvent()

    def start_scanning(self) -> None:
        self.process = threading.Thread(target=self.initialize_port)
        self.process.daemon = True
        self.process.start()

    def start_checking_for_connection(self) -> None:
        self.process2 = threading.Thread(target=self.connection_checking)
        self.process2.daemon = True
        self.process2.start()

    def clipboard_copy(self) -> None:
        if self.scanner_field.text() != "":
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{self.scanner_field.text()}")

    def grab_from_database(self) -> None:
        if self.scanner_field.text():
            data = sql_connection.PostgresData(dbname=self.dbname, user=self.user, password=self.password,
                                               host=self.host, port=self.port)
            QMessageBox.information(self, "Сопутсвующие характеристики кода",
                                    data.fetch_data_from_sql_table(
                                        self.scanner_field.text().encode().decode('unicode-escape').encode()),
                                    QMessageBox.StandardButton.Ok)

    def is_ini_exists(self) -> None:
        try:
            self.ini_port = serial.Serial(self.config[0], baudrate=int(self.config[1]))
            self.start_scanning()
            self.curr_lable.setText('<font color="#b0afaf"> Подлкючение: </front><font color="green"> ДА </font>')

        except Exception:
            QMessageBox.warning(self, "Ошибка подключения",
                                f"Ошибка при попытке подключиться через порт {self.config[0]} c бод-частотой {self.config[1]}\nУбедитесь в корректности данных файла инициализации settings.ini ([COM], [BAUD])")
            self.start_checking_for_connection()

    def connection_checking(self) -> None:
        while True:
            time.sleep(2)
            try:
                self.ini_port = serial.Serial(self.config[0], baudrate=int(self.config[1]))
                self.curr_lable.setText('<font color="#b0afaf"> Подлкючение: </front><font color="green"> ДА </font>')
                self.start_scanning()
                break
            except:
                self.curr_lable.setText('<font color="#b0afaf"> Подключение: </front><font color="red"> НЕТ </font>')
        self.process2.join()
