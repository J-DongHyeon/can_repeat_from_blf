import os, sys, time

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

import threading
from reader   import Reader
from sender   import Sender
from client   import Client
from utils    import Utils
from message_formatter import PeakSystemInterface

class TGU(object):

    def __init__(self):
        # self.__ip         = Utils.get_ipv4_address()
        self.__protocol     = 'udpSocket'
        self.__src_ip       = '172.30.1.207'
        self.__src_port     = 50000
        
        self.__dst_ip       = '192.168.1.254'
        self.__dst_port     = 50000

        # self.__can_port      = 'can2'
        # self.__bustype = 'socketcan'

        self.__can_channel = 'test'
        self.__bustype = 'virtual'
        self.__bitrate  = 250000
        client = Client()
        client.initialize(protocol_info=Utils.json_dump({"type": self.__protocol,
                                                         "ip" : self.__src_ip, 
                                                       "port": self.__src_port}))

        self.reader_  = Reader()
        self.reader_.initialize_can(self.__can_channel , self.__bustype, self.__bitrate)

        self.initialize_dbc()
        self.reader_.send_fake_can_data()
    
    def get_status(self):
        return {
            "protocol"     : self.__protocol,
            "src_ip"       : self.__src_ip,  
            "src_port"     : self.__src_port,
            "dst_ip"       : self.__dst_ip,
            "dst_port"     : self.__dst_port,
            "can_channel"  : self.__can_channel,
            "bustype"      : self.__bustype,
            "bitrate"      : self.__bitrate
        }
    
    def initialize_dbc(self):
        #sender.streamTrcPublish('test', '192.168.5.116', 50000, trc_file, 1)
        dbc_file = f'/{parent_directory}/files/Dozer_Auto_v0.1.dbc'
        params = Utils.json_dump({
            # 'dbcframeIds': ["CFFA770", "18ffd370", "CFF0270"],
            'dbcPath': dbc_file,
            # 'canIdentifiers': "MachPosNorth"
        })                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
        self.reader_.updateDbcInterface(params=params)
        
    def get_can_data(self, callbackFunction):
        data_generator = self.reader_.can_listner_to_dict(self.__can_channel)
        def inner_function():
            while True:
                try:
                    message = next(data_generator)
                    callbackFunction(message)
                    time.sleep(1)
                except Exception as e:
                    print(e)
                time.sleep(0.001)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

if __name__ == "__main__":
    tgu = TGU()
    while True:
        time.sleep(0.001)
    #     sender.publish("172.30.1.207", 50000, b'03/01/02/04')
    #sender.transmitCanMessage('test2', '192.168.5.116', 50000, 'RCC', 'EmergEngineStopSwitchStatus', 2.0)