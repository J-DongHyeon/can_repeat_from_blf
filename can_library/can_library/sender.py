import time
import threading

from can_library.pycantools import PyCanTools
from can_library.utils import Utils
from abc import ABC, abstractmethod

from can_library.client import Client
from can_library.system_information import systemInformation_access

class AbstractSender(ABC):
    '''
    Sender는 Client에 정의 된 데이터에 대하여 전송하는 기능을 담당한다 
    '''
    @abstractmethod
    def publish(self, topicUrl: str, msg: dict, qos=0) -> None:
        pass

    @abstractmethod
    def periodic_publish(self, topicUrl: str, msg: dict, qos=0, frequency=1) -> None:
        pass

    @abstractmethod
    def transmit_can_message(self, topicUrl: str, threadingId: str, data: list, qos=0, frequency=1) -> None:
        pass

    @abstractmethod
    def stream_trc_publish(self, topicUrl: str, trcFile: str, qos=0, frequency=0) -> None:
        pass

    @abstractmethod
    def stop_publish(self, topicUrl: str) -> None:
        pass

    @abstractmethod
    def stop_all_pulibsh(self) -> None:
        pass
    
class Sender:
    def __init__(self, protocol):
        if protocol == "mqtt":
            self.__custom_sender = MQTTSender(protocol)
        elif protocol == "tcpSocket":
            self.__custom_sender = TcpSocketSender(protocol)
        elif protocol == "udpSocket":
            self.__custom_sender = UdpSocketSender(protocol)
        print(f"\t[Initialize {protocol} Sender]")

    def publish(self, *args, **kwargs)-> None:
        self.__custom_sender.publish(*args, **kwargs)

    def periodicPublish(self, *args, **kwargs)-> None:
        self.__custom_sender.periodic_publish(*args, **kwargs)

    def transmitCanMessage(self, *args, **kwargs)-> None:
        self.__custom_sender.transmit_can_message(*args, **kwargs)

    def streamTrcPublish(self, *args, **kwargs)-> None:
        self.__custom_sender.stream_trc_publish(*args, **kwargs)

    def stopPublish(self, *args, **kwargs)-> None:
        self.__custom_sender.stop_publish(*args, **kwargs)

    def stopAllSPublish(self)-> None:
        self.__custom_sender.stop_all_pulibsh()

@systemInformation_access
class MQTTSender(AbstractSender):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__thread_loops = {}
        self.__thread_list  = {}
        self.__sender_log   = {}

    def publish(self, topicUrl:str, msg:dict, qos=0)-> None:
        self.__client.publish_message(topicUrl, msg, qos)

    def periodic_publish(self, topicUrl:str, msg:dict, qos=0, frequency=1)-> None:
        self.__thread_loops[topicUrl] = True
        def inner_function():
            while self.__thread_loops[topicUrl]:
                self.__client.publish_message(topicUrl, msg, qos)
                time.sleep(frequency)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(topicUrl, True)

    def transmit_can_message(self, 
                             topicUrl:str, 
                             arbitrationId:str, 
                             data:list, 
                             qos=0, 
                             frequency=1)-> None:
        
        arbitration_id = int(arbitrationId, 16)
        self.__thread_loops[topicUrl] = True

        def inner_function():
            while self.__thread_loops[topicUrl]:
                message = {
                    "id": format(arbitration_id, '08X'),
                    "dt": data
                }
                self.__client.publish_message(topicUrl, Utils.json_dump(message), qos)
                time.sleep(frequency)

        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(topicUrl, True)

    def stream_trc_publish(self, topicUrl:str, trcFile:str, qos=0, frequency=0)-> None:
        from pycantools import PyCanTools
        crawler = PyCanTools.crawl_can_messages_from_trc(trcFile)
        self.__thread_loops[topicUrl] = True
        def inner_function():
            while self.__thread_loops[topicUrl]:
                try:
                    message = next(crawler)
                    self.__client.publish_message(topicUrl, Utils.json_dump(message), qos) 
                    time.sleep(frequency)
                except StopIteration:
                    print("데이터 소진")
                    self.__thread_loops[topicUrl] = False
                    break
                except Exception as e:
                    print("오류 발생:", e)
                    break
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(topicUrl, True)

    def stop_publish(self, topicUrl:str)-> None:
        if topicUrl in self.__thread_loops :
            self.__thread_loops[topicUrl] = False
            self.__update_thread_list(topicUrl, False)
        else:
            print("Can't thread stop check in topic url")

    def stop_all_pulibsh(self)-> None:
        for threadingId in self.__thread_loops:
            self.stop_publish(threadingId)

    def __update_thread_list(self, topicUrl, result):
        self.__thread_list[topicUrl] = result
        self.__sender_log['threadList'] = self.__thread_list
        self.set_data('sender', self.__sender_log)

class TcpSocketSender(AbstractSender):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__thread_loops = {}
        self.__is_loop = True
        
    def publish(self, msg:bytearray)-> None:
        self.__client.publish_message(msg)

    def periodic_publish(self, arbitrationId:str, msg:bytearray, frequency=1)-> None:
        self.__thread_loops[arbitrationId] = True
        def inner_function():
            while self.__thread_loops[arbitrationId]:
                self.__client.publish_message(msg)
                time.sleep(frequency)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    def transmit_can_message(self, arbitrationId:str, length:int, data:list, frequency=1)-> None:
        self.__thread_loops[arbitrationId] = True
        def inner_function():
            while self.__thread_loops[arbitrationId]:
                arbitration_id_int = int(arbitrationId, 16)

                # Convert data hex strings to integers
                data_integers = [int(x, 16) for x in data]

                # Combine everything into a bytearray
                combined_data = bytearray()
                combined_data.extend((arbitration_id_int >> 24) & 0xFF)
                combined_data.extend((arbitration_id_int >> 16) & 0xFF)
                combined_data.extend((arbitration_id_int >> 8) & 0xFF)
                combined_data.extend(arbitration_id_int & 0xFF)
                combined_data.extend(length.to_bytes(1, 'big'))
                combined_data.extend(data_integers)
                # self.__client.publish_message(combined_data, ip, port)
                time.sleep(frequency)

        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    def stream_trc_publish(self, topicUrl:str, trcFile:str, qos=0, frequency=0)-> None:
        print(f"CustomSender2 - stream_trc_publish: {topicUrl}, {trcFile}, {qos}, {frequency}")

    def stop_publish(self, arbitrationId) -> None:
        if arbitrationId in self.__thread_loops :
            self.__thread_loops[arbitrationId] = False
        else:
            print("Can't thread stop check in topic url")  

@systemInformation_access
class UdpSocketSender(AbstractSender):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__thread_loops = {}
        self.__thread_list  = {}
        self.__sender_log   = {}

    def publish(self, ip:str, port:int, data:bytearray)-> None:
        self.__client.publish_message(data, ip, port)
    
    def periodic_publish(self, 
                         threadingId:str, 
                         ip:str, 
                         port:int, 
                         data:bytearray, 
                         frequency=1)-> None:
        
        self.__thread_loops[threadingId] = True
        def inner_function():
            while self.__thread_loops[threadingId]:
                self.publish(ip, port, data)
                time.sleep(frequency)
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(threadingId, ip, port, True)

    def transmit_can_message(self, 
                             threadingId:str, 
                             ip:str, 
                             port:int, 
                             messageName:str,
                             signalName:str,
                             data:int, 
                             frequency=1) -> None:
        self.__thread_loops[threadingId] = True
        byte_array_msg = PyCanTools._encode_signal_data(messageName, signalName, data)
        def inner_function():
            while self.__thread_loops[threadingId]:
                self.publish(ip, port, byte_array_msg)
                time.sleep(frequency)

        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(threadingId, ip, port, True)

    def stream_trc_publish(self, 
                           threadingId:str,
                           ip:str, 
                           port:int, 
                           trcFile:str, 
                           frequency=0.001)-> None:
        self.__thread_loops[threadingId] = True
        crawler = PyCanTools._crawl_bytearray_can_messages_from_trc(trcFile)
        def inner_function():
            while self.__thread_loops[threadingId]:
                try:
                    message  = next(crawler)
                    self.publish(ip, port, message) 
                    time.sleep(frequency)
                except StopIteration as e :
                    print("데이터 소진 : ", e)
                    break
                except Exception as e:
                    pass
                    break
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()
        self.__update_thread_list(threadingId, ip, port, True)

    def stop_publish(self, threadingId:str)-> None:
        if threadingId in self.__thread_loops :
            self.__thread_loops[threadingId]  = False
            self.__sender_log['threadList'] = self.__thread_list
            self.__update_thread_list(threadingId, 
                                      self.__thread_list[threadingId]['ip'], 
                                      self.__thread_list[threadingId]['port'], 
                                      False)
        else:
            print("Can't thread stop check in topic url")  

    def stop_all_pulibsh(self)-> None:
        for threadingId in self.__thread_loops:
            self.stop_publish(threadingId)

    def __update_thread_list(self, threadingId, ip, port, result):
        self.__thread_list[threadingId] = {
            'process'     : result,
            'ip'          : ip,
            'port'        : port,
        }
        self.__sender_log['threadList'] = self.__thread_list
        self.set_data('sender', self.__sender_log)