import os 
import sys
import time 

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from sender import Sender
from client import Client
from utils  import Utils
from tgu    import TGU
from message_formatter import PeakSystemInterface

if __name__ == "__main__":

    channels = ['can1']
    bitrates = [500000]

    can_handler = TGU(channels=channels, 
                      bitrates=bitrates, 
                      buffer_mode=False,  
                      max_queue_size=100)  
    
    can_handler.start_all()

    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "udpSocket",
                                                "ip" : Utils.get_ipv4_address(), 
                                                "port": 50000}))

    sender = Sender(protocol='udpSocket')
    
    def external_handle_message_1(channel, messages):
        peak_msg = PeakSystemInterface(can_id=hex(messages.arbitration_id), can_data=messages.data)
        convert_can_msg = peak_msg.get_binary()
        sender.publish('172.30.1.207', 50000, convert_can_msg)

    # def external_handle_message_2(channel, messages):
    #     sender.publish('0.0.0.0', 40000, messages)

    # def external_handle_message_3(channel, messages):
    #     sender.publish('0.0.0.0', 40000, messages)

    can_handler.add_callback('can1', external_handle_message_1)
    # can_handler.add_callback('can2', external_handle_message_2)
    # can_handler.add_callback('can3', external_handle_message_3)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("프로그램이 사용자에 의해 중단되었습니다.")
    finally:
        can_handler.stop_all()
