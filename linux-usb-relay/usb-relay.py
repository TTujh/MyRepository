import usb.backend.libusb1
import time
import array

USB_TYPE_CLASS = 0x20
USB_ENDPOINT_OUT = 0x00
USB_ENDPOINT_IN = 0x80
USB_RECIP_DEVICE = 0x00
GET_REPORT = 0x1
SET_REPORT = 0x9
USB_HID_REPORT_TYPE_FEATURE = 3
MAIN_REPORT = 0
SwitchOnOneChannel = 0xFF
SwitchOffOneChannel = 0xFD
SwitchOnAllChannels = 0xFE
SwitchOffAllChannels = 0xFC
timeLongBeep = 0.5
timeShortBeep = 0.2
timePause = 0.2


def getReport(device, report, size):
    return device.ctrl_transfer(USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_IN, GET_REPORT,
                                (USB_HID_REPORT_TYPE_FEATURE << 8) | report,
                                0,
                                size,
                                1000
                                )


def setReport(device, report, data):
    return device.ctrl_transfer(USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_OUT, SET_REPORT,
                                (USB_HID_REPORT_TYPE_FEATURE << 8) | report,
                                0,
                                data,
                                1000
                                )


def switchOn(device, number):
    data = [0 for _ in range(8)]
    if number == 0:
        data[0] = int(SwitchOnAllChannels)
    else:
        data[0] = int(SwitchOnOneChannel)
        data[1] = number
    setReport(device, MAIN_REPORT, data)


def switchOff(device, number):
    data = [0 for _ in range(8)]
    if number == 0:
        data[0] = int(SwitchOffAllChannels)
    else:
        data[0] = int(SwitchOffOneChannel)
        data[1] = number
    setReport(device, MAIN_REPORT, data)


def TikTak(device, channel, wait):
    switchOn(device, channel)
    time.sleep(wait)
    switchOff(device, channel)




def connect():
    try:
        connected_device = usb.core.find(idVendor=0x16c0,
                                         idProduct=0x05df,
                                         backend=usb.backend.libusb1.get_backend(
                                             find_library='/usr/lib/x86_64-linux-gnu/libusb-1.0.so'))
    except Exception as err:
        raise err

    else:
        if connected_device:
            for cfg in connected_device:
                for intf in cfg:
                    if connected_device.is_kernel_driver_active(intf.bInterfaceNumber):
                        connected_device.detach_kernel_driver(intf.bInterfaceNumber)
            connected_device.set_configuration()
            return connected_device
        else:
            raise ValueError('Error during connection to hid')


device = connect()
TikTak(device, 1, 0.5)
time.sleep(0.2)
TikTak(device, 1, 0.2)
device.reset()
