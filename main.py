from ctypes import *
import time

# from PyQt5.QtCore import QtMsgType, qInstallMessageHandler
# from PyQt5.QtWidgets import QApplication, QMessageBox

from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

import app_ui
import faulthandler

import os
import sys


from tongue_detector import TongueDetector

# import System
# from System import String
# from System import Type
# from System import Byte
# from System import IntPtr
# from System.Runtime import InteropServices
# from System.Collections import Generic

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# assembly_path = "C:\\Program Files (x86)\\IDMVS\\Development\\MvCodeReaderSDK\\DotNet\\win64"
#
# sys.path.append(assembly_path)
# clr.AddReference('MvCodeReaderSDK.Net')
#
# from MvCodeReaderSDKNet import MvCodeReader

# from Hik4Net import python_bytes


python_bytes = bytes()

'''
def ImageCallbackFunc(pData: IntPtr, pstFrameInfoEx2: IntPtr, pUser: IntPtr):
    print(f"here we go")
    global python_bytes
    m_BufForDriver = System.Array[Byte](1024 * 1024 * 20)
    stFrameInfo = InteropServices.Marshal.PtrToStructure(pstFrameInfoEx2, (MvCodeReader.MV_CODEREADER_IMAGE_OUT_INFO_EX2));
    print(f"frame info:\nsize:{stFrameInfo.nWidth}x{stFrameInfo.nHeight}\nframeNum: {stFrameInfo.nFrameNum}\ntriggerIndex: {stFrameInfo.nTriggerIndex}\n"
          f"frameLength: {stFrameInfo.nFrameLen}")
    result_of_copy = InteropServices.Marshal.Copy(pData, m_BufForDriver, 0, stFrameInfo.nFrameLen)
    print(f"result of copy: {result_of_copy}, {type(result_of_copy)}")
    print(f"type of buffer: {type(m_BufForDriver)}, [0]: {m_BufForDriver[0]}")
    python_bytes = bytes(m_BufForDriver)[0:stFrameInfo.nFrameLen]
    print(f"size of python bytes after slice: {len(python_bytes)}")



def test_search():
    mv_class = MvCodeReader()
    cMyDevice = MvCodeReader()
    m_stDeviceList = MvCodeReader.MV_CODEREADER_DEVICE_INFO_LIST()
    out = mv_class.MV_CODEREADER_EnumDevices_NET(m_stDeviceList, MvCodeReader.MV_CODEREADER_GIGE_DEVICE)
    print(out[1].nDeviceNum)
    stDevInfo = InteropServices.Marshal.PtrToStructure(out[1].pDeviceInfo[0], (MvCodeReader.MV_CODEREADER_DEVICE_INFO))

    print(f"dev 0: {stDevInfo.nTLayerType}")
    if stDevInfo.nTLayerType == MvCodeReader.MV_CODEREADER_GIGE_DEVICE:
        print("it`s Gige device")

        stGigEDeviceInfo = MvCodeReader.ByteToStruct(stDevInfo.SpecialInfo.stGigEInfo, MvCodeReader.MV_CODEREADER_GIGE_DEVICE_INFO)
        print(f"ip: {(stGigEDeviceInfo.nCurrentIp & 0xff000000) >> 24}:{(stGigEDeviceInfo.nCurrentIp & 0x00ff0000) >> 16}:{(stGigEDeviceInfo.nCurrentIp & 0x0000ff00) >> 8}:{stGigEDeviceInfo.nCurrentIp & 0x000000ff}")

        create_result = cMyDevice.MV_CODEREADER_CreateHandle_NET(stDevInfo)
        print(f"create handle result: {create_result[0], create_result[1]}")
        print(f"open device: {cMyDevice.MV_CODEREADER_OpenDevice_NET()}")  # MV_CODEREADER_StartGrabbing_NET
        ImageCallback = MvCodeReader.cbOutputEx2delegate(ImageCallbackFunc)
        print(f"register callback: {cMyDevice.MV_CODEREADER_RegisterImageCallBackEx2_NET(ImageCallback, IntPtr.Zero)}")
        print(f"start grabbing: {cMyDevice.MV_CODEREADER_StartGrabbing_NET()}")
        time.sleep(1)
        cMyDevice.MV_CODEREADER_SetCommandValue_NET("TriggerSoftware")
        time.sleep(4)
        print(f"stop grabbing: {cMyDevice.MV_CODEREADER_StopGrabbing_NET()}")
        print(f"close device: {cMyDevice.MV_CODEREADER_CloseDevice_NET()}")
        print(f"destroy handle: {cMyDevice.MV_CODEREADER_DestroyHandle_NET()}")
'''

# mv_ca c dll dir C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64


def messageHandler(msg_type, log_context, string):
    if msg_type == QtMsgType.QtFatalMsg:
        print(f"{msg_type} {log_context} {string}")  # log.error("{} {} {}".format(msg_type, log_context, string))
        QMessageBox.critical(None, "Error", "A critical error occurred. Please, report about this error")
        os.abort()


if __name__ == '__main__':
    # dll = ctypes.cdll.LoadLibrary(
    #        'C:\\Program Files (x86)\\IDMVS\\Development\\Bin\\win64\\MvCodeReaderCtrl.dll')
    faulthandler.enable()
    qInstallMessageHandler(messageHandler)

    # test = TongueDetector()
    # test.detect_test()

    # testObj = Hik4Net()
    # testObj.test_connect()

    # testObj.test_search()
    # test_search()
    app = QApplication(sys.argv)
    window = app_ui.MainWindow(python_bytes)
    window.show()

    app.exec()
