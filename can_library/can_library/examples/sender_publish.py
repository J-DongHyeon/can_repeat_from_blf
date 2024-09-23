#!/usr/bin/env python3
import os, sys
import time
current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from sender   import Sender
from client   import Client
from utils    import Utils

if __name__ == "__main__":
    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "udpSocket",
                                                "ip" : "172.30.1.207", 
                                                "port": 50000}))
    udp_socket = client.get_protocol('udpSocket')
    sender = Sender(protocol='udpSocket')
    while True:
        print(udp_socket.is_connected())
        sender.publish('0.0.0.0', 40000, b'1111111')
        time.sleep(1)















































