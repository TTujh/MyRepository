import enum

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread


class CamStateMachine(enum.Enum):
    idle = 0,
    cam_detected = 1,
    handle_done = 2,
    device_session_open = 3,
    grabbing_on_progress = 4,
    grabbing_stopped = 5,
    device_session_close = 6,
    handle_destroy = 7


class CamProcessing(QThread):
    time_to_trig = pyqtSignal(bool)

    def __init__(self):
        QThread.__init__(self, None)
        self.is_thread_running = False
        self.is_cam_ready = False

    def search_devices(self):
        pass

    def run(self):
        self.is_thread_running = True
        while self.is_thread_running:
            QThread.msleep(100)
            if self.is_cam_ready:
                self.time_to_trig.emit(True)

    def on_stop(self):
        self.is_thread_running = False





