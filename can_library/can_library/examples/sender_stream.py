#!/usr/bin/env python3
import os, sys
import time
from pathlib import Path

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from sender   import Sender
from client   import Client
from utils    import Utils

if __name__ == "__main__":
   
    # bus = can.interface.Bus(channel='can2', bustype='socketcan', bitrate=500000)
    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "udpSocket",
                                                "ip" : "172.30.1.207", 
                                                "port": 50000}))
    udp_socket = client.get_protocol('udpSocket')

    trc_file = os.path.join(Path(__file__).parent.parent, 'files/dozer_0628_3_2.trc')

    sender = Sender(protocol='udpSocket')
    sender.streamTrcPublish('threadId', '0.0.0.0', 40000, trc_file, 1)

    while True:
        print(udp_socket.is_connected())
        time.sleep(1)















































