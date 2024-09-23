import os 
import sys
import time
import json

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from can_library.sender import Sender
from can_library.client import Client
from can_library.utils  import Utils
from can_library.reader import Reader
from can_library.tgu    import TGU
from can_library.message_formatter import canmsg2json


if __name__ == "__main__":
    dbc_file =  Utils.files_abspath('wheel_loader.dbc')

    params = Utils.json_dump({
        # 'dbcframeIds': ["CFFA770", "18ffd370", "CFF0270"],
        'dbcPath': dbc_file,
        # 'canIdentifiers': "MachPosNorth"
    })

    reader = Reader()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    reader.updateDbcInterface(params=params)

    channels = ['can2']
    bitrates = [250000]

    can_handler = TGU(channels=channels, 
                      bitrates=bitrates, 
                      buffer_mode=True, 
                      buffer_size=1000, 
                      max_queue_size=100)
    
    can_handler.start_all()

    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "mqtt",
                                                     "ip"  : "172.20.10.5", 
                                                     "port": "1883"}))

    sender = Sender(protocol='mqtt')
    
    def external_handle_message_1(channel, messages):
        if isinstance(messages, list):
            messages = json.dumps(list(map(canmsg2json, messages)), indent=2)
            sender.publish(f'tgu/{channel}', messages)
        else:
            messages = json.dumps(canmsg2json(messages), indent=2)


    can_handler.add_callback('can2', external_handle_message_1)

    try:
        while True:
            sender.publish(f'/tgu/equipment-monitor/machine-information', 
                      can_handler.get_status_message())
            
            print(can_handler.get_status_message())

            time.sleep(5)
    except KeyboardInterrupt:
        print("프로그램이 사용자에 의해 중단되었습니다.")
    finally:
        can_handler.stop_all()
        print("finally.")


