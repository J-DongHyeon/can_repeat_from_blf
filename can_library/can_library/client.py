from can_library.utils import Utils
from can_library.protocols import PyTcpSocket, PyMqtt, PyUdpSocket

class Client:
    '''
    protocol function()
    protocol.connect()
    protocol.loop_start()
    protocol.disconnect()
    protocol.is_connected()
    protocol.status()
    '''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 프로토콜 초기화 작업
            cls._instance.protocols = {
                "udpSocket": PyUdpSocket(),
                "tcpSocket": PyTcpSocket(),
                'mqtt' : PyMqtt()
            }
        return cls._instance
    
    def initialize(self, protocol_info:dict)-> None:
        protocol_info = Utils.json_load(protocol_info)
        if "type" in protocol_info and "ip" in protocol_info and "port" in protocol_info:
            protocol_type = protocol_info["type"]
            if protocol_type in self.protocols:
                protocol = self.protocols[protocol_type]
                print("Initialized with data:", protocol_info)
                protocol.update_connection_info(protocol_info)
                protocol.connect()
                protocol.loop_start()
            else:
                print("Unsupported protocol type:", protocol_info["type"])
        else:
            print("Incomplete data provided for initialization")

    def get_protocol(self, protocol_name):
        if protocol_name in self.protocols:
            return self.protocols[protocol_name]
        else:
            return None