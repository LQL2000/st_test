import time
from ctypes import *  # 结构体数组类

# import isort
# import numpy as np
# import pandas as pd
import streamlit as st
from icecream import ic

# isort.file(__file__)  # 自动格式化文件

VCI_USBCAN2 = 4

canDLL = windll.LoadLibrary('./ControlCAN.dll')


class VciBoardInfo(Structure):
    _fields_ = [("hw_Version", c_uint16),
                ("fw_Version", c_uint16),
                ("dr_Version", c_uint16),
                ("in_Version", c_uint16),
                ("irq_Num", c_uint16),
                ("can_Num", c_byte),
                ("str_Serial_Num", c_char * 20),
                ("str_hw_Type", c_char * 40),
                ("Reserved", c_uint16 * 4),
                ]


class VciBoardInfoArray(Structure):
    _fields_ = [('SIZE', c_uint16), ('STRUCT_ARRAY', POINTER(VciBoardInfo))]

    def __init__(self, num_of_structs, *args: None, **kw: None):
        super().__init__(*args, **kw)
        self.STRUCT_ARRAY = cast((VciBoardInfo * num_of_structs)(), POINTER(VciBoardInfo))  # 结构体数组
        self.SIZE = num_of_structs  # 结构体长度
        self.ADDR = self.STRUCT_ARRAY[0]  # 结构体数组地址  byref()转c地址


class VciCanObj(Structure):
    _fields_ = [("ID", c_uint16),
                ("TimeStamp", c_uint16),
                ("TimeFlag", c_byte),
                ("SendType", c_byte),
                ("RemoteFlag", c_byte),
                ("ExternFlag", c_byte),
                ("DataLen", c_byte),
                ("Data", c_byte * 8),
                ("Reserved", c_byte * 3),
                ]


class VciCanObjArray(Structure):
    _fields_ = [('SIZE', c_uint16), ('STRUCT_ARRAY', POINTER(VciCanObj))]

    def __init__(self, num_of_structs, *args: None, **kw: None):
        # 这个括号不能少
        super().__init__(*args, **kw)
        self.STRUCT_ARRAY = cast((VciCanObj * num_of_structs)(), POINTER(VciCanObj))  # 结构体数组
        self.SIZE = num_of_structs  # 结构体长度
        self.ADDR = self.STRUCT_ARRAY[0]  # 结构体数组地址  byref()转c地址


class VciInitConfig(Structure):
    _fields_ = [("AccCode", c_uint32),
                ("fw_Version", c_uint32),
                ("Reserved", c_uint32),
                ("Filter", c_ubyte),
                ("Timing0", c_ubyte),
                ("Timing1", c_ubyte),
                ("Mode", c_ubyte),
                ]


baudrate_config = {"100Kbps" : [0x04, 0x1C],
                   "125Kbps" : [0x03, 0x1C],
                   "200Kbps" : [0x81, 0xFA],
                   "250Kbps" : [0x01, 0x1C],
                   "400Kbps" : [0x03, 0x1C],
                   "500Kbps" : [0x00, 0x1C],
                   "1000Kbps": [0x00, 0x14],
                   }

can_device_info = VciBoardInfoArray(64)
can_rece_obj = VciCanObjArray(2048)


def can_OpenDevice():
    if canDLL.VCI_OpenDevice(VCI_USBCAN2, 0, 0) > 0:
        st.success('CAN 打开成功', icon="✅")
    else:
        st.error('CAN 打开失败', icon="🚨")
        canDLL.VCI_CloseDevice(VCI_USBCAN2, 0)


if __name__ == "__main__":
    can_device_number = canDLL.VCI_FindUsbDevice2(byref(can_device_info.ADDR))
    # can_device_number = 0
    # print(can_device_number)
    # if can_device_number > 0:
    #     for i in range(can_device_number):
    #         ic(can_device_info.STRUCT_ARRAY[i].hw_Version)
    #         ic(can_device_info.STRUCT_ARRAY[i].fw_Version)
    #         ic(can_device_info.STRUCT_ARRAY[i].dr_Version)
    #         ic(can_device_info.STRUCT_ARRAY[i].in_Version)
    #         ic(can_device_info.STRUCT_ARRAY[i].irq_Num)
    #         ic(can_device_info.STRUCT_ARRAY[i].can_Num)
    #         ic(can_device_info.STRUCT_ARRAY[i].str_Serial_Num)
    #         ic(can_device_info.STRUCT_ARRAY[i].str_hw_Type)
    #         ic(can_device_info.STRUCT_ARRAY[i].Reserved)

    st.title("MPPT CAN上位机")
    col1, col2, col3 = st.columns(3)
    with col1:
        can_device_list = list()
        for i in range(can_device_number):
            serial = str(can_device_info.STRUCT_ARRAY[i].str_Serial_Num)
            serial = serial[2:-1]
            can_device_list.append(F"设备{i} [{serial}]")
        genre = st.radio(
                "CAN分析仪选择",
                can_device_list if can_device_list != [] else ("未找到CAN分析仪",),
                help="目前只支持创芯的CAN分析仪",
                disabled=False if can_device_list != [] else True
                )
    with col2:
        genre = st.radio(
                "通道1波特率",
                baudrate_config.keys(),
                index=5)
        can1_init_config = VciInitConfig(0x00000000,
                                         0xFFFFFFFF,
                                         0,
                                         0,
                                         baudrate_config.get(genre)[0],
                                         baudrate_config.get(genre)[1],
                                         0)
        ic(can1_init_config)
    with col3:
        genre = st.radio(
                "通道2波特率",
                baudrate_config.keys(),
                index=5)
        can2_init_config = VciInitConfig(0x00000000,
                                         0xFFFFFFFF,
                                         0,
                                         0,
                                         baudrate_config.get(genre)[0],
                                         baudrate_config.get(genre)[1],
                                         0)
        ic(can2_init_config)

    # number = st.number_input('Insert a number', value=2)
    # st.write('The current number is ', number)
    # asd = st.button('Say hello', on_click=can_OpenDevice)

    vci_initconfig = VciInitConfig(0x00000000,
                                   0xFFFFFFFF,
                                   0,
                                   0,
                                   0x00,
                                   0x1C,
                                   0)
    # 初始通道1
    # ret = canDLL.VCI_InitCAN(VCI_USBCAN2, 0, 0, byref(vci_initconfig))
    # if ret != STATUS_OK:
    #     ic('调用 VCI_InitCAN1出错')
    # ret = canDLL.VCI_StartCAN(VCI_USBCAN2, 0, 0)
    # if ret != STATUS_OK:
    #     ic('调用 VCI_StartCAN1出错')
    #
    # # 初始通道2
    # ret = canDLL.VCI_InitCAN(VCI_USBCAN2, 0, 1, byref(vci_initconfig))
    # if ret != STATUS_OK:
    #     ic('调用 VCI_InitCAN2 出错')
    # ret = canDLL.VCI_StartCAN(VCI_USBCAN2, 0, 1)
    # if ret != STATUS_OK:
    #     ic('调用 VCI_StartCAN2 出错')

    # # 通道1发送数据
    # ubyte_array = c_ubyte * 8
    # a = ubyte_array(1, 2, 3, 4, 5, 6, 7, 8)
    # ubyte_3array = c_ubyte * 3
    # b = ubyte_3array(0, 0, 0)
    # can_rece_obj = VciCanObj(0x1, 0, 0, 1, 0, 0, 8, a, b)  # 单次发送
    #
    # ret = canDLL.VCI_Transmit(VCI_USBCAN2, 0, 0, byref(can_rece_obj), 1)
    # if ret != STATUS_OK:
    #     ic('CAN1通道发送失败')

    # 接收数据
    #
    # while 1:
    #     ret = canDLL.VCI_Receive(VCI_USBCAN2, 0, 0, byref(can_rece_obj.ADDR), 2048, None)
    #     if ret > 0:
    #         can_id = can_rece_obj.STRUCT_ARRAY[0].ID
    #         can_data_len = can_rece_obj.STRUCT_ARRAY[0].DataLen
    #         can_data = list(can_rece_obj.STRUCT_ARRAY[0].Data)
    #         print(F'ID:0x{can_id:04X}', end="|")
    #         print(F'Len:{can_data_len}', end="|")
    #         print('Data:', end="")
    #         for i in can_data:
    #             print(F'0x{i:02X}', end=" ")
    #         print("")
    #         # ic(can_data)
    #         # df = pd.DataFrame(can_data)
    #         # st.table(df)
    #     time.sleep(0.03)
    # # 关闭
    # canDLL.VCI_CloseDevice(VCI_USBCAN2, 0)
