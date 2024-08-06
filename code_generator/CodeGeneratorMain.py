from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton,
                             QComboBox, QRadioButton, QHBoxLayout, QButtonGroup, QTextEdit, QSpinBox, QStackedWidget,
                             QVBoxLayout, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
import json
import sys
import os
import configparser
import base64


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
        self.code = list()
        self.serial_end = '0'
        self.generate_flag = False
        self.readConfig()

    def initializeUI(self):
        self.showFullScreen()
        self.setWindowTitle('Генератор кодов маркировки')
        self.setUpWindow()
        self.show()

    def setUpWindow(self):
        # create grid layout
        self.grid = QGridLayout()
        self.vboxlay = QVBoxLayout()

        # gtin
        self.sub_layout_for_id = QHBoxLayout()
        self.gtin_lable = QLabel('<b>GTIN:</b>')
        self.sub_layout_for_id.addWidget(self.gtin_lable)

        # fill first sub layout
        # id combox (01, 02)
        self.box_id = QComboBox()
        self.box_id.addItems(['01', '02'])
        self.sub_layout_for_id.addWidget(self.box_id)

        # GTIN edit field (14 symbols)
        self.gtin = QLineEdit()
        self.gtin.setMaxLength(14)
        self.sub_layout_for_id.addWidget(self.gtin)
        self.vboxlay.addLayout(self.sub_layout_for_id)

        # serial
        self.sub_layout_for_serial = QHBoxLayout()
        self.sub_layout_for_serial.addWidget(QLabel('<b>Serial:</b>'))
        self.sub_layout_for_serial.addWidget(QLabel('21'))
        self.sub_layout_for_serial.addWidget(QLabel('Length:'))
        self.serial_length_spin = QSpinBox(value=6)
        self.serial_length_spin.setRange(2, 20)
        self.sub_layout_for_serial.addWidget(self.serial_length_spin)
        self.sub_layout_for_serial.addWidget(QLabel('Start:'))
        self.serial_start_edit = QLineEdit()
        self.sub_layout_for_serial.addWidget(self.serial_start_edit)
        self.vboxlay.addLayout(self.sub_layout_for_serial)

        # sub layout for suffix
        self.stacked_layout = QStackedWidget()

        self.combox_decode = QComboBox()
        self.combox_decode.addItem('91/92 (44)')
        self.combox_decode.addItem('91/92 (85)')
        self.combox_decode.addItem('93')
        self.combox_decode.addItem('free')
        self.combox_decode.currentIndexChanged.connect(self.switchType)

        w1 = QWidget()
        self.sub_layout1 = QHBoxLayout()
        self.tag91_1 = QLabel('91:')
        self.edit_tag91_1 = QLineEdit()
        self.edit_tag91_1.setMaxLength(4)
        self.tag92_1 = QLabel('92:')
        self.edit_tag92_1 = QLineEdit()
        self.edit_tag92_1.setMaxLength(44)
        self.sub_layout1.addWidget(self.tag91_1)
        self.sub_layout1.addWidget(self.edit_tag91_1)
        self.sub_layout1.addWidget(self.tag92_1)
        self.sub_layout1.addWidget(self.edit_tag92_1)
        w1.setLayout(self.sub_layout1)

        w2 = QWidget()
        self.sub_layout2 = QHBoxLayout()
        self.tag91_2 = QLabel('91:')
        self.edit_tag91_2 = QLineEdit()
        self.edit_tag91_2.setMaxLength(4)
        self.tag92_2 = QLabel('92:')
        self.edit_tag92_2 = QLineEdit()
        self.edit_tag92_2.setMaxLength(85)
        self.sub_layout2.addWidget(self.tag91_2)
        self.sub_layout2.addWidget(self.edit_tag91_2)
        self.sub_layout2.addWidget(self.tag92_2)
        self.sub_layout2.addWidget(self.edit_tag92_2)
        w2.setLayout(self.sub_layout2)

        w3 = QWidget()
        self.sub_layout3 = QHBoxLayout()
        self.tag93 = QLabel('93:')
        self.edit_tag93 = QLineEdit()
        self.edit_tag93.setMaxLength(4)
        self.sub_layout3.addWidget(self.tag93)
        self.sub_layout3.addWidget(self.edit_tag93)
        w3.setLayout(self.sub_layout3)

        w4 = QWidget()
        self.sub_layout4 = QHBoxLayout()
        self.tag_free = QLabel('free:')
        self.edit_tag_free = QLineEdit()
        self.edit_tag_free.setMaxLength(32767)
        self.sub_layout4.addWidget(self.tag_free)
        self.sub_layout4.addWidget(self.edit_tag_free)
        w4.setLayout(self.sub_layout4)

        self.stacked_layout.addWidget(w1)
        self.stacked_layout.addWidget(w2)
        self.stacked_layout.addWidget(w3)
        self.stacked_layout.addWidget(w4)

        self.sub_out = QHBoxLayout()
        self.sub_out.addWidget(self.combox_decode)
        self.sub_out.addWidget(self.stacked_layout)

        self.vboxlay.addLayout(self.sub_out)

        # quantity field
        self.sub_layout_for_generate = QHBoxLayout()
        self.quantity_edit = QLineEdit('1')
        self.quantity_edit.setFixedWidth(120)
        self.sub_layout_for_generate.addWidget(QLabel('<b>Quantity</b> (under 1 mln):'))
        self.sub_layout_for_generate.addWidget(self.quantity_edit)

        # generate button
        self.generate_button = QPushButton('Generate')
        # self.generate_button.setStyleSheet('background-color: #647991')

        self.generate_button.clicked.connect(self.codeGeneration)
        self.sub_layout_for_generate.addWidget(self.generate_button)
        self.vboxlay.addLayout(self.sub_layout_for_generate)

        # group of radiobuttons
        self.radiobutton_txt_view = QRadioButton('.txt')
        self.radiobutton_txt_view.setChecked(True)
        self.radiobutton_json_view = QRadioButton('.json')
        self.group_buttons_view = QButtonGroup()
        self.group_buttons_view.addButton(self.radiobutton_txt_view)
        self.group_buttons_view.addButton(self.radiobutton_json_view)
        self.group_buttons_view.buttonClicked.connect(self.supportingFunc)

        self.radiobutton_txt_format = QRadioButton('.txt')
        self.radiobutton_b64_format = QRadioButton('.b64')
        self.radiobutton_txt_format.setChecked(True)
        self.group_buttons_format = QButtonGroup()
        self.group_buttons_format.addButton(self.radiobutton_txt_format)
        self.group_buttons_format.addButton(self.radiobutton_b64_format)
        self.group_buttons_format.buttonClicked.connect(self.supportingFunc)

        self.sub_layout_for_buttons_view = QVBoxLayout()
        self.sub_layout_for_buttons_view.addWidget(self.radiobutton_txt_view)
        self.sub_layout_for_buttons_view.addWidget(self.radiobutton_json_view)

        self.sub_layout_for_buttons_format = QVBoxLayout()
        self.sub_layout_for_buttons_format.addWidget(self.radiobutton_txt_format)
        self.sub_layout_for_buttons_format.addWidget(self.radiobutton_b64_format)

        self.sub_ratio_layout = QHBoxLayout()
        self.sub_ratio_layout.addWidget(QLabel('View:'))
        self.sub_ratio_layout.addLayout(self.sub_layout_for_buttons_view)
        self.sub_ratio_layout.addWidget(QLabel('Format:'))
        self.sub_ratio_layout.addLayout(self.sub_layout_for_buttons_format)

        self.vboxlay.addLayout(self.sub_ratio_layout)
        self.grid.addLayout(self.vboxlay, 0, 0, 3, 1)

        # text field
        self.text_field = QTextEdit()
        self.grid.addWidget(self.text_field)
        self.sub_layout_for_buttons_2 = QHBoxLayout()

        # group of bottom buttons
        self.copy_button = QPushButton('Copy')
        # self.copy_button.setStyleSheet('background-color: #9b776f')
        self.copy_button.clicked.connect(self.clipBoardCopy)

        self.reset_button = QPushButton('Reset')
        # self.reset_button.setStyleSheet('background-color: #976981')
        self.reset_button.clicked.connect(self.text_field.clear)

        self.save_button = QPushButton('Save...')
        # self.save_button.setStyleSheet('background-color: #866491')
        self.save_button.clicked.connect(self.saveFunc)

        self.exit_button = QPushButton('Exit')
        self.exit_button.setStyleSheet('background-color: red')
        self.exit_button.clicked.connect(self.closeEvent)
        self.sub_layout_for_buttons_2.addWidget(self.copy_button)
        self.sub_layout_for_buttons_2.addWidget(self.reset_button)
        self.sub_layout_for_buttons_2.addWidget(self.save_button)
        self.sub_layout_for_buttons_2.addWidget(self.exit_button)
        self.grid.addLayout(self.sub_layout_for_buttons_2, 6, 0, 1, 4)
        self.setLayout(self.grid)

    def switchType(self, index):
        self.stacked_layout.setCurrentIndex(index)

    def codeGeneration(self, **kwargs):
        self.generate_flag = True
        error = self.errorRise()
        if error == "":
            pass
        else:
            QMessageBox.warning(self, "Сообщение об ошибке", error, QMessageBox.StandardButton.Ok)
            return
        self.code.clear()
        self.text_field.clear()
        id = self.box_id.currentText()
        GTIN = self.gtin.text()
        count_of_symbols_in_serial = int(self.serial_length_spin.text())
        serial_id = int(self.serial_start_edit.text())
        suffix_id = self.combox_decode.currentText()
        if suffix_id == '91/92 (44)':
            serial_current = ''
            for i in range(int(self.quantity_edit.text())):
                serial_current = '0' * (count_of_symbols_in_serial - len(str(serial_id + i))) + str(serial_id + i)
                self.code.append(
                    id + GTIN + '21' + serial_current + '␝' + '91' + self.edit_tag91_1.text() + '␝' + '92' + self.edit_tag92_1.text())
            self.codeRemasteringB64(self.group_buttons_format.checkedButton().text())
            self.text_field.setText(self.codeRemasteringJson(self.group_buttons_view.checkedButton().text()))
            self.serial_end = int(serial_current.strip('0'))
        elif suffix_id == '91/92 (85)':
            serial_current = ''
            for i in range(int(self.quantity_edit.text())):
                serial_current = '0' * (count_of_symbols_in_serial - len(str(serial_id + i))) + str(serial_id + i)
                self.code.append(
                    id + GTIN + '21' + serial_current + '␝' + '91' + self.edit_tag91_2.text() + '␝' + '92' + self.edit_tag92_2.text())
            self.codeRemasteringB64(self.group_buttons_format.checkedButton().text())
            self.text_field.setText(self.codeRemasteringJson(self.group_buttons_view.checkedButton().text()))
            self.serial_end = int(serial_current.strip('0'))
        elif suffix_id == '93':
            serial_current = ''
            for i in range(int(self.quantity_edit.text())):
                serial_current = '0' * (count_of_symbols_in_serial - len(str(serial_id + i))) + str(serial_id + i)
                self.code.append(id + GTIN + '21' + serial_current + '␝' + '93' + self.edit_tag93.text())
            self.codeRemasteringB64(self.group_buttons_format.checkedButton().text())
            self.text_field.setText(self.codeRemasteringJson(self.group_buttons_view.checkedButton().text()))
            self.serial_end = int(serial_current.strip('0'))
        else:
            serial_current = ''
            for i in range(int(self.quantity_edit.text())):
                serial_current = '0' * (count_of_symbols_in_serial - len(str(serial_id + i))) + str(serial_id + i)
                self.code.append(id + GTIN + '21' + serial_current + '␝' + self.edit_tag_free.text())
            self.codeRemasteringB64(self.group_buttons_format.checkedButton().text())
            self.text_field.setText(self.codeRemasteringJson(self.group_buttons_view.checkedButton().text()))
            self.serial_end = int(serial_current.strip('0'))

    def codeRemasteringB64(self, format):
        if format == '.b64':
            current_code = list()
            for i in self.code:
                code_string_bytes = i.encode('utf-8')
                base64_bytes = base64.b64encode(code_string_bytes)
                base64_string = base64_bytes.decode("ascii")
                current_code.append(base64_string)
            self.code = current_code

    def codeRemasteringJson(self, view):
        if view == '.json':
            current = {"codes": []}
            for i in self.code:
                current["codes"].append(i)
            to_print_json = json.dumps(current, indent=4, ensure_ascii=False)
            return to_print_json
        else:
            to_print_txt = ''
            for x in self.code:
                to_print_txt += x + '\n'
            return to_print_txt

    def clipBoardCopy(self):
        if self.text_field.toPlainText() != "":
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{self.text_field.toPlainText()}")

    def errorRise(self):
        errDesc = ""
        if self.gtin.text().isdigit():
            pass
        else:
            errDesc += "Поле GTIN должно состоять только из цифр.\n"
        if int(self.serial_length_spin.text()) >= len(
                    self.serial_start_edit.text()) and self.serial_start_edit.text().isdigit():
            pass
        else:
            errDesc += "Длина поля Serial превышает указанную длину или поле Serial не является целым числом.\n"
        if self.combox_decode.currentText() == '91/92 (44)' or self.combox_decode.currentText() == '91/92 (85)':
            if ((len(self.edit_tag91_1.text()) != 0 and len(
                    self.edit_tag92_1.text()) != 0) and self.combox_decode.currentText() == '91/92 (44)') or (
                    (len(
                        self.edit_tag91_2.text()) != 0 and len(
                        self.edit_tag92_2.text()) != 0) and self.combox_decode.currentText() == '91/92 (85)'):
                pass
            else:
                errDesc += "Убедитесь что поля 91 и 92 заполнены.\n"
        elif self.combox_decode.currentText() == '93':
            if len(self.edit_tag93.text()) != 0:
                pass

            else:
                errDesc += "Убедитесь что полe 93 заполненo.\n"

        if self.quantity_edit.text().isdigit():
            pass
        else:
            errDesc += "Некорректный формат поля Quantity.\n"

        return errDesc



    def readConfig(self):
        path = os.getcwd() + '/config.ini'
        config = configparser.ConfigParser()
        config.read(path)

        self.box_id.setCurrentText(config.get("GTIN_ID", "id"))
        self.gtin.setText(config.get("GTIN", "gtin"))
        self.serial_start_edit.setText(config.get("SERIAL", "start"))
        self.edit_tag91_1.setText(config.get("NINE_ONE_ONE", "text"))
        self.edit_tag92_1.setText(config.get("NINE_TWO_ONE", "text"))
        self.edit_tag91_2.setText(config.get("NINE_ONE_TWO", "text"))
        self.edit_tag92_2.setText(config.get("NINE_TWO_TWO", "text"))
        self.edit_tag93.setText(config.get("NINE_THREE", "text"))
        self.edit_tag_free.setText(config.get("FREE", "text"))
        self.combox_decode.setCurrentText(config.get("SUFFIX", "value"))
        # self.stacked_layout.setCurrentIndex(
        #     self.combox_decode.currentIndex()
        # )
        self.quantity_edit.setText(config.get("QUANTITY", "value"))

    def closeEvent(self, event):
        path = os.getcwd() + '/config.ini'
        config = configparser.ConfigParser()
        config.read(path)
        if self.generate_flag:
            self.serial_end = str(int(self.serial_start_edit.text()) + int(self.quantity_edit.text()))
        else:
            self.serial_end = self.serial_start_edit.text()

        config["GTIN_ID"]["id"] = self.box_id.currentText()
        config["GTIN"]["gtin"] = self.gtin.text()
        config["SERIAL"]["start"] = self.serial_end
        config["NINE_ONE_ONE"]["text"] = self.edit_tag91_1.text()
        config["NINE_TWO_ONE"]["text"] = self.edit_tag92_1.text()
        config["NINE_ONE_TWO"]["text"] = self.edit_tag91_2.text()
        config["NINE_TWO_TWO"]["text"] = self.edit_tag92_2.text()
        config["NINE_THREE"]["text"] = self.edit_tag93.text()
        config["FREE"]["text"] = self.edit_tag_free.text()
        config["SUFFIX"]["value"] = self.combox_decode.currentText()
        config["QUANTITY"]["value"] = self.quantity_edit.text()

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        sys.exit(0)

    def supportingFunc(self):
        if len(self.text_field.toPlainText()) != 0:
            self.codeGeneration()

    def saveFunc(self):
        path_to, _ = QFileDialog.getSaveFileName(self, "Сохранение файла в выбранном формате.", "", "Text Files (*.txt);;Json Files (*.json)")
        try:
            if self.group_buttons_view.checkedButton().text() == '.txt':
                with open(str(path_to), 'w') as file:
                    file.write(self.text_field.toPlainText())
                    QMessageBox.information(self, "Сохранение файла",
                                            f"Файл успешно сохранен в {path_to}")
                    return
            else:
                with open(str(path_to), 'w') as file:
                    file.write(self.text_field.toPlainText())
                    QMessageBox.information(self, "Сохранение файла", f"Файл успешно сохранен в {path_to}")
                    return
        except:
            QMessageBox.information(self, "Сохранение файла", "Ошибка при сохранении файла, убедитесь в корректности указанного пути, имени файла, параметров генерации (View и Format)")
