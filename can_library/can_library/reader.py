import can
import time
import threading

from can_library.pycantools import PyCanTools
from can_library.utils import Utils

class Reader(object):
    def __init__(self):
        self.__read_blf_is_loop = True
        self.__blf_data_list = []
        self.__thread_loops  = {}
        self.__bus           = {}
        print('\t[Initialize Reader]')

# PyCanTools 클래스의 _update_dbc_interface() 메소드를 통해 
# dbc 파일에서 필요한 데이터만 파싱된 파이썬 객체와 dbc 파일의 frame id 리스트를 초기화함
    def updateDbcInterface(self, params):
        PyCanTools._update_dbc_interface(params)

    def getCurrentDbcData(self):
        return PyCanTools._get_current_dbc_data()

    def getBlfDataList(self):
        return Utils.json_dump(self.__blf_data_list)
 
    def isReadingBlf(self):
        return self.__read_blf_is_loop
    
    def readBlf(self, fn, callback=None, filters=None):
        self.__read_blf_is_loop = True
        ext = fn[-3:].lower()
        def inner_function():
            while self.__read_blf_is_loop:
                if(ext == "blf" or ext == "BLF"):
                    data_generator = self.__read_file_log(fn, filters)
                    blf_data_list = self.__blf_data_list.append
                    for data in data_generator:
                        if callback is not None:
                            callback(Utils.json_dump(data))
                        else :
                            blf_data_list(data)
                else:
                    print("Please Check BLF file path")
                    return
                print(self.__read_blf_is_loop)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    def stopReadBlf(self):
        self.__read_blf_is_loop = False
        
    def initialize_can(self, can_channel, bustype, bitrate):
        self.__bus[can_channel] = can.interface.Bus(channel=can_channel, bustype=bustype, bitrate=bitrate)

    def can_listner_to_dict(self, can_channel):
        bus = self.__bus[can_channel]
        self.__thread_loops[can_channel] = True
        def inner_function():
            while self.__thread_loops[can_channel]:
                msg = bus.recv(1)
                parsing_data = PyCanTools._decode_raw_can_data(msg)
                if msg is not None:
                    yield {
                        'original' : {
                            'time_stamp' : msg.timestamp,
                            'can_id' :     msg.arbitration_id,
                            'can_data' :   [byte for byte in msg.data],
                            'channel' :    msg.channel
                        },
                        'parsing' : {
                            'can_data' : parsing_data
                        }
                    }
                time.sleep(0.001)
        return inner_function()

    def send_fake_can_data(self):
        msg_data = can.Message(arbitration_id = 419419504, data=[220,254, 00,00,00,00,00,00], is_extended_id=True)
        bus = can.interface.Bus(channel='test', bustype='virtual')
        def inner_function():
            while True:
                bus.send(msg_data) 
                time.sleep(0.001)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    def __verify_log(self, fn):
        try:
            ext = fn[-3:].lower()
            if(ext == "blf"):
                with can.BLFReader(fn) as f:
                    pass
            return True
        except Exception as e:
            # print("blf read fail: " + str(e))
            return False

    def __read_file_log(self, fn, filters):
        try:
            if filters is not None:
                frame_ids = Utils.json_load(filters)
                with can.BLFReader(fn) as f:               
                    for msg_data in f: 
                        if msg_data.arbitration_id in frame_ids.values():      
                        # print("\t{}".format(msg_data.timestamp))
                        # print("\t{}".format(msg_data.channel))
                        # print("\t{}".format(msg_data.data))
                        # print("\t{}".format(msg_data.arbitration_id))
                        # print("\t{}".format(msg_data.dlc))
                            yield {"timestamp": msg_data.timestamp,
                                "channel": msg_data.channel,
                                "dlc" : msg_data.dlc,
                                "canId": msg_data.arbitration_id,
                                "canData": [format(byte, '02x') for byte in msg_data.data]}
                    print("read done")
                    # self.__read_blf_is_loop = False  
            else:
                with can.BLFReader(fn) as f:     
                    msg_data = None           
                    for msg_data in f:    
     
                        msg_data = msg_data     
                        # print("\t{}".format(msg_data.timestamp))
                        # print("\t{}".format(msg_data.channel))
                        # print("\t{}".format(msg_data.data))
                        # print("\t{}".format(msg_data.arbitration_id))
                        # print("\t{}".format(msg_data.dlc))
                        # time.sleep(0.001)
                        yield {"timestamp": msg_data.timestamp,
                            "channel": msg_data.channel,
                            "dlc" : msg_data.dlc,
                            "canId": msg_data.arbitration_id,
                            "canData": [format(byte, '02x') for byte in msg_data.data]}
                    
                    print("read done")
                    # self.__read_blf_is_loop = False           
        except Exception as e:
            print("blf read fail: " + str(e) + str(msg_data))
     
if __name__ == "__main__":
    reader = Reader()
    file = 'C:/Users/User/OneDrive/바탕 화면/can-library_0.0.2/can-library/can-library/Logging_total.blf'
    test = reader.readBlf(file)
    while True:
        time.sleep(1)