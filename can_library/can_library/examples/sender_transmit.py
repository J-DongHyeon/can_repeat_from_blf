#!/usr/bin/env python3
import os, sys
import time
from pathlib import Path

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from reader   import Reader
from sender   import Sender
from client   import Client
from utils    import Utils

if __name__ == "__main__":
    client = Client()
    client.initialize(protocol_info=Utils.json_dump({"type": "udpSocket",
                                                "ip" : "172.30.1.207", 
                                                "port": 50000}))
    udp_socket = client.get_protocol('udpSocket')

    dbc_file = os.path.join(Path(__file__).parent.parent, 'files/Excavator_NonASCII_v0.1.dbc')

    params = Utils.json_dump({
        # 'dbcframeIds': ["CFFA770", "18ffd370", "CFF0270"],
        'dbcPath': dbc_file,
        # 'canIdentifiers': "MachPosNorth"
    })

    reader   = Reader()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    reader.updateDbcInterface(params=params)

    sender = Sender(protocol='udpSocket')
    sender.transmitCanMessage('threadId', '0.0.0.0', 40000, 'RCC', 'EmergEngineStopSwitchStatus', 2.0)
    while True:
        print(udp_socket.is_connected())
        time.sleep(1)















































