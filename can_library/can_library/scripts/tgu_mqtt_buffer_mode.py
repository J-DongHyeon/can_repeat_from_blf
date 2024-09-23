import os 
import sys
import time 
import json

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from sender import Sender
from client import Client
from utils  import Utils
from reader import Reader
from tgu    import TGU
from message_formatter import canmsg2json

if __name__ == "__main__":
    dbc_file =  Utils.files_abspath('conceptx.dbc')
    csv_file_path = Utils.files_abspath('TGU.csv')
    
    params = Utils.json_dump({
        # 'dbcframeIds': ["CFFA770", "18ffd370", "CFF0270"],
        'dbcPath': dbc_file,
        # 'canIdentifiers': "MachPosNorth"
    })

    reader = Reader()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    reader.updateDbcInterface(params=params)

    channels = ['can1', 'can2', 'can3']
    bitrates = [500000, 500000, 500000]

    can_handler = TGU(channels=channels, 
                      bitrates=bitrates, 
                      buffer_mode=True, 
                      buffer_size=1000, 
                      max_queue_size=100)  
    
    can_handler.start_all()

    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "mqtt",
                                                     "ip"  : can_handler.IP, 
                                                     "port": can_handler.PORT}))
    sender = Sender(protocol='mqtt')

    serial_number = Utils.get_machine_id_from_ifconfig(csv_file_path)
    def external_handle_message_1(channel, messages):
        if isinstance(messages, list):
            messages = json.dumps(list(map(canmsg2json, messages)), indent=2)
            sender.publish(f'tgu/{serial_number}/{channel}', messages)
        else:
            messages = json.dumps(canmsg2json(messages), indent=2)

    def external_handle_message_2(channel, messages):
        if isinstance(messages, list):
            messages = json.dumps(list(map(canmsg2json, messages)), indent=2)
            sender.publish(f'tgu/{serial_number}/{channel}', messages)
        else:
            messages = json.dumps(canmsg2json(messages), indent=2)

    def external_handle_message_3(channel, messages):
        if isinstance(messages, list):
            messages = json.dumps(list(map(canmsg2json, messages)), indent=2)
            sender.publish(f'tgu/{serial_number}/{channel}', messages)
        else:
            messages = json.dumps(canmsg2json(messages), indent=2)

    can_handler.add_callback('can1', external_handle_message_1)
    can_handler.add_callback('can2', external_handle_message_2)
    can_handler.add_callback('can3', external_handle_message_3)

    try:
        while True:
            sender.publish(f'/rgt/equipment-monit/{serial_number}/machine-information', 
                                 can_handler.get_status_message())
            time.sleep(10)
    except KeyboardInterrupt:
        print("프로그램이 사용자에 의해 중단되었습니다.")
    finally:
        can_handler.stop_all()
