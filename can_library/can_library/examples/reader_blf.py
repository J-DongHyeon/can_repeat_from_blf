#!/usr/bin/env python3
import can
import os, sys
import time
from pathlib import Path

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from pycantools import PyCanTools
from client   import Client
from utils    import Utils
from reader   import Reader

if __name__ == "__main__":

    # dbc_file = '/home/aiden/tm_ws/can_repeat_from_blf/can_library/can_library/files/tm.dbc'

    # dbc_params = Utils.json_dump({
    #     'dbcPath': dbc_file,
    # })

    blf_file = os.path.join(Path(__file__).parent.parent, '/home/aiden/tm_ws/can_repeat_from_blf/blf_files/E25_EXMS_01_can2_20240828_123000__20240828_125959.BLF')

    bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=250000)

    # can_filters = '{"id1": 217056295, "id2": 217056289, "id3": 217056256, "id4": 419375875, "id5": 419414311, "id6": 419420193, "id7": 419382561, "id8": 419363863, "id9": 33531392, "id10": 419335201, "id11": 419360256, "id12": 419361280, "id13": 419420705, "id14": 419360512, "id15": 419357952, "id16": 33530880, "id17": 419358976, "id18": 419236096, "id19": 419307776}'
    can_filters = '{"id1": 217056295, "id2": 217056289, "id3": 217056256, "id4": 419375875, "id5": 419414311, "id6": 419420193, "id7": 419382561, "id8": 419363863, "id9": 33531392, "id10": 419335201, "id12": 419361280, "id13": 419420705, "id14": 419360512, "id15": 419357952, "id16": 33530880, "id17": 419358976, "id18": 419236096, "id19": 419307776}'


    #callback function
    def calblack(msg):

        msg_dic = Utils.json_load(msg)

        can_id = msg_dic["canId"]
        hex_list = msg_dic["canData"]
        can_data = [int(x, 16) for x in hex_list]

        if can_id == 217056256 :
            can_data[-1] = 0
            can_data[-2] = 0

        can_msg  = can.Message(arbitration_id = can_id, data = can_data, is_extended_id=True)

        bus.send(can_msg)

        # decode_can_msg = PyCanTools._decode_raw_can_data(can_msg)
        # print(decode_can_msg)
        time.sleep(0.01)

        pass

    # use filter [arbitrationId, arbitrationId]
    reader = Reader()

    # PyCanTools._update_dbc_interface(dbc_params)

    # type callback
    reader.readBlf(blf_file, callback=calblack, filters=can_filters)

    # type result
    # reader.readBlf(blf_file)

    idx = 0
    while True:
        idx += 1 
        if idx == 2 :
            reader.stopReadBlf()
            # print(reader.getBlfDataList())
        time.sleep(1)















































