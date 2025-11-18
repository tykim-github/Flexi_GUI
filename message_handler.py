"""
메시지 패킹, 데이터 변환 및 처리 관련 함수들
"""

import struct
from constants import *


def pack_sdo_unit(task_id, sdo_id, status, length, value):
    """
    Pack SDO message unit.
    
    Parameters:
        task_id: Task ID
        sdo_id: SDO ID
        status: Status
        length: Data length
        value: Data value
    
    Returns:
        Packed message list
    """
    temp = [task_id, sdo_id, status, length]
    
    if length == 1:
        temp.extend([value])
    else:
        for i in range(length):
            if isinstance(value[i], int):
                temp.extend([value[i]])
            elif isinstance(value[i], list):
                temp.extend(value[i])
    return temp


def flatten_list(nested_list):
    """
    Flatten nested list.
    
    Parameters:
        nested_list: nested list
    
    Returns:
        flattened list
    """
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


def float_to_byte_list(value):
    """
    Convert float value to byte list.
    
    Parameters:
        value: float value to convert
    
    Returns:
        byte list
    """
    packed_float = struct.pack('f', value)
    byte_list = list(packed_float)
    return byte_list


def get_dlc_from_length(length):
    """
    Calculate DLC (Data Length Code) from data length.
    
    Parameters:
        length: data length
    
    Returns:
        DLC value
    """
    if length <= 12:
        return 9
    elif length <= 16:
        return 10
    elif length <= 20:
        return 11
    elif length <= 24:
        return 12
    elif length <= 32:
        return 13
    elif length <= 48:
        return 14
    elif length <= 64:
        return 15


def get_length_from_dlc(dlc):
    """
    Calculate data length from DLC code.
    
    Parameters:
        dlc: Data length code
    
    Returns:
        data length
    """
    if dlc == 9:
        return 12
    elif dlc == 10:
        return 16
    elif dlc == 11:
        return 20
    elif dlc == 12:
        return 24
    elif dlc == 13:
        return 32
    elif dlc == 14:
        return 48
    elif dlc == 15:
        return 64
    
    return dlc


def get_data_string(data, msgtype):
    """
    Convert CAN message data to string.
    
    Parameters:
        data: byte array
        msgtype: message type flags
    
    Returns:
        data string formatted in hexadecimal
    """
    from PCANBasic import PCAN_MESSAGE_RTR
    
    if (msgtype & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value:
        return "Remote Request"
    else:
        strTemp = b""
        for x in data:
            strTemp += b'%.2X ' % x
        return str(strTemp).replace("'", "", 2).replace("b", "", 1)


def bytes_to_string(bytes_data):
    """
    Convert bytes to string.
    
    Parameters:
        bytes_data: bytes data
    
    Returns:
        converted string
    """
    return str(bytes_data).replace("'", "", 2).replace("b", "", 1)
