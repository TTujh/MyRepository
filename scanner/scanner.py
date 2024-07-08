import time

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QLineEdit, QGridLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import sys
import serial
import os
import configparser
import threading
import sqlConnect


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()
        self.initializeUI()
        self.flag = True
        self.config = self.readConfig()
        self.all_scanned_codes = set()
        self.isIniExists()
        self.startScanning()

    def initializeUI(self):

        self.setFixedSize(700, 150)
        self.setStyleSheet('background-color: grey')
        self.setWindowTitle('Symbol Bar Code Scanner')
        self.setUpWindow()
        self.show()

    def readConfig(self):

        path = os.getcwd() + '/settings.ini'
        config = configparser.ConfigParser()
        config.read(path)
        return config.get("COM", "path"), config.get("BAUD", "baudrate")

    def initializePort(self):
        self.ini_port = serial.Serial(self.config[0], baudrate=int(self.config[1]))
        while self.ini_port.is_open:
            data = self.ini_port.readline().decode().strip()
            if data:
                self.scanner_field.setText(data)
                self.all_scanned_codes.add(data)


    def setUpWindow(self):

        self.grid = QGridLayout()

        self.lable = QLabel('<b>Данные с штрих-кода</b>')
        self.lable.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.lable, 0, 1, 1, 2)

        self.scanner_field = QLineEdit()
        # Надо проверить, чтобы писать нельзя было, а копировать можно из поля.
        # self.scanner_field.setDisabled(True)
        self.grid.addWidget(self.scanner_field, 1, 0, 1, 4)

        self.start_button = QPushButton('Сброс')
        self.start_button.setStyleSheet('background-color: #808080')
        self.start_button.clicked.connect(self.scanner_field.clear)
        self.grid.addWidget(self.start_button, 2, 0)

        self.clipboard = QPushButton('Скопировать')
        self.clipboard.setStyleSheet('background-color: #808080')
        self.clipboard.clicked.connect(self.clipBoardCopy)
        self.grid.addWidget(self.clipboard, 2, 1)

        self.showInformation = QPushButton('Информация о коде')
        self.showInformation.setStyleSheet('background-color: #808080')
        self.showInformation.clicked.connect(self.grabFromDB)
        self.grid.addWidget(self.showInformation, 2, 2)

        self.exit_button = QPushButton('Выход')
        self.exit_button.setStyleSheet('background-color: red')
        self.exit_button.clicked.connect(self.closeApplication)
        self.grid.addWidget(self.exit_button, 2, 3)

        self.setLayout(self.grid)

    def closeApplication(self):
        self.ini_port.close()
        self.closeEvent()

    def startScanning(self):

        self.process = threading.Thread(target=self.initializePort)
        self.process.daemon = True
        self.process.start()

    def clipBoardCopy(self):
        if self.scanner_field.text() != "":
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{self.scanner_field.text()}")

    def grabFromDB(self):
        if len(self.scanner_field.text()):
            QMessageBox.information(self, "Сопутсвующие характеристики кода",
                                    sqlConnect.connectToSendData((self.scanner_field.text())),
                                    QMessageBox.StandardButton.Ok)

    def isIniExists(self):
        try:
            ini = serial.Serial(self.config[0], baudrate=int(self.config[1]))
            ini.close()
        except Exception:
            QMessageBox.warning(self, "Ошибка подключения",
                                f"Ошибка при попытке подключиться через порт {self.config[0]} c бод-частотой {self.config[1]}\nУбедитесь в корректности данных файла инициализации settings.ini ([COM], [BAUD])")
