import io

from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QMainWindow, QPushButton, QGridLayout, QWidget, QMessageBox, QVBoxLayout, \
    QComboBox, QLabel, QHBoxLayout, QTextEdit
from PyQt6.QtCore import QSize, Qt
from PIL import Image, ImageDraw
from data_models import *

from hikrobot import *

__version__ = "0.2.0.a"

default_width = 100
default_height = 50


class MainWindow(QMainWindow):
    def __init__(self, image_bytes):
        super().__init__()
        self.setWindowTitle(f"InMark_DatamatrixImageViewer {__version__}")
        self.lock_redraw = False
        # self.dll = dll_
        # self.main_vbox_layout = QVBoxLayout()

        self.hik = Hikrobot()

        # self.image_callback = self.get_one_frame_callback  # self.get_one_frame_callback

        self.cam_callback = CamCallback()

        # self.image_callback_partial = partial(MainWindow.get_one_frame_callback, test = 13)

        self.controlPanel = ControlPanelView(self)
        self.controlPanel.searchBtn.clicked.connect(self.on_search)
        self.controlPanel.getversionBtn.clicked.connect(self.hik.get_sdk_version)
        self.controlPanel.connectBtn.clicked.connect(self.on_connect)
        self.controlPanel.disconnectBtn.clicked.connect(self.on_disconnect)
        self.controlPanel.startGrabbingBtn.clicked.connect(self.on_start_grabbing)
        self.controlPanel.stopGrabbingBtn.clicked.connect(self.on_stop_grabbing)
        self.controlPanel.setTriggerSourceBtn.clicked.connect(self.on_select_software_trigger)
        self.controlPanel.sendTriggerBtn.clicked.connect(self.on_trigger)
        self.controlPanel.triggerOnBtn.clicked.connect(self.on_trigger_enable)
        self.controlPanel.triggerOffBtn.clicked.connect(self.on_trigger_disable)
        self.controlPanel.getFrameTimeout.clicked.connect(self.on_get_frame_callback)
        self.controlPanel.testBtn.clicked.connect(self.on_test)

        self.cam_callback.it_is_time.connect(self.on_test)

        self.imageWidget = ImageView(image_bytes)

        v_log_layout = QVBoxLayout()
        self.log_pannel = QTextEdit()
        self.log_pannel.setFixedSize(400, 100)
        self.log_pannel.setEnabled(False)
        v_log_layout.addWidget(QLabel('Log output'))
        v_log_layout.addWidget(self.log_pannel)
        # v_log_layout.insertStretch(2, 10)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.controlPanel)
        h_layout.addWidget(self.imageWidget)
        # h_layout.insertStretch(2, 100)

        self.text_test = ""

        layout = QVBoxLayout()
        # layout.addWidget(self.controlPanel)
        layout.addLayout(h_layout)
        layout.addLayout(v_log_layout)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setMinimumSize(QSize(1600, 1200))

    def on_search(self):
        try:
            self.hik.search_devices()
        except Exception as e:
            print(e)

    # self.__call__(get_one_frame_callback)

    @staticmethod
    @CFUNCTYPE(c_void_p, POINTER(c_ubyte), POINTER(ImageOutInfoEx2), POINTER(c_char_p))
    def get_one_frame_callback(self, p_data, p_frame_info, p_user):
        print('image callback called')
        frame_info = p_frame_info.contents
        data_ = p_data.contents

        lenData = frame_info.nFrameLen
        bytesImage = (c_ubyte * lenData)
        print(f"address callback: {addressof(data_)}, data_: {data_}")
        image_data_carray = bytesImage.from_address(addressof(data_))  # addressof(castedImg
        img_to_save = []
        try:
            print(
                f"type of element: {type(image_data_carray)} {image_data_carray[0]}, {image_data_carray[1]}")
        except Exception as e:
            print(e)
        print(f"length of image data: {len(image_data_carray)}")

        # numpy.save("C:\\InAuto\\HikRobotCamera\\data", (image_data_carray))

        print(
            f"width: {frame_info.nWidth}, height: {frame_info.nHeight}, pixelFormat: {frame_info.enPixelType}, "
            f"enum: {MvCodeReaderGvspPixelType(c_uint(frame_info.enPixelType).value).name}")
        dataBrc = frame_info.pstCodeListEx.contents
        print(
            f"nFrameLen: {frame_info.nFrameLen}, dir: {dataBrc.__dir__()}\nBarcodeCount: {dataBrc.nCodeNum}")

    def update_image_from_callback(self, result):
        try:
            bytes = result[2]
            image = Image.open(io.BytesIO(bytes))
            # image = Image.new('RGB', (1280, 1024), (100, 120, 27))
            draw = ImageDraw.Draw(image)

            for item in result[1]:
                c_list = []
                print(item.coordinates)
                for coor in item.coordinates:
                    c_list.append((coor.x, coor.y))

                draw.polygon(c_list, outline=(0, 0xFE, 0), width=10)
            self.imageWidget.update_image(image)
        except Exception as e:
            print(e)

    def on_connect(self):
        try:
            if self.hik.create_handle()[0]:
                try:
                    if self.hik.open_device_session()[0]:
                        print("device session open successfully")
                        # self.hik.register_trigger_callback()
                        # self.hik.register_exception_callback()
                    else:
                        print("failed open session")
                except Exception as e:
                    print(e)
            else:
                print("failed create handle")
        except Exception as e:
            print(e)

    def on_get_frame(self):
        result = self.hik.get_one_frame_timeout()
        print(result[1])
        if result[0]:
            try:
                bytes = result[2]
                # print(bytes)
                image = Image.open(io.BytesIO(bytes))
                # image = Image.new('RGB', (1280, 1024), (100, 120, 27))
                draw = ImageDraw.Draw(image)

                for item in result[1]:
                    c_list = []
                    print(item.coordinates)
                    for coor in item.coordinates:
                        c_list.append((coor.x, coor.y))

                    draw.polygon(c_list, outline=(0, 0xFE, 0), width=10)
                self.imageWidget.update_image(image)
            except Exception as e:
                print(e)
        else:
            image = Image.new('RGB', (1280, 1024), (200, 200, 200))
            self.imageWidget.update_image(image)
            print(f"False get image data")

    def on_test(self):
        if not self.lock_redraw and not self.cam_callback.lock_callback:
            self.lock_redraw = True
            print(f"current text: {self.cam_callback.param}")
            try:
                if len(self.cam_callback.image_data) != 0:
                    # data_pkt = deepcopy(self.cam_callback.image_data)  # .copy()
                    data_pkt = bytearray(self.cam_callback.image_data)
                    b = io.BytesIO(data_pkt)
                    print(
                        f"size of IO buffer in bytes: {b.__sizeof__()}")
                    self.image = Image.open(b)
                    print(f"image_size: {self.image.size}")
                    draw = ImageDraw.Draw(self.image)
                    for item in self.cam_callback.datamatrix_list:
                        c_list = []
                        print(item.coordinates)
                        for coor in item.coordinates:
                            print(f"{coor[0]}, {coor[1]}")
                            c_list.append((coor[0], coor[1]))
                        if len(c_list) >= 3:
                            draw.polygon(c_list, outline=(0, 0xFE, 0), width=10)

                    self.imageWidget.update_image(self.image)
            except Exception as e:
                print(e)
                image = Image.new('RGB', (1280, 1024), (200, 200, 200))
                self.imageWidget.update_image(image)
                print(f"False get image data\n")
            self.lock_redraw = False

    def on_get_frame_callback(self):
        result = self.hik.get_one_frame_callback()
        print(result[1])


    def on_start_grabbing(self):
        try:
            self.hik.start_grabbing()
        except Exception as e:
            print(e)

    def on_stop_grabbing(self):
        try:
            self.hik.stop_grabbing()
        except Exception as e:
            print(e)

    def on_select_software_trigger(self):
        try:
            self.hik.change_trigger_to_software()
        except Exception as e:
            print(f"{e}: on_select_software_trigger Exception")

    def on_trigger(self):
        try:
            self.hik.send_software_trigger()
        except Exception as e:
            print(f"{e}: on_trigger Exception")

    def on_trigger_enable(self):
        print(f"on_trigger_enable")
        try:
            self.hik.enable_trigger_mode()
        except Exception as e:
            print(f"{e}: on_trigger_enable Exception")

    def on_trigger_disable(self):
        print(f"on_trigger_disable")
        try:
            self.hik.disable_trigger_mode()
        except Exception as e:
            print(f"{e}: on_trigger_disable Exception")

    def on_disconnect(self):
        try:
            if self.hik.close_device_session()[0]:
                if self.hik.destroy_handle()[0]:
                    print("handle destroyed successfully")
                else:
                    print(f"failed handle destroy")
            else:
                print(f"failed close device session")
        except Exception as e:
            print(e)

    '''
        def resizeEvent(self, event):
            if self.width() >= 400:
                width = self.width() - 150
            else:
                width = self.width()
            if self.height() >= 300:
                height = self.height() - 100
            else:
                height = self.height()

            pixmap = self.imageWidget.pixmap.scaled(self.width() - 150, self.height() - 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.imageWidget.update_pixmap(pixmap)
    '''

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Подтверждение закрытия программы',
                                     "Вы действительно хотите закрыть программу?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # self.dll
            event.accept()
        else:

            event.ignore()

    def closeEventTr(self, event):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('"Подтверждение закрытия приложения"')
        msg_box.setPlainText('"Вы действительно хотите закрыть приложение?"')
        msg_box.setMinimumSize(300, 300)
        accept_btn = msg_box.addButton("Да", QMessageBox.AcceptRole)
        reject_btn = msg_box.addButton("Нет", QMessageBox.RejectRole)
        msg_box.exec_()
        # msg_box.exec()
        if msg_box.clickedButton() == accept_btn:
            event.accept()
        else:
            # self.hide()
            event.ignore()


class ImageView(QWidget):
    def __init__(self, image_data, parent=None):
        QWidget.__init__(self, parent)

        # bytes_ = bytearray(image_data)
        # image_ = Image.open(io.BytesIO(bytes_))

        image_ = Image.new('RGB', (600, 400), (200, 200, 200))
        # draw = ImageDraw.Draw(image)
        # draw.polygon(((1156, 575), (1232, 469), (1143, 385), (1068, 492)), outline=(0, 0xFE, 0), width=10)

        self.qim = ImageQt(image_)
        self.pixmap = QPixmap.fromImage(self.qim)

        # self.image_pixmap = QPixmap()
        self.label = QLabel()
        self.label.setPixmap(self.pixmap)
        self.label.setMinimumSize(600, 400)

        self.v_layout = QVBoxLayout(self)
        self.v_layout.addWidget(self.label)
        self.v_layout.addWidget(QLabel(""))
        self.v_layout.insertStretch(2, 50)

        self.resize(self.pixmap.size())

    def update_image(self, image: Image):
        self.qim = ImageQt(image)
        self.pixmap = QPixmap.fromImage(self.qim)
        self.label.setPixmap(self.pixmap)
        # self.resize(self.pixmap.size())
        # self.image_pixmap.loadFromData(bytes)

    def update_pixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.label.setPixmap(self.pixmap)
        self.resize(self.pixmap.size())


class ImageWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        image = Image.new('RGB', (1280, 1024), (219, 193, 27))

        self.qim = ImageQt(image)
        self.pixmap = QPixmap.fromImage(self.qim)

    def hasHeightForWidth(self):
        return self.pixmap() is not None

    def heightForWidth(self, w):
        if self.pixmap():
            try:
                return int(w * (self.pixmap().height() / self.pixmap().width()))
            except ZeroDivisionError:
                return 0


class ControlPanelView(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.font = QFont("Arial", 13)
        self.title_header = QFont("Arial", 13)

        self.lockSelectDevice = True

        self.searchBtn = QPushButton("Поиск\nкамер в сети")
        self.searchBtn.setMinimumSize(default_width, default_height)
        # self.searchBtn.clicked.connect(self.on_search)

        self.getversionBtn = QPushButton("SDK version")
        self.searchBtn.setMinimumSize(default_width, default_height)

        # self.deviceBox = QComboBox()
        # self.deviceBox.setDisabled(self.lockSelectDevice)

        self.connectBtn = QPushButton("Подключиться")
        self.connectBtn.setMinimumSize(default_width, default_height)

        self.disconnectBtn = QPushButton("Отключиться")
        self.disconnectBtn.setMinimumSize(default_width, default_height)

        self.startGrabbingBtn = QPushButton("Start\nGrabbing")
        self.startGrabbingBtn.setMinimumSize(default_width, default_height)

        self.stopGrabbingBtn = QPushButton("Stop\nGrabbing")
        self.stopGrabbingBtn.setMinimumSize(default_width, default_height)

        self.testBtn = QPushButton("Test")
        self.testBtn.setMinimumSize(default_width, default_height)

        self.triggerOnBtn = QPushButton("TriggerOn")
        self.triggerOnBtn.setMinimumSize(default_width, default_height)

        self.triggerOffBtn = QPushButton("TriggerOff")
        self.triggerOffBtn.setMinimumSize(default_width, default_height)

        self.setTriggerSourceBtn = QPushButton("Set\nSoftTriggerMode")
        self.setTriggerSourceBtn.setMinimumSize(default_width, default_height)

        self.sendTriggerBtn = QPushButton("TrigCam")
        self.sendTriggerBtn.setMinimumSize(default_width, default_height)

        self.getFrameTimeout = QPushButton("GetFrame")
        self.getFrameTimeout.setMinimumSize(default_width, default_height)

        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.searchBtn, 0, 0, 1, 2)
        self.gridLayout.addWidget(self.getversionBtn, 1, 0, 1, 2)
        self.gridLayout.addWidget(self.connectBtn, 2, 0, 1, 2)
        self.gridLayout.addWidget(self.disconnectBtn, 2, 2, 1, 2)
        self.gridLayout.addWidget(self.testBtn, 3, 0, 1, 2)

        self.gridLayout.addWidget(self.triggerOnBtn, 4, 0, 1, 2)
        self.gridLayout.addWidget(self.triggerOffBtn, 4, 2, 1, 2)
        self.gridLayout.addWidget(self.setTriggerSourceBtn, 4, 4, 1, 2)
        self.gridLayout.addWidget(self.sendTriggerBtn, 4, 6, 1, 2)
        self.gridLayout.addWidget(self.startGrabbingBtn, 5, 0, 1, 2)
        self.gridLayout.addWidget(self.stopGrabbingBtn, 5, 2, 1, 2)
        self.gridLayout.addWidget(self.getFrameTimeout, 6, 0, 1, 2)

        self.v_layout = QVBoxLayout()
        self.v_layout.addLayout(self.gridLayout)
        self.v_layout.insertStretch(1, 400)

        self.setLayout(self.v_layout)
