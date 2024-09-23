#!/usr/bin/env python3
import os, sys
import time

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from client   import Client
from utils    import Utils
from receiver import Receiver

if __name__ == "__main__":
   
    # bus = can.interface.Bus(channel='can2', bustype='socketcan', bitrate=500000)
    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "udpSocket",
                                                "ip" : "172.30.1.207", 
                                                "port": 40000}))
    udp_socket = client.get_protocol('udpSocket')

    udp_receiver = Receiver('udpSocket')

    udp_receiver.initialize()
    #callback function
    def calblack(msg):
        print(msg)

    udp_receiver.createSubscription(calblack) 
    
    while True:
        print(udp_socket.is_connected())
        time.sleep(1)















































