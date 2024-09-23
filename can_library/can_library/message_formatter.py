import can
import json
import string
import zlib
import time
import struct
import binascii

from binascii import hexlify

from codecs import encode
from codecs import decode

from can_library.utils import Utils

CAN_FD_DLC = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64]
TIME_REF = time.time()

class MessageFormatter(object):
    def __init__(self):
        self.dynamic_functions = {}  

    @staticmethod
    def hex_str_to_list(hex_str):
        hex_data = binascii.hexlify(hex_str).decode()
        hex_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
        return hex_list

    def setAttribute(self, attribute:dict) -> None:
        type_info = str(type(attribute))
        if type_info == "<class 'java.util.LinkedHashMap'>":
            convert_dict_data = Utils._convert_hashmap_to_dict(attribute)
        elif type_info == "<class 'dict'>":
            convert_dict_data = attribute

        for key, value in convert_dict_data.items():
            setattr(self, key, value)
            if callable(value):
                self.dynamic_functions[key] = value
       
    def getAllData(self)-> dict:
        all_data = {}
        for attr_name in dir(self):
            if not attr_name.startswith('__') and attr_name != 'dynamic_functions':
                attr_value = getattr(self, attr_name)
                if not callable(attr_value): 
                    all_data[attr_name] = attr_value
                elif attr_name in self.dynamic_functions:
                    updated_value = self.dynamic_functions[attr_name]() 
                    all_data[attr_name] = updated_value if not callable(updated_value) else updated_value()

        return all_data

    def getAllDataAsJson(self)-> json:
        all_data = self.getAllData()
        return json.dumps(all_data, indent=2)

# can.Message -> dict object
def canmsg2json(msg):
    jobj = {}
    jobj["tm"] = msg.timestamp
    jobj["id"] = msg.arbitration_id
    jobj["dt"] = hexlify(msg.data).decode("ascii")
    jobj["ch"] = str(msg.channel)

    # Convert only if its value is not default
    if(msg.is_extended_id == False):
        jobj["is_extended_id"] = msg.is_extended_id
    if(msg.is_remote_frame == True):
        jobj["is_remote_frame"] = msg.is_remote_frame
    if(msg.is_error_frame == True):
        jobj["is_error_frame"] = msg.is_error_frame
    if(msg.bitrate_switch == True):
        jobj["bitrate_switch"] = msg.bitrate_switch
    if(msg.error_state_indicator == True):
        jobj["error_state_indicator"] = msg.error_state_indicator

    return jobj

# dict object -> can.Message
def obj2canmsg(jobj):
    return can.Message(
        timestamp = jobj["tm"], 
        arbitration_id = jobj["id"], 
        channel = jobj["ch"],
        data = decode(jobj["dt"], "hex"),
        dlc = int(len(jobj["dt"])/2),
        is_extended_id = jobj["is_extended_id"] if "is_extended_id" in jobj else True,
        is_remote_frame = jobj["is_remote_frame"] if "is_remote_frame" in jobj else False,
        is_error_frame = jobj["is_error_frame"] if "is_error_frame" in jobj else False,
        bitrate_switch = jobj["bitrate_switch"] if "bitrate_switch" in jobj else False,
        error_state_indicator = jobj["error_state_indicator"] if "error_state_indicator" in jobj else False,
        )


class StatusMessage(object):
    def __init__(self):
        # default data 
        self.engine_speed = 0
        self.machine_status = "Engine OFF"
        self.fuel_level = 0
        self.hydraulic_oil_temp = 0.0
        self.coolant_temp = 0.0
        self.engine_fuel_rate = 0.0
        self.coolant_level = 0
        self.work_status = "idle"
        self.engine_total_hours_of_operation = 0.0
        self.engine_total_fuel_used = 0.0

    def get_json_properties_data(self):
        time_stamp = time.time()   
        status = {
            "head": {
                "gp_ver": "1.0.0",
                "epos_ver": "2.0.0",
                "ecu_ver": "3.0.0",
                "tcu_ver": "4.0.0"
            },
            "body": {
                'engine_speed (rpm)' : self.engine_speed,
                'machine_status (on/off)' : self.machine_status,
                'fuel_level (%)' : self.fuel_level,
                'hydraulic_oil_temp (deg C)' : self.hydraulic_oil_temp,
                'coolant_temp (deg C)' : self.coolant_temp,
                'engine_fuel_rate (L/h)' : self.engine_fuel_rate,
                'coolant_level (%)' : self.coolant_level,
                'work_status (idle/work)' : self.work_status,
                'engine_total_hours_of_operation (h)' : self.engine_total_hours_of_operation,
                'engine_total_fuel_used (L)' : self.engine_total_fuel_used,
                'reg_dt (sec)' : time_stamp
            }
        }

        return json.dumps(status)
    
class PeakSystemInterface(object):
    MESSAGE_TYPE_CAN            = 0x80
    MESSAGE_TYPE_CAN_WITH_CRC   = 0x81
    MESSAGE_TYPE_CANFD          = 0x90
    MESSAGE_TYPE_CANFD_WITH_CRC = 0x91

    FLAGS_RTR   = 0x01
    FLAGS_EXTID = 0x02
    FLAGS_FD_EXTID =0x02
    FLAGS_FD_EXTDATA_LENGTH =0x10
    FLAGS_FD_BITRATE_SWITCHING =0x20
    FLAGS_FD_ERROR_STATE =0x40

    FRAME_HEADER_LENGTH         = 28

    def __init__(self, 
                 can_id    = None, 
                 can_data  = None, 
                 channel   = 0, 
                 timestamp = None, 
                 fd        = False, 
                 brs       = False, 
                 extid     = False, 
                 remote    = False, 
                 error_state_indicator = None, 
                 binary_data = None,
                 with_crc = False, *args):
        
        if isinstance(can_id, str):
            can_id = int(can_id, 16)

        if can_data is not None:
            if isinstance(can_data, list):
                can_data = [int(x, 16) for x in can_data]
            can_data = bytes(can_data)

        self.remote    = remote
        self.extend_id = extid
        self.can_id    = can_id
        self.can_data  = can_data
        self.channel   = channel
        self.fd        = fd
        self.brs       = brs 
        self.error_state_indicator = error_state_indicator
        self.crc_flag  = with_crc
        self.timestamp = timestamp

    def trace_message(self)-> dict:
        return {"timestamp": self.timestamp,
                "channel"  : self.channel,
                "can_id"   : self.can_id,
                "can_data" : self.can_data
        }
    
    def except_byte_array_to_data(self, binary_data)-> tuple:
        can_id  = int.from_bytes(binary_data[24:28],byteorder='big', signed=False) 
        parser_can_msg_type = can_id & 0xC0000000
        parser_can_msg_type = parser_can_msg_type >> 24 
        can_id_int = can_id & 0x3FFFFFFF
        can_id_hex = '{:x}'.format(can_id_int)
        dlc = binary_data[21]
        
        length = CAN_FD_DLC[dlc]
        if length>8: 
            print("CAN Data Byte counter: " + format(length), end='')

        index = 0
        can_data_str = ""
        while (index <= length):
            can_data_str += "" + ''.join(""+'{:02x}'.format(binary_data[27+index])) + " "
            index = index + 1
        if all(c in string.hexdigits for c in can_id_hex):
            can_data_split = can_data_str.split(" ")
            can_data_split.remove("")
        return can_id_int, can_data_split

    def byte_array_to_msg_format(self, binary_data)-> dict:
        frame_length, \
        message_type, \
        tag, \
        timestamp_low, \
        timestamp_high, \
        channel, \
        dlc, \
        flags, \
        can_id = struct.unpack("!HHQIIBBHI", binary_data[0:28])

        timestamp = (timestamp_high << 32 | timestamp_low) * 0.000001

        can_data_bytes = binary_data[28:28+self.__get_length_from_dlc(dlc)]

        if bool(message_type & 0x01):
            crc_begin = 22
            crc_end = 28 + self.__get_length_from_dlc(dlc)
            crc_value = zlib.crc32(binary_data[crc_begin:crc_end])
            crc_ref_value = struct.unpack("!I", binary_data[-4:0])
            # logger.debug(crc_value, crc_ref_value)
            if crc_value != crc_ref_value:
                raise ValueError

        # parse flags
        self.remote = bool(flags & 0x01)
        self.extend_id = bool(flags & 0x02)
        self.brs = bool(flags & 0x10)
        self.error_state_indicator = bool(flags & 0x40)

        # general parameters
        self.can_data = can_data_bytes 
        self.can_id = can_id
        self.timestamp = timestamp
        self.channel = channel
        self.fd = bool(message_type & 0x90)
        
        return {"remote": self.remote,
                "extend_id": self.extend_id,
                "brs": self.brs,
                "error_state_indicator": self.error_state_indicator,
                "can_data": self.can_data,
                "can_id": self.can_id,
                "timestamp": self.timestamp,
                "channel": self.channel,
                "fd": self.fd
        } 
    
    def get_binary(self)-> bytearray:
        timestamp_low, timestamp_high = divmod(int(self.__get_timestamp() * 1000000.0), 2**32)

        message_header = struct.pack("!HHQIIB",
            self.__get_frame_length(),
            self.__get_message_type(),
            0,  # tag
            timestamp_low, timestamp_high,
            self.__get_channel_idx())

        frame_header = struct.pack("!BHI",
            self.get_dlc(),
            self.__get_flags(),
            self.__get_canid())

        frame_data = self.can_data

        frame_crc = b''
        if self.__is_crc_enable(): # no XOR operation
            frame_crc = zlib.crc32(frame_header + frame_data) 

        raw = message_header + frame_header + frame_data + frame_crc
        if len(raw) != self.__get_frame_length():
            raise ValueError

        return raw
        
    def get_dlc(self)-> int:
        length = len(self.can_data)
        if length <= 8:
            return length
        for dlc, nof_bytes in enumerate(CAN_FD_DLC):
            if nof_bytes >= length:
                return dlc
        return 15
    
    def __get_canid(self)-> int:
        arbitration_id = self.can_id & 0x3FFFFFFF
        rtr = (1 << 29) if self.remote and not self.fd else 0
        extid = (2 << 29) if self.extend_id else 0
        return arbitration_id | rtr | extid
    
    def __get_timestamp(self)-> time:
        return self.timestamp \
            if self.timestamp is not None \
            else time.time() - TIME_REF

    def __get_message_type(self)-> bytes:
        fd_code = 0x10 if self.fd is True else 0x00
        crc_code = 0x01 if self.crc_flag is True else 0x00
        return 0x80 + fd_code + crc_code
    
    def __get_flags(self)-> None:
        flag = 0
        if self.fd:
            flag |= 0x02 if self.extend_id else 0x00
            flag |= 0x10 if self.fd else 0x00 # extended data length flag
            flag |= 0x20 if self.brs else 0x00
            flag |= 0x40 if self.error_state_indicator else 0x00
        else:
            flag |= 0x02 if self.extend_id else 0x00
            flag |= 0x01 if self.remote else 0x00

        return flag

    def __get_length_from_dlc(self, dlc):
        return CAN_FD_DLC[dlc]
    
    def __get_channel_idx(self):
        return self.channel

    def __get_frame_length(self):
        length = self.FRAME_HEADER_LENGTH + len(self.can_data)
        return length + 4 if self.__is_crc_enable() else length
    
    def __is_crc_enable(self):
        return self.crc_flag is True
    
    def __get_length_from_dlc(self, dlc):
        return CAN_FD_DLC[dlc]
