import os
import sys
import time

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

import can
from can_library.tgu import TGU
from can_library.client import Client
from can_library.utils  import Utils
from can_library.receiver import Receiver



can_bus = can.interface.Bus(channel='can1', bustype='socketcan', bitrate=500000)

def mqtt_callback_forward(message):
    print("wheel_loader/forward topic callback function")

    can_data = can.Message(arbitration_id=0x3F2, data=[11, 11, 11, 11, 00, 00, 00, 00])

    can_bus.send(can_data)

    print(message)

def mqtt_callback_backward(message):
    print("wheel_loader/backward topic callback function")

    can_data = can.Message(arbitration_id=0x3F2, data=[11, 11, 11, 11, 00, 00, 00, 00])

    can_bus.send(can_data)

    print(message)

def mqtt_callback_left(message):
    print("wheel_loader/left topic callback function")

    can_data = can.Message(arbitration_id=0x3F2, data=[11, 11, 11, 11, 00, 00, 00, 00])

    can_bus.send(can_data)

    print(message)

def mqtt_callback_right(message):
    print("wheel_loader/right topic callback function")

    can_data = can.Message(arbitration_id=0x3F2, data=[11, 11, 11, 11, 00, 00, 00, 00])

    can_bus.send(can_data)

    print(message)

def mqtt_callback_stop(message):
    print("wheel_loader/stop topic callback function")

    can_data = can.Message(arbitration_id=0x3F2, data=[11, 11, 11, 11, 00, 00, 00, 00])

    can_bus.send(can_data)

    print(message)


client = Client()
client.initialize(protocol_info=Utils.json_dump({"type": "mqtt",
                                                     "ip"  : "172.30.1.216",
                                                     "port": 1883}))

channel = ['can1']
bitrate = [500000]

can_handler = TGU(channels=channel,
                  bitrates=bitrate,
                  buffer_mode=True,
                  buffer_size=1000,
                  max_queue_size=100)

can_handler.start_all()

receiver = Receiver(protocol='mqtt')
receiver.initialize()

receiver.createSubscription("wheel_loader/forward", mqtt_callback_forward)
receiver.createSubscription("wheel_loader/backward", mqtt_callback_backward)
receiver.createSubscription("wheel_loader/left", mqtt_callback_left)
receiver.createSubscription("wheel_loader/right", mqtt_callback_right)
receiver.createSubscription("wheel_loader/stop", mqtt_callback_stop)



try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("프로그램이 사용자에 의해 중단되었습니다.")
finally:
    can_handler.stop_all()
    print("finally.")


