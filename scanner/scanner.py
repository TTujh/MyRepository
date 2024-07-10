import sys
import serial
import os
import configparser
import threading
import sql_connection
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt


class MainWindow(QWidget):
    ini_port: serial.Serial

    def __init__(self) -> None:
        super().__init__()
        self.initialize_ui()
        self.flag = True
        self.config = self.read_config()
        self.all_scanned_codes = set()
        self.is_ini_exists()
        self.start_scanning()

    def initialize_ui(self) -> None:
        self.setFixedSize(700, 150)
        self.setStyleSheet('background-color: grey')
        self.setWindowTitle('Symbol Bar Code Scanner')
        self.set_up_window()
        self.show()

    def read_config(self) -> tuple:
        path = os.getcwd() + '/settings.ini'
        config = configparser.ConfigParser()
        config.read(path)
        self.__dbname = config.get("DataBase", "dbname")
        self.__user = config.get("DataBase", "user")
        self.__password = config.get("DataBase", "password")
        self.__host = config.get("DataBase", "host")
        self.__port = config.get("DataBase", "port")
        return config.get("COM", "path"), config.get("BAUD", "baudrate")

    def initialize_port(self) -> None:
        self.ini_port = serial.Serial(self.config[0], baudrate=int(self.config[1]))
        while self.ini_port.is_open:
            data = self.ini_port.readline().decode().strip()
            if data:
                self.scanner_field.setText(data)
                self.all_scanned_codes.add(data)

    def set_up_window(self) -> None:
        self.grid = QGridLayout()

        self.lable = QLabel('<b>Данные с штрих-кода</b>')
        self.lable.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.lable, 0, 1, 1, 2)

        self.scanner_field = QLineEdit()
        self.grid.addWidget(self.scanner_field, 1, 0, 1, 4)

        self.start_button = QPushButton('Сброс')
        self.start_button.setStyleSheet('background-color: #808080')
        self.start_button.clicked.connect(self.scanner_field.clear)
        self.grid.addWidget(self.start_button, 2, 0)

        self.clipboard = QPushButton('Скопировать')
        self.clipboard.setStyleSheet('background-color: #808080')
        self.clipboard.clicked.connect(self.clipboard_copy)
        self.grid.addWidget(self.clipboard, 2, 1)

        self.showInformation = QPushButton('Информация о коде')
        self.showInformation.setStyleSheet('background-color: #808080')
        self.showInformation.clicked.connect(self.grab_from_database)
        self.grid.addWidget(self.showInformation, 2, 2)

        self.exit_button = QPushButton('Выход')
        self.exit_button.setStyleSheet('background-color: red')
        self.exit_button.clicked.connect(self.close_application)
        self.grid.addWidget(self.exit_button, 2, 3)

        self.setLayout(self.grid)

    def close_application(self) -> None:
        self.ini_port.close()
        self.closeEvent()

    def start_scanning(self) -> None:
        self.process = threading.Thread(target=self.initialize_port)
        self.process.daemon = True
        self.process.start()

    def clipboard_copy(self) -> None:
        if self.scanner_field.text() != "":
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{self.scanner_field.text()}")

    def grab_from_database(self) -> None:
        if self.scanner_field.text():
            database = sql_connection.RemotePostgresDatabase(dbname=self.__dbname,
                                                             user=self.__user,
                                                             password=self.__password,
                                                             host=self.__host,
                                                             port=self.__port)
            QMessageBox.information(self, "Сопутсвующие характеристики кода",
                                    database.get_answer(self.scanner_field.text().encode()),
                                    QMessageBox.StandardButton.Ok)

    def is_ini_exists(self) -> None:
        try:
            ini = serial.Serial(self.config[0], baudrate=int(self.config[1]))
            ini.close()
        except Exception:
            QMessageBox.warning(self, "Ошибка подключения",
                                f"Ошибка при попытке подключиться через порт {self.config[0]} c бод-частотой {self.config[1]}\nУбедитесь в корректности данных файла инициализации settings.ini ([COM], [BAUD])")
