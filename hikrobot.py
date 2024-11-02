import ctypes
import io
import sys
import time
from copy import deepcopy
from ctypes import *
from typing import Any

import PyQt6
from PyQt6.QtCore import QObject

from data_models import Datamatrix
from pixel_format import *
import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import datetime

from threading import Thread, Lock

mutex = Lock()

frame_counter = 0


class DeviceType(Enum):
    MV_CODEREADER_UNKNOW_DEVICE = 0x00000000
    MV_CODEREADER_GIGE_DEVICE = 0x00000001
    MV_CODEREADER_1394_DEVICE = 0x00000002
    MV_CODEREADER_USB_DEVICE = 0x00000004
    MV_CODEREADER_CAMERALINK_DEVICE = 0x00000008


class TriggerSource(Enum):
    LINE_0 = 0
    LINE_1 = 1
    LINE_2 = 2
    LINE_3 = 3
    COUNTER_0 = 4  # Line_4
    SOFTWARE = 7
    FrequencyConverter = 8


class TriggerModeResult(Enum):
    UNKNOWN = -1,
    OFF = 0,
    ON = 1


class IpMode(Enum):
    IP_CFG_STATIC = 0x05000000
    IP_CFG_DHCP = 0x06000000
    IP_CFG_LLA = 0x04000000


class Hikrobot:
    def __init__(self):  # , dll_instance: CDLL = None
        self.dmx_list = None
        self.Handle0 = ctypes.c_void_p
        self.pData = self.Handle0(0)
        self.Handle = ctypes.c_void_p
        self.handle = self.Handle(0)
        self.is_unlock_operation = False

        self.outValue = EnumTypeValue()

        self.image_byte_array = (c_byte * (1024 * 1024 * 20))()

        # self.image_byte_array = (c_byte * (1024 * 1024 * 20))()  # * 20

        # self.imagePil = Image.new('RGB', (1280, 1024), (200, 100, 200))

        self.deviceList = DeviceListStructure()
        # CDLL PyDLL
        self.hikrobotDll = CDLL(r'/opt/IDMVS/Samples/Demo/linux64/GrabImage/libMvCodeReaderCtrl.so')
        # MvCodeReaderCtrlWrapper  MvCodeReaderCtrl

    def get_sdk_version(self) -> ():
        version_sdk = self.hikrobotDll.MV_CODEREADER_GetSDKVersion()
        return f"{version_sdk >> 24}.{(version_sdk >> 16) & 0xff}.{(version_sdk >> 8) & 0xff}.{version_sdk & 0xff}"

    def search_devices(self):
        # MV_CODEREADER_EnumDevices_NET
        result = self.hikrobotDll.MV_CODEREADER_EnumDevices(byref(self.deviceList),
                                                            DeviceType.MV_CODEREADER_GIGE_DEVICE.value)
        print(f"enum device status: {result}, deviceCount: {self.deviceList.nDeviceNum}")

    def create_handle_test(self):
        if self.deviceList.pDeviceInfo is not None:
            print(f"{self.deviceList.pDeviceInfo.__dir__()}")
            print(f"contents__dir__: {self.deviceList.pDeviceInfo.contents.__dir__()}")
            data = self.deviceList.pDeviceInfo.contents  # deviceList.pDeviceInfo[0].contents

            print(f"sizeof: {data.__dir__()}")
            print(f"here: {hex(data.nMacAddrHigh)}{hex(data.nMacAddrLow)}")
            print(data.stGigEInfo.__dir__())
            print("nDefultGateWay", data.stGigEInfo.nDefultGateWay)
            print("nCurrentSubNetMask", data.stGigEInfo.nCurrentSubNetMask)
            print("nCurrentIp", data.stGigEInfo.nCurrentIp)

            b_result = ctypes.string_at(data.stGigEInfo.chModelName, 32)
            print(ctypes.string_at(data.stGigEInfo.chDeviceVersion, 32))
            print(b_result)

            result = self.hikrobotDll.MV_CODEREADER_CreateHandle(byref(self.handle), data)
            if result != HikrobotErrorCode.MV_CODEREADER_OK.value:
                print(f"handle failed, {HikrobotErrorCode(result).name} code: {result}")
            else:
                print("handle success")
                result = self.hikrobotDll.MV_CODEREADER_OpenDevice(self.handle)
                if result != HikrobotErrorCode.MV_CODEREADER_OK.value:
                    print(f"open device failed, {HikrobotErrorCode(result).name}")
                else:
                    print("open device success")
                    result = self.hikrobotDll.MV_CODEREADER_CloseDevice(self.handle)
                    if result != HikrobotErrorCode.MV_CODEREADER_OK.value:
                        print(f"close device failed, {HikrobotErrorCode(result).name}")
                    else:
                        print(f"close device success")
                        result = self.hikrobotDll.MV_CODEREADER_DestroyHandle(self.handle)
                        if result != HikrobotErrorCode.MV_CODEREADER_OK.value:
                            print(f"destroy handle failed, {HikrobotErrorCode(result).name}")
                        else:
                            print(f"destroy handle success")

    def trigger_state(self, state=False):
        if self.handle is not None:
            # param3 -> Enum, OFF ON
            result = (self.hikrobotDll.MV_CODEREADER_SetEnumValue(self.handle, "TriggerMode", c_uint(state)))
            if result != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value):
                print(f"set trigger state[{state}] failed, {HikrobotErrorCode(c_uint(result).value).name}")

    def trigger_source(self, source: TriggerSource = TriggerSource.SOFTWARE):
        if self.handle is not None:
            # param
            result = (self.hikrobotDll.MV_CODEREADER_SetEnumValue(self.handle, "TriggerSource", c_uint(source.value)))
            if result != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value):
                print(f"set trigger source failed, {HikrobotErrorCode(c_uint(result).value).name}")
            else:
                print(HikrobotErrorCode(c_uint(result).value).name)

    def start_grabbing(self):
        if self.handle is not None:
            result = (self.hikrobotDll.MV_CODEREADER_StartGrabbing(self.handle))
            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(f"start grabbing failed, {HikrobotErrorCode(c_uint(result).value).name}")
            else:
                print(HikrobotErrorCode(c_uint(result).value).name)

    def stop_grabbing(self):
        if self.handle is not None:
            result = (self.hikrobotDll.MV_CODEREADER_StopGrabbing(self.handle))
            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(f"stop grabbing failed, {HikrobotErrorCode(c_uint(result).value).name}")
            else:
                print(HikrobotErrorCode(c_uint(result).value).name)

    def create_handle(self) -> (bool, str):
        if self.deviceList is not None:
            self.Handle = ctypes.c_void_p
            self.handle = self.Handle(0)

            print(self.deviceList.pDeviceInfo.contents.nMajorVer)
            data = self.deviceList.pDeviceInfo

            print(data.__dir__())
            result = self.hikrobotDll.MV_CODEREADER_CreateHandle(byref(self.handle), data)

            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(
                    f"{HikrobotErrorCode(result).name}, {c_uint(result).value}, {c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value}")
                return False, f"{HikrobotErrorCode(result).name}, {c_uint(result).value}, {c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value}"
            else:
                print(f"handle size: {self.handle.__sizeof__()} {self.handle.value}")
                return True, "success"
        else:
            return False, f"device list empty"

    def open_device_session(self) -> (bool, str):
        result = (self.hikrobotDll.MV_CODEREADER_OpenDevice(self.handle))
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            return True, "success"

    def close_device_session(self) -> (bool, str):
        result = (self.hikrobotDll.MV_CODEREADER_CloseDevice(self.handle))
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def destroy_handle(self) -> (bool, str):
        result = (self.hikrobotDll.MV_CODEREADER_DestroyHandle(self.handle))
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def enable_trigger_mode(self):
        cmd_string = "TriggerMode"
        c_string = cmd_string.encode('utf-8')
        result = self.hikrobotDll.MV_CODEREADER_SetEnumValue(self.handle, c_string, 1)
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def disable_trigger_mode(self):
        cmd_string = "TriggerMode"
        c_string = cmd_string.encode('utf-8')
        result = self.hikrobotDll.MV_CODEREADER_SetEnumValue(self.handle, c_string, 0)
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def get_trigger_source(self) -> (bool, TriggerSource):
        try:
            trigger_source = EnumTypeValue()
            self.hikrobotDll.MV_CODEREADER_GetEnumValue.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                                                    POINTER(EnumTypeValue)]
            cmd_string = "TriggerSource"
            c_string = cmd_string.encode('utf-8')
            result = self.hikrobotDll.MV_CODEREADER_GetEnumValue(self.handle, c_string, byref(trigger_source))
            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(f"[get_trigger_mode_state]->{HikrobotErrorCode(c_uint(result).value).name}")
                return True, False
            else:
                list_ar64 = [x for x in trigger_source.nSupportValue]
                print(f"TriggerSource -> {TriggerSource(trigger_source.nCurValue).name}"
                      f"\nCurrent value: {trigger_source.nCurValue}"
                      f"\nSupport values: {list_ar64}\nSupportNum: {trigger_source.nSupportedNum}")
                return True, TriggerSource(trigger_source.nCurValue)

        except Exception as e:
            print(e)
            return False, TriggerSource.SOFTWARE

    def get_trigger_mode_state(self) -> (bool, bool):  # request state, trigger_mode_state
        try:
            trigger_result = EnumTypeValue()
            self.hikrobotDll.MV_CODEREADER_GetEnumValue.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                                                    POINTER(EnumTypeValue)]
            cmd_string = "TriggerMode"
            c_string = cmd_string.encode('utf-8')
            result = self.hikrobotDll.MV_CODEREADER_GetEnumValue(self.handle, c_string, byref(trigger_result))
            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(f"[get_trigger_mode_state]->{HikrobotErrorCode(c_uint(result).value).name}")
                return True, False
            else:
                list_ar64 = [x for x in trigger_result.nSupportValue]
                print(
                    f"TriggerMode\nCurrent value: {trigger_result.nCurValue}\nSupport values: {list_ar64}\n"
                    f"SupportNum: {trigger_result.nSupportedNum}")
                return True, True
        except Exception as e:
            print(e)
            return False, False

    def change_trigger_to_software(self) -> (bool, str):
        # testEnum = EnumTypeValue()
        # print(testEnum.nCurValue)
        # self.hikrobotDll.MV_CODEREADER_GetEnumValue.argtypes = [ctypes.c_void_p, ctypes.c_char_p, POINTER(EnumTypeValue)]
        # cmd_string = "TriggerMode"
        # c_string = cmd_string.encode('utf-8')

        cmd_trigger_source_string = "TriggerSource"
        c_trigger_source = cmd_trigger_source_string.encode('utf-8')

        self.get_trigger_mode_state()
        self.get_trigger_source()

        result = (self.hikrobotDll.MV_CODEREADER_SetEnumValue(self.handle, c_trigger_source,
                                                              7))  # c_uint(TriggerSource.SOFTWARE.value).value
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def send_software_trigger(self) -> (bool, str):
        cmd_string = "TriggerSoftware"
        c_string = cmd_string.encode('utf-8')
        result = (self.hikrobotDll.MV_CODEREADER_SetCommandValue(self.handle, c_string))
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:

            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print("trigger!")
            print(HikrobotErrorCode(c_uint(result).value).name)
            return True, "success"

    def get_one_frame_callback(self) -> (bool, str):
        # get_one_frame_callback
        # param_callback get_one_frame_callback_tes
        result = self.hikrobotDll.MV_CODEREADER_RegisterImageCallBackEx2(self.handle, get_one_frame_callback_test,
                                                                         self.handle)
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            print(f"{HikrobotErrorCode(c_uint(result).value).name}")
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            return True, "callback on"

    def register_trigger_callback(self):
        result = self.hikrobotDll.MV_CODEREADER_RegisterTriggerCallBack(self.handle, trigger_callback, self.handle)
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(f"register_trigger_callback status: {HikrobotErrorCode(c_uint(result).value).name}")
            return True, "success"

    def register_exception_callback(self):
        result = self.hikrobotDll.MV_CODEREADER_RegisterExceptionCallBack(self.handle, exception_callback, self.handle)
        if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
            return False, f"{HikrobotErrorCode(c_uint(result).value).name}"
        else:
            print(f"register_exception_callback status: {HikrobotErrorCode(c_uint(result).value).name}")
            return True, "success"

    def get_one_frame_timeout(self) -> (bool, list[Datamatrix], bytearray):
        imageInfoEx2 = ImageOutInfoEx2()
        handle_frame = c_void_p
        self.pData = handle_frame(0)
        self.dmx_list = []
        try:
            result = self.hikrobotDll.MV_CODEREADER_GetOneFrameTimeoutEx2(self.handle, byref(self.pData),
                                                                          byref(imageInfoEx2), 1000)
            if c_uint(result).value != c_uint(HikrobotErrorCode.MV_CODEREADER_OK.value).value:
                print(f"get_frame_ex2 error code:{HikrobotErrorCode(c_uint(result).value).name}")
                return False, [], []
            else:
                lenData = imageInfoEx2.nFrameLen
                bytesImage = (c_ubyte * lenData)

                image_data_carray = bytesImage.from_address(self.pData.value)  # addressof(castedImg

                print("frame get success")
                print(
                    f"width: {imageInfoEx2.nWidth}, height: {imageInfoEx2.nHeight}, pixelFormat: {imageInfoEx2.enPixelType}, enum: {MvCodeReaderGvspPixelType(c_uint(imageInfoEx2.enPixelType).value).name}")
                dataBrc = imageInfoEx2.pstCodeListEx.contents
                print(
                    f"nFrameLen: {imageInfoEx2.nFrameLen}, dir: {dataBrc.__dir__()}\nBarcodeCount: {dataBrc.nCodeNum}")
                print(type(imageInfoEx2.nFrameLen))
                brc_temp = imageInfoEx2.pstCodeListEx.contents
                dmc_list = []

                print(f"brc_temp: {brc_temp.nCodeNum}, type: {type(brc_temp.nCodeNum)}")
                for i in range(brc_temp.nCodeNum):
                    print(brc_temp.stBcrInfoEx2[i].chCode, type(brc_temp.stBcrInfoEx2[i].chCode))  # chCode
                    print(brc_temp.stBcrInfoEx2[i].chCode.decode("utf-8"))
                    coord = []
                    for j in range(4):
                        coord.append(PointI(x=brc_temp.stBcrInfoEx2[i].pt[j].x, y=brc_temp.stBcrInfoEx2[i].pt[j].y))
                        print(f"({brc_temp.stBcrInfoEx2[i].pt[j].x},{brc_temp.stBcrInfoEx2[i].pt[j].y})")
                    dmc_list.append(Datamatrix(code_string=brc_temp.stBcrInfoEx2[i].chCode.decode("utf-8"),
                                               coordinates=coord))
                return True, dmc_list, bytearray(image_data_carray)
        except Exception as e:
            print(e)


class EventOutInfo(ctypes.Structure):
    _fields_ = [('EventName', c_char), ('nEventID', c_ushort), ('nStreamChannel', c_ushort), ('nBlockIdHigh', c_uint),
                ('nBlockIdLow', c_uint), ('nTimestampHigh', c_uint), ('nTimestampLow', c_uint),
                ('pEventData', c_void_p),
                ('nEventDataSize', c_uint), ('nReserved', c_uint * 16)]


class FileAccess(ctypes.Structure):
    _fields_ = [('pUserFIleName', c_char_p), ('pDevFileName', c_char_p), ('nReserved', c_uint * 32)]


class FileAccessProgress(ctypes.Structure):
    _fields_ = [('nCompleted', c_int64), ('nTotal', c_int64), ('nReserved', c_uint * 8)]


class IntValueEx(ctypes.Structure):
    _fields_ = [('nCurValue', c_int64), ('nMax', c_int64), ('nMin', c_int64), ('nInc', c_int64),
                ('nReserved', c_uint * 16)]


class ChunkDataContent(ctypes.Structure):
    _fields_ = [('pChunkData', c_char_p), ('nChunkID', c_uint), ('nChunkLen', c_uint), ('nReserved', c_uint * 8)]

    def __init__(self):
        self.pChunkData = c_char_p()
        self.nChunkID = c_uint(0)
        self.nChunkLen = c_uint(0)
        self.nReserved = (c_uint * 8)()


class EnumTypeValue(ctypes.Structure):
    _fields_ = [('nCurValue', c_uint), ('nSupportedNum', c_uint), ('nSupportValue', c_uint * 64),
                ('nReserved', c_uint * 4)]

    def __init__(self, num_of_cams=4):
        elems = (c_uint * num_of_cams)()
        elems2 = (c_uint * 64)()
        self.nCurValue = c_uint(0)
        self.nSupportedNum = c_uint(0)
        self.nSupportValue = (c_uint * 64)()
        self.nReserved = (c_uint * 4)()


class FloatValue(ctypes.Structure):
    _fields_ = [('fCurValue', c_float), ('fMax', c_float), ('fMin', c_float), ('nReserved', c_uint * 4)]


class PointI(ctypes.Structure):
    _fields_ = [('x', c_int), ('y', c_int)]


class PointF(ctypes.Structure):
    _fields_ = [('x', c_float), ('y', c_float)]


class FrameOutInfo(ctypes.Structure):
    _fields_ = [('nWidth', c_ushort), ('nHeight', c_ushort), ('enPixelType', c_uint), ('nFrameNum', c_uint),
                ('nDevTimeStampHigh', c_uint), ('nDevTimeStampLow', c_uint), ('nReserved0', c_uint * 8),
                ('nHostTimeStamp', c_int64), ('nFrameLen', c_uint), ('nLostPacket', c_uint), ('nReserved', c_uint * 2)]

    def __init__(self):
        self.nWidth = c_ushort(0)
        self.nHeight = c_ushort(0)
        self.enPixelType = c_uint(0)
        self.nFrameNum = c_uint(0)
        self.nDevTimeStampHigh = c_uint(0)
        self.nDevTimeStampLow = c_uint(0)
        self.nReserved0 = (c_uint * 8)()
        self.nHostTimeStamp = c_int64(0)
        self.nFrameLen = c_uint(0)
        self.nLostPacket = c_uint(0)
        self.nReserved = (c_uint * 2)()


class UnparsedChunkListUnion(ctypes.Union):
    _fields_ = [('pUnparsedChunkContent', POINTER(ChunkDataContent)), ('nAligning', c_int64)]

    def __init__(self):
        ch = ChunkDataContent()
        self.pUnparsedChunkContent = pointer(ch)
        self.nAligning = c_int64(0)


class FrameOutInfoEx(ctypes.Structure):
    _fields_ = [('nWidth', c_ushort), ('nHeight', c_ushort), ('enPixelType', c_uint), ('nFrameNum', c_uint),
                ('nDevTimeStampHigh', c_uint), ('nDevTimeStampLow', c_uint), ('nReserved0', c_uint * 8),
                ('nHostTimeStamp', c_int64), ('nFrameLen', c_uint), ('nSecondCount', c_uint), ('nCycleCount', c_uint),
                ('nCycleOffset', c_uint), ('fGain', c_float), ('fExposureTime', c_float),
                ('nAverageBrightness', c_uint), ('nRed', c_uint), ('nGreen', c_uint), ('nBlue', c_uint),
                ('nFrameCounter', c_uint), ('nTriggerIndex', c_uint), ('nInput', c_uint), ('nOutput', c_uint),
                ('nOffsetX', c_ushort), ('nOffsetY', c_ushort), ('nChunkWidth', c_ushort), ('nChunkHeight', c_ushort),
                ('nLostPacket', c_uint), ('nReserved', c_uint * 36)]  # 36 in demo project, 39 in doc

    def __init__(self):
        self.nWidth = c_ushort(0)
        self.nHeight = c_ushort(0)
        self.enPixelType = c_uint(0)
        self.nFrameNum = c_uint(0)
        self.nDevTimeStampHigh = c_uint(0)
        self.nDevTimeStampLow = c_uint(0)
        self.nReserved0 = (c_uint * 8)()
        self.nHostTimeStamp = c_int64(0)
        self.nFrameLen = c_uint(0)
        self.nSecondCount = c_uint(0)
        self.nCycleCount = c_uint(0)
        self.nCycleOffset = c_uint(0)
        self.fGain = c_float(0)
        self.fExposureTime = c_float(0)
        self.nAverageBrightness = c_uint(0)
        self.nRed = c_uint(0)
        self.nGreen = c_uint(0)
        self.nBlue = c_uint(0)
        self.nFrameCounter = c_uint(0)
        self.nTriggerIndex = c_uint(0)
        self.nInput = c_uint(0)
        self.nOutput = c_uint(0)
        self.nOffsetX = c_ushort(0)
        self.nOffsetY = c_ushort(0)
        self.nChunkWidth = c_ushort(0)
        self.nChunkHeight = c_ushort(0)
        self.nLostPacket = c_uint(0)
        self.nReserved = (c_uint * 39)()


class OcrRowInfo(ctypes.Structure):
    _fields_ = [('nId', c_uint), ('nOcrLen', c_uint), ('chOcr', c_char * 128), ('fCharConfidence', c_float),
                ('nOcrRowCenterX', c_uint), ('nOcrRowCenterY', c_uint), ('nOcrRowWidth', c_uint),
                ('nOcrRowHeight', c_uint), ('fOcrRowAngle', c_float), ('fDeteConfidence', c_float),
                ('sOcrAlgoCost', c_ushort), ('sReserved', c_ushort), ('nReserved', c_int * 31)]

    def __init__(self):
        self.nId = c_uint(0)
        self.nOcrLen = c_uint(0)
        self.chOcr = (c_char * 128)()
        self.fCharConfidence = c_float(0)
        self.nOcrRowCenterX = c_uint(0)
        self.nOcrRowCenterY = c_uint(0)
        self.nOcrRowWidth = c_uint(0)
        self.nOcrRowHeight = c_uint(0)
        self.fOcrRowAngle = c_float(0)
        self.fDeteConfidence = c_float(0)
        self.sOcrAlgoCost = c_ushort(0)
        self.sReserved = c_ushort(0)
        self.nReserved = (c_int * 31)()


class OcrInfoList(ctypes.Structure):
    _fields_ = [('nOCRAllNum', c_uint), ('stOcrRowInfo', OcrRowInfo * 100), ('nReserved', c_int * 8)]

    def __init__(self):
        self.nOCRAllNum = c_uint(0)
        self.stOcrRowInfo = (OcrRowInfo * 100)()
        self.nReserved = (c_int * 8)()


class WaybillInfo(ctypes.Structure):
    _fields_ = [('fCenterX', c_float), ('fCenterY', c_float), ('fWidth', c_float), ('fHeight', c_float),
                ('fAngle', c_float), ('fConfidence', c_float), ('pImageWaybill', c_char_p), ('nImageLen', c_uint),
                ('nReserved', c_uint * 12)]

    def __init__(self):
        self.fCenterX = c_float(0)
        self.fCenterY = c_float(0)
        self.fWidth = c_float(0)
        self.fHeight = c_float(0)
        self.fAngle = c_float(0)
        self.fConfidence = c_float(0)
        self.pImageWaybill = c_char_p()  # NULL pointer
        self.nImageLen = c_uint(0)
        self.nReserved = (c_uint * 12)()


class WaybillList(ctypes.Structure):
    _fields_ = [('nWaybillNum', c_uint), ('enWaybillImageType', c_uint), ('stWaybillInfo', WaybillInfo * 50),
                ('nReserved', c_uint * 4)]

    def __init__(self):
        self.nWaybillNum = c_uint(0)
        self.enWaybillImageType = c_uint(0)
        self.stWaybillInfo = (WaybillInfo * 50)()
        self.nReserved = (c_uint * 4)()


class CodeInfo(ctypes.Structure):
    _fields_ = [('nOverQuality', c_int), ('nDeCode', c_int), ('nSCGrade', c_int), ('nModGrade', c_int),
                ('nFPDGrade', c_int), ('nANGrade', c_int), ('nGNGrade', c_int), ('nUECGrade', c_int),
                ('nPGHGrade', c_int), ('nPGVGrade', c_int), ('fSCScore', c_float), ('fModScore', c_float),
                ('fFPDScore', c_float), ('fAnScore', c_float), ('fGNScore', c_float), ('fUECScore', c_float),
                ('fPGHScore', c_float), ('fPGVScore', c_float), ('nRMGrade', c_int), ('fRMScore', c_float),
                ('nReserved', c_int * 30)]

    def __init__(self):
        self.nOverQuality = c_int(0)
        self.nDeCode = c_int(0)
        self.nSCGrade = c_int(0)
        self.nModGrade = c_int(0)
        self.nFPDGrade = c_int(0)
        self.nANGrade = c_int(0)
        self.nGNGrade = c_int(0)
        self.nUECGrade = c_int(0)
        self.nPGHGrade = c_int(0)
        self.nPGVGrade = c_int(0)
        self.fSCScore = c_float(0)
        self.fModScore = c_float(0)
        self.fFPDScore = c_float(0)
        self.fAnScore = c_float(0)
        self.fGNScore = c_float(0)
        self.fUECScore = c_float(0)
        self.fPGHScore = c_float(0)
        self.fPGVScore = c_float(0)
        self.nRMGrade = c_int(0)
        self.fRMScore = c_float(0)
        self.nReserved = (c_int * 30)()


class BcrInfo(ctypes.Structure):
    _fields_ = [('nID', c_uint), ('chCode', c_char * 256), ('nLen', c_uint), ('nBarType', c_uint), ('pt', PointI * 4),
                ('nAngle', c_int), ('nMainPackageId', c_uint), ('nSubPackageId', c_uint), ('sAppearCount', c_ushort),
                ('sPPM', c_ushort), ('sAlgoCost', c_ushort), ('sSharpness', c_ushort)]

    def __init__(self):
        self.nID = c_uint(0)
        self.chCode = (c_char * 256)()
        self.nLen = c_uint(0)
        self.nBarType = c_uint(0)
        self.pt = (PointI * 4)()
        self.nAngle = c_int(0)
        self.nMainPackageId = c_uint(0)
        self.nSubPackageId = c_uint(0)
        self.sAppearCount = c_ushort(0)
        self.sPPM = c_ushort(0)
        self.sAlgoCost = c_ushort(0)
        self.sSharpness = c_ushort(0)


class BrcInfoEx(ctypes.Structure):
    _fields_ = [('nId', c_uint), ('chCode', c_char * 256), ('nLen', c_uint), ('nBarType', c_uint), ('pt', PointI * 4),
                ('stCodeQuality', CodeInfo), ('nAngle', c_int), ('nMainPackageId', c_uint), ('nSubPackageId', c_uint),
                ('sAppearCount', c_ushort), ('sPPM', c_ushort), ('sAlgoCost', c_ushort), ('sSharpness', c_ushort),
                ('blsGetQuality', c_bool), ('nIDRScore', c_uint), ('nReserved', c_uint * 30)]

    def __init__(self):
        self.nID = c_uint(0)
        self.chCode = (c_char * 256)()
        self.nLen = c_uint(0)
        self.nBarType = c_uint(0)
        self.pt = (PointI * 4)()
        self.stCodeQuality = CodeInfo()
        self.nAngle = c_int(0)
        self.nMainPackageId = c_uint(0)
        self.nSubPackageId = c_uint(0)
        self.sAppearCount = c_ushort(0)
        self.sPPM = c_ushort(0)
        self.sAlgoCost = c_ushort(0)
        self.sSharpness = c_ushort(0)
        self.blsGetQuality = c_bool(False)
        self.nIDRScore = c_uint(0)
        self.nReserved = (c_uint * 30)()


class BrcInfoEx2(ctypes.Structure):
    _fields_ = [('nId', c_uint), ('chCode', c_char * 4096), ('nLen', c_uint), ('nBarType', c_uint), ('pt', PointI * 4),
                ('stCodeQuality', CodeInfo), ('nAngle', c_int), ('nMainPackageId', c_uint), ('nSubPackageId', c_uint),
                ('sAppearCount', c_ushort), ('sPPM', c_ushort), ('sAlgoCost', c_ushort), ('sSharpness', c_ushort),
                ('blsGetQuality', c_bool), ('nIDRScore', c_uint), ('n1DIsGetQuality', c_uint),
                ('nTotalProcCost', c_uint), ('nTriggerTimeTvHigh', c_uint), ('nTriggerTimeTvLow', c_uint),
                ('nTriggerTimeUtvHigh', c_uint), ('nTriggerTimeUtvLow', c_uint), ('nReserved', c_int * 59)]

    def __init__(self):
        # elems = (ctypes.POINTER(DeviceInfoStructure) * 26)()
        # self.nDeviceNum = c_uint(0)
        # self.pDeviceInfo = ctypes.cast(elems, ctypes.POINTER(DeviceInfoStructure))

        self.nId = c_uint(0)
        self.chCode = (c_char * 200)()
        self.nLen = c_uint(0)
        self.nBarType = c_uint(0)
        self.pt = (PointI * 4)()
        self.stCodeQuality = CodeInfo()
        self.nAngle = c_int(0)
        self.nMainPackageId = c_uint(0)
        self.nSubPackageId = c_uint(0)
        self.sAppearCount = c_ushort(0)
        self.sPPM = c_ushort(0)
        self.sAlgoCost = c_ushort(0)
        self.sSharpness = c_ushort(0)
        self.blsGetQuality = c_bool(False)
        self.nIDRScore = c_uint(0)
        self.n1DIsGetQuality = c_uint(0)
        self.nTotalProcCost = c_uint(0)
        self.nTriggerTimeTvHigh = c_uint(0)
        self.nTriggerTimeTvLow = c_uint(0)
        self.nTriggerTimeUtvHigh = c_uint(0)
        self.nTriggerTimeUtvLow = c_uint(0)
        self.nReserved = (c_int * 59)()


class ResultBCR(ctypes.Structure):
    _fields_ = [('nCodeNum', c_uint), ('strBcrInfo', BrcInfoEx * 200), ('nReserved', c_uint * 4)]

    def __init__(self):
        # elems = (ctypes.POINTER(DeviceInfoStructure) * 26)()
        # self.nDeviceNum = c_uint(0)
        # self.pDeviceInfo = ctypes.cast(elems, ctypes.POINTER(DeviceInfoStructure))

        self.nCodeNum = c_uint(0)
        self.strBcrInfo = (BrcInfoEx * 200)()
        self.nReserved = (c_uint * 4)()


class ResultBcrEx(ctypes.Structure):
    _fields_ = [('nCodeNum', c_uint), ('stBcrInfoEx', BrcInfoEx * 200), ('nReserved', c_uint * 4)]

    def __init__(self):
        # elems = (ctypes.POINTER(DeviceInfoStructure) * 26)()
        # self.nDeviceNum = c_uint(0)
        # self.pDeviceInfo = ctypes.cast(elems, ctypes.POINTER(DeviceInfoStructure))

        self.nCodeNum = c_uint(0)
        self.stBcrInfoEx = (BrcInfoEx * 200)()
        self.nReserved = (c_uint * 4)()


class ResultBcrEx2(ctypes.Structure):
    _fields_ = [('nCodeNum', c_uint), ('stBcrInfoEx2', BrcInfoEx2 * 300), ('nReserved', c_uint * 8)]

    def __init__(self):
        self.nCodeNum = ctypes.c_uint(0)
        self.stBcrInfoEx2 = (BrcInfoEx2 * 300)()
        self.nReserved = (ctypes.c_uint * 8)()


class UnparsedBcrListUnion(ctypes.Union):
    _fields_ = [('pstCodeListEx2', POINTER(ResultBcrEx2)), ('nAligning', c_int64)]

    def __init__(self):
        # elems = (ctypes.POINTER(DeviceInfoStructure) * 26)()
        # self.nDeviceNum = c_uint(0)
        # self.pDeviceInfo = ctypes.cast(elems, ctypes.POINTER(DeviceInfoStructure))

        brc = ResultBcrEx2()
        self.pstCodeListEx2 = pointer(brc)
        self.nAligning = c_int64(0)


class UnparsedOcrListUnion(ctypes.Union):
    _fields_ = [('pstOcrList', POINTER(OcrInfoList)), ('nAligning', c_int64)]

    def __init__(self):
        ocr = OcrInfoList()
        self.pstOcrList = pointer(ocr)
        self.nAligning = c_int64(0)


class ImageOutInfo(ctypes.Structure):
    _fields_ = [('nWidth', c_ushort), ('nHeight', c_ushort), ('enPixelType', c_uint), ('nTriggerIndex', c_uint),
                ('nFrameNum', c_uint), ('nFrameLen', c_uint), ('nTimeStampHigh', c_uint), ('nTimeStampLow', c_uint),
                ('nResultType', c_uint), ('chResult', c_ubyte * (1024 * 64)), ('blsGetCode', c_bool),
                ('pImageWaybill', c_char_p), ('nImageWaybillLen', c_uint), ('bFlaseTrigger', c_uint),
                ('nFocusScore', c_uint), ('nChannelID', c_uint), ('nImageCost', c_uint), ('nReserved', c_uint * 6)]

    def __init__(self):
        self.nWidth = c_ushort(0)
        self.nHeight = c_ushort(0)
        self.enPixelType = c_uint(0)
        self.nTriggerIndex = c_uint(0)
        self.nFrameNum = c_uint(0)
        self.nFrameLen = c_uint(0)
        self.nTimeStampHigh = c_uint(0)
        self.nTimeStampLow = c_uint(0)
        self.nResultType = c_uint(0)
        self.chResult = (c_ubyte * 1024 * 64)()
        self.blsGetCode = c_bool(False)
        self.pImageWaybill = c_char_p()  # NULL pointer
        self.nImageWaybillLen = c_uint(0)
        self.bFlaseTrigger = c_uint(0)
        self.nFocusScore = c_uint(0)
        self.nChannelID = c_uint(0)
        self.nImageCost = c_uint(0)
        self.nReserved = (c_uint * 6)()


class ImageOutInfoEx(ctypes.Structure):
    _fields_ = [('nWidth', c_ushort), ('nHeight', c_ushort), ('enPixelType', c_uint), ('nTriggerIndex', c_uint),
                ('nFrameNum', c_uint), ('nFrameLen', c_uint), ('nTimeStampHigh', c_uint), ('nTimeStampLow', c_uint),
                ('bFlaseTrigger', c_uint), ('nFocusScore', c_uint), ('blsGetCode', c_bool),
                ('pstCodeList', POINTER(ResultBCR)), ('pstWaybillList', POINTER(WaybillList)), ('nEventID', c_uint),
                ('nChannelID', c_uint), ('nImageCost', c_uint), ('nReserved', c_uint * 6)]

    def __init__(self):
        bcr = ResultBCR()
        ocr = OcrInfoList()
        waybill = WaybillList()
        self.nWidth = c_ushort(0)
        self.nHeight = c_ushort(0)
        self.enPixelType = c_uint(0)
        self.nTriggerIndex = c_uint(0)
        self.nFrameNum = c_uint(0)
        self.nFrameLen = c_uint(0)
        self.nTimeStampHigh = c_uint(0)
        self.nTimeStampLow = c_uint(0)
        self.bFlaseTrigger = c_uint(0)
        self.nFocusScore = c_uint(0)
        self.blsGetCode = c_bool(False)
        self.pstCodeList = pointer(bcr)
        self.pstWaybillList = pointer(waybill)
        self.nEventID = c_uint(0)
        self.nChannelID = c_uint(0)
        self.nImageCost = c_uint(0)
        self.nReserved = (c_uint * 6)()


class ImageOutInfoEx2(ctypes.Structure):
    _fields_ = [('nWidth', c_ushort), ('nHeight', c_ushort), ('enPixelType', c_uint), ('nTriggerIndex', c_uint),
                ('nFrameNum', c_uint), ('nFrameLen', c_uint), ('nTimeStampHigh', c_uint), ('nTimeStampLow', c_uint),
                ('bFlaseTrigger', c_uint), ('nFocusScore', c_uint), ('blsGetCode', c_bool),
                ('pstCodeListEx', POINTER(ResultBcrEx)), ('pstWaybillList', POINTER(WaybillList)),
                ('nEventID', c_uint), ('nChannelID', c_uint), ('nImageCost', c_uint), ('nReserved', c_uint * 28)]

    def __init__(self):
        brc_ex = ResultBcrEx()
        way = WaybillList()

        self.nWidth = c_ushort(0)
        self.nHeight = c_ushort(0)
        self.enPixelType = MvCodeReaderGvspPixelType(0)
        self.nTriggerIndex = c_uint(0)
        self.nFrameNum = c_uint(0)
        self.nFrameLen = c_uint(0)
        self.nTimeStampHigh = c_uint(0)
        self.nTimeStampLow = c_uint(0)
        self.bFlaseTrigger = c_uint(0)
        self.nFocusScore = c_uint(0)
        self.blsGetCode = c_bool(False)
        self.pstCodeListEx = pointer(brc_ex)
        self.pstWaybillList = pointer(way)
        self.nEventID = c_uint(0)
        self.nChannelID = c_uint(0)
        self.nImageCost = c_uint(0)
        self.nReserved = (c_uint * 28)()

    # def __copy__(self):


class ImageParamEx(ctypes.Structure):
    _fields_ = [('pData', POINTER(ctypes.c_ubyte)), ('nDataLen', c_uint), ('enPixelType', c_uint),
                ('nWidth', c_ushort), ('nHeight', c_ushort), ('pImageBuffer', POINTER(c_ubyte)), ('nImageLen', c_uint),
                ('nBufferSize', c_uint), ('enImageType', c_uint), ('nJpgQuality', c_uint), ('iMethodValue', c_uint),
                ('nReserved', c_uint * 3)]


class StringValue(ctypes.Structure):
    _fields_ = [('chCurValue', c_char * 256), ('nMaxLength', c_int64), ('nReserved', c_uint * 2)]


class TriggerInfoData(ctypes.Structure):
    _fields_ = [('nTriggerIndex', c_uint), ('nTriggerFlag', c_uint), ('nTriggerTimeHigh', c_uint),
                ('nTriggerTimeLow', c_uint), ('nOriginalTrigger', c_uint), ('nIsForceOver', c_ushort),
                ('nIsMainCam', c_ushort), ('nHostTimeStamp', c_int64), ('reserved', c_uint * 30)]

    def __init__(self):
        self.nTriggerIndex = c_uint(0)
        self.nTriggerFlag = c_uint(0)
        self.nTriggerTimeHigh = c_uint(0)
        self.nTriggerTimeLow = c_uint(0)
        self.nOriginalTrigger = c_uint(0)
        self.nIsForceOver = c_ushort(0)
        self.nIsMainCam = c_ushort(0)
        self.nHostTimeStamp = c_int64(0)
        self.reserved = (c_uint * 30)()


class GigeDeviceInfo(ctypes.Structure):
    _fields_ = [('nIpCfgOption', c_uint), ('nIpCfgCurrent', c_uint),
                ('nCurrentIp', c_uint), ('nCurrentSubNetMask', c_uint),
                ('nDefultGateWay', c_uint), ('chManufacturerName', c_ubyte * 32),
                ('chModelName', c_ubyte * 32), ('chDeviceVersion', c_ubyte * 32),
                ('chManufacturerSpecificInfo', c_ubyte * 48), ('chSerialNumber', c_ubyte * 16),
                ('chUserDefinedName', c_ubyte * 16), ('nNetExport', c_uint), ('nCurUserIP', c_uint),
                ('nReserved', c_uint * 3)]

    def __init__(self):
        self.nIpCfgOption = c_uint(0)
        self.nIpCfgCurrent = c_uint(0)
        self.nCurrentIp = c_uint(0)
        self.nCurrentSubNetMask = c_uint(0)
        self.nDefultGateWay = c_uint(0)
        self.chManufacturerName = (c_ubyte * 32)()
        self.chModelName = (c_ubyte * 32)()
        self.chDeviceVersion = (c_ubyte * 32)()
        self.chManufacturerSpecificInfo = (c_ubyte * 48)()
        self.chSerialNumber = (c_ubyte * 16)()
        self.chUserDefinedName = (c_ubyte * 16)()
        self.nNetExport = c_uint(0)
        self.nCurUserIP = c_uint(0)
        self.nReserved = (c_uint * 3)()


class U3VDeviceStructure(ctypes.Structure):
    _fields_ = [('CrtlInEndPoint', c_ubyte), ('CrtlOutEndPoint', c_ubyte),
                ('StreamEndPoint', c_ubyte), ('EventEndPoint', c_ubyte),
                ('idVendor', c_ushort), ('idProduct', c_ushort),
                ('nDeviceNumber', c_uint), ('chDeviceGUID', c_ubyte),
                ('chVendorName', c_ubyte), ('chModelName', c_ubyte),
                ('chFamilyName', c_ubyte), ('chDeviceVersion', c_ubyte),
                ('chManufacturerName', c_ubyte), ('chSerialNumber', c_ubyte),
                ('chUserDefinedName', c_ubyte), ('nbcdUSB', c_uint),
                ('nReserved', c_uint * 3)]


class DeviceInfoStructure(ctypes.Structure):
    _fields_ = [('nMajorVer', c_ushort), ('nMinorVer', c_ushort),
                ('nMacAddrHigh', c_uint), ('nMacAddrLow', c_uint),
                ('nTLayerType', c_uint), ('bSelectDevice', c_bool),('nReserved', c_uint * 3),
                ('stGigEInfo', GigeDeviceInfo), ('stUsb3VInfo', U3VDeviceStructure)]

    def __init__(self):
        self.nMajorVer = c_ushort(0)
        self.nMinorVer = c_ushort(0)
        self.nMacAddrHigh = c_uint(0)
        self.nMacAddrLow = c_uint(0)
        self.nTLayerType = c_uint(0)
        self.bSelectDevice = c_bool(False)
        self.nReserved = (c_uint * 3)()
        self.stGigEInfo = GigeDeviceInfo()
        self.stUsb3VInfo = U3VDeviceStructure()

    @property
    def fields_(self):
        return self._fields_


class DeviceListStructure(ctypes.Structure):
    _fields_ = [('nDeviceNum', c_uint), ('pDeviceInfo', POINTER(DeviceInfoStructure))]

    def __init__(self, num_of_cams=256):
        # devInfo = DeviceInfoStructure()
        elems = (ctypes.POINTER(DeviceInfoStructure) * num_of_cams)()
        self.nDeviceNum = c_uint(0)
        self.pDeviceInfo = ctypes.cast(elems, ctypes.POINTER(DeviceInfoStructure))


class DeviceErrorCode(Enum):
    UnknownError = 0
    DeviceNotPrepareToOperation = 1


class HikrobotImageType(Enum):
    MV_CODEREADER_Image_Undefined = 0
    MV_CODEREADER_Image_Mono8 = 1
    MV_CODEREADER_Image_Jpeg = 2
    MV_CODEREADER_Image_Bmp = 3
    MV_CODEREADER_Image_RGB24 = 4
    MV_CODEREADER_Image_Png = 5  # PNG image, which is not supported now
    MV_CODEREADER_Image_Tif = 6  # TIF image, which is not supported now


class HikrobotBarcodeType(Enum):
    MV_CODEREADER_CODE_NONE = 0
    # 1D Code
    MV_CODEREADER_TDCR_DM = 1
    MV_CODEREADER_TDCR_QR = 2
    # 2D Code
    MV_CODEREADER_BCR_EAN8 = 8
    MV_CODEREADER_BCR_UPCE = 9
    MV_CODEREADER_BCR_UPCA = 12
    MV_CODEREADER_BCR_EAN13 = 13
    MV_CODEREADER_BCR_ISBN13 = 14
    MV_CODEREADER_BCR_CODABAR = 20  # codebar
    MV_CODEREADER_BCR_ITF25 = 25
    MV_CODEREADER_BCR_MATRIX25 = 26
    MV_CODEREADER_BCR_ITF14 = 27
    MV_CODEREADER_BCR_MSI = 30
    MV_CODEREADER_BCR_CODE11 = 31
    MV_CODEREADER_BCR_INDUSTRIAL_25 = 32
    MV_CODEREADER_BCR_CHINAPOST = 33
    MV_CODEREADER_BCR_CODE39 = 39
    MV_CODEREADER_BCR_CODE93 = 93
    MV_CODEREADER_BCR_CODE128 = 128
    MV_CODEREADER_TDCR_PDF417 = 131
    MV_CODEREADER_TDCR_ECC140 = 133


class HikrobotErrorCode(Enum):
    MV_CODEREADER_OK = 0x00000000
    MV_CODEREADER_E_HANDLE = 0x80020000
    MV_CODEREADER_E_SUPPORT = 0x80020001
    MV_CODEREADER_E_BUFOVER = 0x80020002
    MV_CODEREADER_E_CALLORDER = 0x80020003
    MV_CODEREADER_E_PARAMETER = 0x80020004
    MV_CODEREADER_E_RESOURCE = 0x80020005
    MV_CODEREADER_E_NODATA = 0x80020006
    MV_CODEREADER_E_PRECONDITION = 0x80020007
    MV_CODEREADER_E_VERSION = 0x80020008
    MV_CODEREADER_E_NOENOUGH_BUF = 0x80020009
    MV_CODEREADER_E_ABNORMAL_IMAGE = 0x8002000A
    MV_CODEREADER_E_LOAD_LIBRARY = 0x8002000B
    MV_CODEREADER_E_NOOUTBUF = 0x8002000C
    MV_CODEREADER_E_FILE_PATH = 0x8002000F
    MV_CODEREADER_E_UNKNOW = 0x800200FF
    # GenICam Related Error
    MV_CODEREADER_E_GC_GENERIC = 0x80020100
    MV_CODEREADER_E_GC_ARGUMENT = 0x80020101
    MV_CODEREADER_E_GC_RANGE = 0x80020102
    MV_CODEREADER_E_GC_PROPERTY = 0x80020103
    MV_CODEREADER_E_GC_RUNTIME = 0x80020104
    MV_CODEREADER_E_GC_LOGICAL = 0x80020105
    MV_CODEREADER_E_GC_ACCESS = 0x80020106
    MV_CODEREADER_E_GC_TIMEOUT = 0x80020107
    MV_CODEREADER_E_GC_DYNAMICCAST = 0x80020108
    MV_CODEREADER_E_GC_UNKNOW = 0x800201FF
    # GigE_STATUS Reltaed Errors
    MV_CODEREADER_E_NOT_IMPLEMENTED = 0x80020200
    MV_CODEREADER_E_INVALID_ADDRESS = 0x80020201
    MV_CODEREADER_E_WRITE_PROTECT = 0x80020202
    MV_CODEREADER_E_ACCESS_DENIED = 0x80020203
    MV_CODEREADER_E_BUSY = 0x80020204
    MV_CODEREADER_E_PACKET = 0x80020205
    MV_CODEREADER_E_NETER = 0x80020206
    # GigE Cameras Related Error(s)
    MV_CODEREADER_E_IP_CONFLICT = 0x80020221
    # USB_STATUS Related Errors // not used
    MV_CODEREADER_E_USB_READ = 0x80020300
    MV_CODEREADER_E_USB_WRITE = 0x80020301
    MV_CODEREADER_E_USB_DEVICE = 0x80020302
    MV_CODEREADER_E_USB_GENICAM = 0x80020303
    MV_CODEREADER_E_USB_BANDWIDTH = 0x80020304
    MV_CODEREADER_E_USB_DRIVER = 0x80020305
    MV_CODEREADER_E_USB_UNKNOW = 0x800203FF
    # Upgrade Related Errors
    MV_CODEREADER_E_UPG_MIN_ERRCODE = 0x80020400
    MV_CODEREADER_E_UPG_FILE_MISMATCH = 0x80020400
    MV_CODEREADER_E_UPG_LANGUSGE_MISMATCH = 0x80020401
    MV_CODEREADER_E_UPG_CONFLICT = 0x80020402
    MV_CODEREADER_E_UPG_INNER_ERR = 0x80020403
    MV_CODEREADER_E_UPG_REGRESH_TYPE_ERR = 0x80020404
    MV_CODEREADER_E_UPG_COPY_FPGABIN_ERR = 0x80020405
    MV_CODEREADER_E_UPG_ZIPEXTRACT_ERR = 0x80020406
    MV_CODEREADER_E_UPG_DAVEXTRACT_ERR = 0x80020407
    MV_CODEREADER_E_UPG_DAVCOMPRESS_ERR = 0x80020408
    MV_CODEREADER_E_UPG_ZIPCOMPRESS_ERR = 0x80020409
    MV_CODEREADER_E_UPG_GET_PROGRESS_TIMEOUT_ERR = 0x80020410
    MV_CODEREADER_E_UPG_SEND_QUERY_PROGRESS_ERR = 0x80020411
    MV_CODEREADER_E_UPG_RECV_QUERY_PROGRESS_ERR = 0x80020412
    MV_CODEREADER_E_UPG_GET_QUERY_PROGRESS_ERR = 0x80020413
    MV_CODEREADER_E_UPG_GET_MAX_QUERY_PROGRESS_ERR = 0x80020414
    MV_CODEREADER_E_UPG_CHECKT_PACKET_FAILED = 0x80020465
    MV_CODEREADER_E_UPG_FPGA_PROGRAM_FAILED = 0x80020466
    MV_CODEREADER_E_UPG_WATCHDOG_FAILED = 0x80020467
    MV_CODEREADER_E_UPG_CAMERA_AND_BARE_FAILED = 0x80020468
    MV_CODEREADER_E_UPG_RETAIN_CONFIG_FAILED = 0x80020469
    MV_CODEREADER_E_UPG_FPGA_DRIVER_FAILED = 0x8002046A
    MV_CODEREADER_E_UPG_SPI_DRIVER_FAILED = 0x8002046B
    MV_CODEREADER_E_UPG_REBOOT_SYSTEM_FAILED = 0x8002046C
    MV_CODEREADER_E_UPG_UPSELF_FAILED = 0x8002046D
    MV_CODEREADER_E_UPG_STOP_RELATION_PROGRAM_FAILED = 0x8002046E
    MV_CODEREADER_E_UPG_DEVCIE_TYPE_INCONSISTENT = 0x8002046F
    MV_CODEREADER_E_UPG_READ_ENCRYPT_INFO_FAILED = 0x80020470
    MV_CODEREADER_E_UPG_PLAT_TYPE_INCONSISTENT = 0x80020471
    MV_CODEREADER_E_UPG_CAMERA_TYPE_INCONSISTENT = 0x80020472
    MV_CODEREADER_E_UPG_DEVICE_UPGRADING = 0x80020473
    MV_CODEREADER_E_UPG_UNZIP_FAILED = 0x80020474
    MV_CODEREADER_E_UPG_BLE_DISCONNECT = 0x80020475
    MV_CODEREADER_E_UPG_BATTERY_NOTENOUGH = 0x80020476
    MV_CODEREADER_E_UPG_RTC_NOT_PRESENT = 0x80020477
    MV_CODEREADER_E_UPG_APP_ERR = 0x80020478
    MV_CODEREADER_E_UPG_L3_ERR = 0x80020479
    MV_CODEREADER_E_UPG_MCU_ERR = 0x8002047A
    MV_CODEREADER_E_UPG_UNKNOW = 0x800204FF
    # Network Components Related Errors
    MV_CODEREADER_E_CREAT_SOCKET = 0x80020500
    MV_CODEREADER_E_BIND_SOCKET = 0x80020501
    MV_CODEREADER_E_CONNECT_SOCKET = 0x80020502
    MV_CODEREADER_E_GET_HOSTNAME = 0x80020503
    MV_CODEREADER_E_NET_WRITE = 0x80020504
    MV_CODEREADER_E_NET_READ = 0x80020505
    MV_CODEREADER_E_NET_SELECT = 0x80020506
    MV_CODEREADER_E_NET_TIMEOUT = 0x80020507
    MV_CODEREADER_E_NET_ACCEPT = 0x80020508
    MV_CODEREADER_E_NET_UNKNOW = 0x800205FF


@CFUNCTYPE(c_void_p, POINTER(TriggerInfoData), POINTER(c_char_p))
def trigger_callback(p_trigger_info, p_user):
    Hikrobot.log_text = ("trigger_raise_callback")
    trigger_info = p_trigger_info.contents
    Hikrobot.log_text = (f"{trigger_info.nTriggerIndex}, {trigger_info.nTriggerFlag}, {trigger_info.nOriginalTrigger}")


@CFUNCTYPE(c_void_p, c_uint, POINTER(c_char_p))
def exception_callback(nMsgType, p_user):
    Hikrobot.log_text = (f"error_callback: {nMsgType}")


@CFUNCTYPE(c_void_p, POINTER(c_ubyte), POINTER(ImageOutInfoEx2), POINTER(c_void_p))
def get_one_frame_callback_test(p_data: POINTER(c_ubyte), p_frame_info: POINTER(ImageOutInfoEx2),
                                p_user: POINTER(c_char_p)):
    print('image callback')
    if p_frame_info:
        # time.sleep(0.2)
        # frame_counter += 1
        cur_time = datetime.datetime.now().time()

        frame_info: ImageOutInfoEx2 = p_frame_info.contents
        print(f"frame_info size: {frame_info.__sizeof__()}, ref cnt: {sys.getrefcount(frame_info)}")
        data_ = p_data.contents

        lenData = frame_info.nFrameLen
        bytesImage = (c_ubyte * lenData)
        print(f"[{cur_time}] address callback: {addressof(data_)}, data_: {data_}")
        image_data_carray = bytesImage.from_address(addressof(data_))  # addressof(castedImg
        # img_to_save = []
        try:
            print(
                f"[{cur_time}]type of element: {type(image_data_carray)} {image_data_carray[0]}, {image_data_carray[1]}")
        except Exception as e:
            print(e)
        # print(f"length of image data: {len(image_data_carray)}")
        # numpy.save("C:\\InAuto\\HikRobotCamera\\data", (image_data_carray))

        print(
            f"[{cur_time}]width: {frame_info.nWidth}, height: {frame_info.nHeight}, pixelFormat: {frame_info.enPixelType}, "
            f"enum: {c_uint(frame_info.enPixelType).value} {frame_info.pstCodeListEx}")
        data_brc: ResultBcrEx = frame_info.pstCodeListEx.contents

        print(f"[{cur_time}]address of data_brc: {addressof(data_brc)}")
        print(dir(data_brc))
        if data_brc.__sizeof__() != 0:
            print(
                f"[{cur_time}]data_brc size: {data_brc.__sizeof__()}") #, codes cnt:{data_brc.nCodeNum.value}, ref cnt: {sys.getrefcount(data_brc)}")
            # print(f"[{cur_time}]nFrameLen: {frame_info.nFrameLen}, dir: {data_brc.__dir__()}\nBarcodeCount: {data_brc.nCodeNum}")


class CamCallback(QObject):
    CALLBACK = CFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ImageOutInfoEx2),
                         ctypes.POINTER(ctypes.c_char_p))

    it_is_time = PyQt6.QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.callback_func = CamCallback.CALLBACK(self.observer_callback)
        self.param = None
        self.image_data = []
        self.datamatrix_list = []

        self.lock_callback = False
        self.frame_stored = None
        self.datamatrix_stored = None

        self.frame_counter = 0
        self.data_container = []

    def observer_callback(self, p_data, p_frame_info: POINTER(ImageOutInfoEx2), p_user):
        if mutex.locked():
            print("mutex locked")

        mutex.acquire()
        is_unlock_local = True
        print("catch new callback")
        if not self.lock_callback and is_unlock_local and p_frame_info:
            self.lock_callback = True
            data_ = p_data.contents
            frame_info: ImageOutInfoEx2() = p_frame_info.contents  # () add new

            len_data = frame_info.nFrameLen
            bytes_image = (ctypes.c_ubyte * len_data)

            # print(f"address callback: {ctypes.addressof(self.data_)}, data_: {self.data_}")
            image_data_carray = bytes_image.from_address(ctypes.addressof(data_))
            # image_data_carray = bytes_image
            # castedBytes = cast(bytes_image, c_ubyte)
            bytes_copy = (ctypes.c_ubyte * len_data).from_buffer_copy(bytearray(image_data_carray))
            image_data_carray = bytes_copy

            # self.data_container.append(bytearray(image_data_carray))

            # print(
            #    f"width: {self.frame_info.nWidth}, height: {self.frame_info.nHeight}, pixelFormat: {self.frame_info.enPixelType}, "
            #    f"enum: {MvCodeReaderGvspPixelType(ctypes.c_uint(self.frame_info.enPixelType).value).name}")

            # dataBrc = self.frame_info.pstCodeListEx.contents
            # print(f"nFrameLen: {self.frame_info.nFrameLen}, dir: {dataBrc.__dir__()}\nBarcodeCount: {dataBrc.nCodeNum}")

            brc_temp = frame_info.UnparsedBcrList.pstCodeListEx2.contents

            # ocr_tmpio = self.frame_info.UnparsedOcrList.pstOcrList.contents
            # self.ocr_temp = ocr_tmpio
            dmc_list = []

            print(f"brc_temp: {brc_temp.nCodeNum}, type: {type(brc_temp.nCodeNum)}")
            for i in range(brc_temp.nCodeNum):
                print(brc_temp.stBcrInfoEx2[i].chCode, type(brc_temp.stBcrInfoEx2[i].chCode))  # chCode
                # print(self.brc_temp.stBcrInfoEx2[i].chCode.decode("utf-8"))
                coord = []
                print(f"point cnt: {len(brc_temp.stBcrInfoEx2[i].pt)}, {brc_temp.stBcrInfoEx2[i].pt}")
                for j in range(4):
                    # PointI(x=self.brc_temp.stBcrInfoEx2[i].pt[j].x, y=self.brc_temp.stBcrInfoEx2[i].pt[j].y)
                    coord.append((brc_temp.stBcrInfoEx2[i].pt[j].x, brc_temp.stBcrInfoEx2[i].pt[j].y))
                    # print(f"({brc_temp.stBcrInfoEx2[i].pt[j].x},{brc_temp.stBcrInfoEx2[i].pt[j].y})")
                dmc_list.append(Datamatrix(code_string=brc_temp.stBcrInfoEx2[i].chCode.decode("utf-8"),
                                           coordinates=coord))

            '''
                        print(f"ocr_temp: {self.ocr_temp.nOCRAllNum}, type: {type(self.ocr_temp.nOCRAllNum)}")
            if self.ocr_temp.nOCRAllNum == 0:
                print("No ocr")
            for i in range(self.ocr_temp.nOCRAllNum):
                for j in range(4):
                    pass
                    # print(f"({ocr_temp.stOcrRowInfo[i].pt[j].x},{ocr_temp.stOcrRowInfo[i].pt[j].y})")
            '''

            self.param = "callback done"
            self.datamatrix_list = dmc_list.copy()
            ba_image = bytearray(image_data_carray)
            self.image_data = []
            for element in ba_image:
                self.image_data.append(element)
            # self.image_data = deepcopy(bytearray(image_data_carray))  # bytearray(image_data_carray).copy()
            # self.it_is_time.emit(True)

            self.lock_callback = False

            print(f"counter: {self.frame_counter}")
            self.frame_counter += 1
            mutex.release()
