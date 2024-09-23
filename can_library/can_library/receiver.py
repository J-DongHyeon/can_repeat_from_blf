import queue
import threading

from can_library.utils import Utils
from can_library.pycantools import PyCanTools
from can_library.client import Client
from can_library.system_information import systemInformation_access
from abc import ABC, abstractmethod

class AbstractReceiver(ABC):
    '''
    Receiver client 및 can_port를 통해 전달 받은 데이터를 바이패스 또는 가공하여 callback한다
    '''
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def create_subscription(self, callback=None, executeFunction=None) -> None:
        pass

    @abstractmethod
    def stop_receiver(self) -> None:
        pass

class Receiver:
    def __init__(self, protocol):
        if protocol == "mqtt":
            self.__custom_receiver = MQTTReceiver(protocol)
        elif protocol == "tcpSocket":
            self.__custom_receiver = TcpSocketReceiver(protocol)
        elif protocol == "udpSocket":
            self.__custom_receiver = UdpSocketReceiver(protocol)
        print(f"\t[Initialize {protocol} Receiver]")

    def initialize(self)-> None:
        self.__custom_receiver.initialize()

    def createSubscription(self, *args, **kwargs)-> None:
        self.__custom_receiver.create_subscription(*args, **kwargs)

    def cancelSubscription(self, *args, **kwargs)-> None:
        self.__custom_receiver.cancle_subscription(*args, **kwargs)

    def stopReceiver(self)-> None:
        return self.__custom_receiver.stop_receiver()

    def releaseReceiver(self)-> None:
        return self.__custom_receiver.release_receiver()

class TcpSocketReceiver(AbstractReceiver):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__method_funtion      = {}
        self.__execute_function    = {0 : PyCanTools._json_to_dict_extractor}
        self.__message_queue       = queue.SimpleQueue()

    def initialize(self) -> None:
        self.__client.add_message_callback(self._message_enqueue)
        self.__on_message_thread = threading.Thread(target=self._process_received_messages)
        self.__on_message_thread.daemon = True
        self.__on_message_thread.start()

    def create_subscription(self, callback=None, executeFunction=None)-> None:
        assert self.__client.status()['protocol'] == "tcpSocket", "Protocol must be socket for this method."
        assert callback is not None and callback, "Empty or None value for callback is not allowed."

        def inner_function(msg):
            data_generator = self.__execute_function[executeFunction](msg)
            for data in data_generator:
                json_dump = Utils.json_dump
                if data is not None:
                    callback(json_dump(data))

        if executeFunction is None :
            self.__method_funtion = callback
        else:
            condition = PyCanTools._is_dbc_defined()
            assert not (condition == False and executeFunction == 0), "You've passed the executeFunction parameter, but not the DBC file."
            if condition and executeFunction == 0:
                self.__method_funtion = inner_function
            else:
                self.__method_funtion = callback

    def _message_enqueue(self, msg)-> None:
        self.__message_queue.put(msg)

    def _process_received_messages(self)-> None:
        while True:
            try:
                msg = self.__message_queue.get()
                self.__method_funtion(msg)
            except Exception as e:
                print("Error in message processing:", e)
                
    def stop_receiver(self)-> None:
        self.__method_funtion = None
        self.__stop_event.set()
        self.__message_queue  = queue.SimpleQueue()

@systemInformation_access
class UdpSocketReceiver(AbstractReceiver):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__method_funtion      = None
        self.__execute_function    = {0 : PyCanTools._json_to_dict_extractor,
                                      1 : PyCanTools._bytearray_convert_to_dict_data,
                                      2 : PyCanTools._bytearray_convert_to_parser_data}

        self.__message_queue       = queue.SimpleQueue()
        self.__stop_event          = threading.Event()
        self.__reciver_log         = {}
        
    def initialize(self) -> None:
        self.__stop_event.clear()
        self.__client.add_message_callback(self._message_enqueue)
        self.__on_message_thread = threading.Thread(target=self._process_received_messages)
        self.__on_message_thread.daemon = True
        self.__on_message_thread.start()
        self.__reciver_log['initialize'] = True
        self.set_data('receiver', self.__reciver_log)
 
    def create_subscription(self, callback=None, executeFunction=None) -> None:
        assert self.__client.status()['protocol'] == "udpSocket", "Protocol must be socket for this method."
        assert callback is not None and callback, "Empty or None value for callback is not allowed."
        
        self.__reciver_log['callbackFunction'] = True

        def inner_function(msg):
            data_generator = self.__execute_function[executeFunction](msg)
            self.__reciver_log['executeFunction'] = PyCanTools._can_tools_function_names(executeFunction)
            json_dump = Utils.json_dump
            for data in data_generator:
                if data is not None:
                    callback(json_dump(data))

        if executeFunction is not None:
            self.__method_funtion = inner_function
        else:
            self.__method_funtion = callback
        self.set_data('receiver', self.__reciver_log)

    def _message_enqueue(self, msg)-> None:
        self.__message_queue.put(msg)
        
    def _process_received_messages(self)-> None:
        while not self.__stop_event.is_set():
            try:
                msg = self.__message_queue.get()
                self.__reciver_log['processReceived'] = True
                self.__reciver_log['lastByteArrayData'] = str(msg)

                self.__method_funtion(msg)
            except Exception as e:
                # print("Error in message processing:", e)
                self.__reciver_log['processReceived'] = False
            finally:
                self.set_data('receiver', self.__reciver_log)

    def stop_receiver(self)-> None:
        self.__stop_event.set()

    def release_receiver(self)-> None:
        self.__stop_event.clear()

@systemInformation_access
class MQTTReceiver(AbstractReceiver):
    def __init__(self, protocol):
        client = Client()
        self.__client = client.get_protocol(protocol)
        self.__method_funtion      = {}
        self.__execute_function    = {0 : PyCanTools._json_to_dict_extractor}
        self.__stop_event          = threading.Event()
        self.__message_queue       = queue.SimpleQueue()
        self.__reciver_log         = {}

    def initialize(self)-> None:
        self.__stop_event.clear()
        self.__client.add_message_callback(self._message_enqueue)
        self.__on_message_thread = threading.Thread(target=self._process_received_messages)
        self.__on_message_thread.daemon = True
        self.__on_message_thread.start()
        self.__reciver_log['initialize'] = True
        self.set_data('receiver', self.__reciver_log)

    def create_subscription(self,
                            topicUrl=None,
                            callback=None,
                            executeFunction=None,
                            qos=0) -> None:
        '''
        topicUrl= '/test',
        callback= int(inner funtion)
                  0 : 캔 메세지의 데이터를 decode하여 dict으로 반환
        '''
        assert self.__client.status()['protocol'] == "mqtt", "Protocol must be MQTT for this method."
        assert callback is not None and callback, "Empty or None value for callback is not allowed."
        self.__client.add_subscriber(topicUrl, qos)

        self.__reciver_log['callbackFunction'] = True

        def inner_function(msg):
            data_generator = self.__execute_function[executeFunction](msg)
            self.__reciver_log['executeFunction'] = PyCanTools._can_tools_function_names(executeFunction)
            for data in data_generator:
                json_dump = Utils.json_dump
                if data is not None:
                    callback(json_dump(data))

        if executeFunction is None :
            self.__method_funtion[topicUrl] = callback
        else:
            condition = PyCanTools._is_dbc_defined()
            assert not (condition == False and executeFunction == 0), "You've passed the executeFunction parameter, but not the DBC file."
            if condition and executeFunction == 0:
                self.__method_funtion[topicUrl] = inner_function
            else:
                self.__method_funtion[topicUrl] = callback

        self.set_data('receiver', self.__reciver_log)

    def cancle_subscription(self,
                            topicUrl:str) -> None:
        '''
        topicUrl= '/test',
        '''
        assert topicUrl is not None and topicUrl, "Empty or None value for topicUrl is not allowed."

        if topicUrl in self.__client.status()['subscirberList']:
            self.__client.un_subscriber(topicUrl)
            self.__method_funtion[topicUrl] = None
            if not self.__client.status()['subscirberList']:
                self.__reciver_log['callbackFunction'] = False
                self.set_data('receiver', self.__reciver_log)
        else:
            print("TopicUrl is not definition")

    def _message_enqueue(self, client, obj, msg)-> None:
        self.__message_queue.put(msg)

    def _process_received_messages(self)-> None:
        while not self.__stop_event.is_set():
            try:
                msg = self.__message_queue.get()
                self.__reciver_log['processReceived'] = True
                topic = msg.topic
                byte_to_dict = Utils.json_load(msg.payload)
                self.__method_funtion[topic](byte_to_dict)
            except Exception as e:
                print("Error in message processing:", e)
                self.__reciver_log['processReceived'] = False
            finally:
                self.set_data('receiver', self.__reciver_log)

    def stop_receiver(self)-> None:
        self.__stop_event.set()

    def release_receiver(self)-> None:
        self.__stop_event.clear()