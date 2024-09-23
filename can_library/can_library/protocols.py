import socket
import time
import threading

import paho.mqtt.client as mqtt

from can_library.system_information import systemInformation_access

from abc import ABC, abstractmethod

class Protocols(ABC):
    def __init__(self, protocol_info):
        self.protocol_info = protocol_info

    @abstractmethod
    def status(self) -> dict:
        ''' 
        현재의 통신 status들에 대한 데이터 리턴
        '''
        pass
    
    @abstractmethod
    def connect(self) -> None:
        '''
        통신 레이어 연결
        '''
        pass
    
    @abstractmethod
    def loop_start(self) -> None:
        ''' 
        세션 유지 및 리커넥트 로직 
        '''
        pass

    @abstractmethod
    def disconnect(self) -> None:
        '''
        세션 종료
        '''
        pass

    @abstractmethod
    def publish_message(self) -> None:
        '''
        메세지 전송 
        '''
        pass

class PyTcpSocket(Protocols):
    def __init__(self):
        # self.__name                = protocol_info['type']
        # self.__ip                  = protocol_info['ip']
        # self.__port                = protocol_info['port']
        # self.__role                = protocol_info['role']
        self.__stop_event          = threading.Event()
        self.__lock                = threading.Lock()
        self.__session_active      = False
        self.__on_message_callback = False

    def status(self)-> dict:
        return {
            'protocol': self.__name,
            'ip'      : self.__ip,
            'port'    : int(self.__port),
            'session' : self.__session_active
        }
    
    def connect(self)-> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self.__role == "server":
                self._server_socket.bind((self.__ip, self.__port))
                self._server_socket.listen(1)
                print("-------------------------------------------")
                print("------------SERVER INFORMATION-------------")
                print(f"\t[IP: [{self.__ip} / PORT: {self.__port}]")
                print("-------------------------------------------")
            elif self.__role == "client":
                self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
        except OSError as os_error:
            print(f"Error while binding/listening/connecting: {os_error}")
            self.__session_active = False
        except Exception as error:
            print(f"Unexpected error during socket connection: {error}")
            self.__session_active = False

    def disconnect(self)-> None:
        self.__stop_event.set()

    def publish_message(self, message)-> None:
        if self.__session_active:
            try:
                with self.__lock :
                    if self.__role == "server":
                        self.server_pub.sendall(message)
                    elif self.__role == 'client':
                        self._client_socket.sendall(message)
            except BrokenPipeError as e:
                print(f"클라이언트와의 연결이 끊겼습니다: {e}")
                self.__session_active = False
            except Exception as e:
                print(f"클라이언트와 연결되지 않았습니다: {e}")
                self.__session_active = False

    def add_message_callback(self, function)-> None:
        self.__on_message_callback = function

    def receiver_data(self)-> None:
        client_socket, client_address = self._server_socket.accept()
        print(f"클라이언트가 연결 되었습니다. 주소: {client_address}")
        self.server_pub = client_socket

        while not self.__stop_event.is_set():
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                self.__session_active = True
                if self.__on_message_callback :
                    self.__on_message_callback(data)

            except ConnectionResetError as reset_error:
                # print(f"클라이언트와의 연결이 끊겼습니다: {reset_error}")
                pass
            except Exception as e:
                # print(f"Unexpected error during data reception: {e}")
                pass

        print(f"클라이언트와의 연결이 종료되었습니다.")
        client_socket.close()
        
    def loop_start(self)-> None:
        def inner_function():
            while not self.__stop_event.is_set():
                if not self.__session_active :
                    local_thread = threading.Thread(target=self.receiver_data)
                    local_thread.daemon = True
                    local_thread.start()
                time.sleep(1)
        t = threading.Thread(target =inner_function)
        t.daemon = True
        t.start()

@systemInformation_access
class PyUdpSocket(Protocols):
    def __init__(self):
        self.__stop_event          = threading.Event()
        self.__session_active      = False
        self.__on_message_callback = False

    def status(self)-> dict:
        return {
            'protocol': self.__name,
            'ip': self.__ip,
            'port': int(self.__port),
            'session': self.__session_active
        }
    
    def update_connection_info(self, protocol_info)-> None:
        self.__name = protocol_info['type']
        self.__ip   = protocol_info['ip']
        self.__port = protocol_info['port']
        self.set_data('UDPClient', self.status())

    def connect(self)-> None:
        try:
            self.__stop_event.clear()
            self.__udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__udp_socket.bind((self.__ip, self.__port))
            self.__session_active = True
            self.set_data('UDPClient', self.status())
        except OSError as os_error:
            print(f"Error while binding UDP socket: {os_error}")
            self.__session_active = False
        except Exception as error:
            print(f"Unexpected error during UDP socket initialization: {error}")
            self.__session_active = False

    def is_connected(self)-> None:
        return self.__session_active 
    
    def disconnect(self)-> None:
        self.__stop_event.set()
        self.__udp_socket.close()
        self.__session_active = False
    
    def publish_message(self, message, ip, port)-> None:
        try:
            self.__udp_socket.sendto(message, (ip, port))
        except Exception as e:
            # print(f"Error during UDP message publication: {e}")
            pass

    def add_message_callback(self, function)-> None:
        self.__on_message_callback = function

    def receiver_data(self)-> None:
        while not self.__stop_event.is_set():
            try:
                data, _ = self.__udp_socket.recvfrom(1024)

                if not data:
                    continue

                self.__session_active = True
                if self.__on_message_callback:
                    self.__on_message_callback(data)
                    
            except Exception as e:
                print(f"Error handling UDP data: {e}")
                self.__session_active = False

    def loop_start(self)-> None:
        local_thread = threading.Thread(target=self.receiver_data)
        local_thread.daemon = True
        local_thread.start()
        
@systemInformation_access
class PyMqtt():
    def __init__(self):
        self.__mqttc              = mqtt.Client(client_id="", clean_session=True, userdata=None)
        self.__mqttc.on_connect   = self._on_connect
        self.__mqtt_session_alive = False

    def status(self) -> dict:
        return {
            'protocol': self.__name,
            'session': self.__mqtt_session_alive,
            'ip': self.__ip,
            'port': int(self.__port),
            'userName': self.__user_name,
            'password': self.__password,
            'subscirberList' : self.__subcriber_url
        }
    
    def update_connection_info(self, protocol_info)-> None:
        self.__name               = "mqtt"
        self.__ip                 = protocol_info.get('ip')
        self.__port               = protocol_info.get('port')
        self.__user_name          = protocol_info.get('id') or None
        self.__password           = protocol_info.get('password') or None
        self.__keep_alive         = protocol_info.get('keepAlive') or 30
        self.__subcriber_url      = []
        self.set_data('MQTTClient', self.status())

    def connect(self) -> None:
        try:
            if self.__user_name is not None and self.__password is not None:
                self.__mqttc.username_pw_set("/:" + self.__user_name, self.__password)
            self.__mqttc.connect(self.__ip, int(self.__port), keepalive=int(self.__keep_alive), bind_address="")
        except:
            pass

    def _on_connect(self, client, userdata, flags, rc)-> None:
        try:
            if rc == 0:
                self.__mqtt_session_alive = True
            else:
                self.__mqtt_session_alive = False
            print("\tConnect Result: {}".format(self.__mqtt_session_alive))
            self.set_data('MQTTClient', self.status())
        except Exception as e:
            print("\terror in on_connect: " + str(e))

    def un_subscriber(self, url:str) -> None:
        if type(url) == str:
            result, _ = self.__mqttc.unsubscribe(url)
            if result == mqtt.MQTT_ERR_SUCCESS:
                print(f"\tUN_SUBCRIBE_SUCCESS: {url}")
                self.__subcriber_url.remove(url)
            else:
                print(f"\tUN_SUBCRIBE_FAILED:  {url}")

        elif type(url) == list:
            for topic in url :
                result, _ = self.__mqttc.unsubscribe(topic)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    print(f"\tUN_SUBCRIBE_SUCCESS: {topic}")
                    self.__subcriber_url.remove(url)
                else:
                    print(f"\tUN_SUBCRIBE_FAILED:  {topic}")
        self.set_data('MQTTClient', self.status())

    def add_message_callback(self, function)-> None:
        self.__mqttc.on_message = function

    def add_subscriber(self, url:str, qos:int) -> None:
        if type(url) == str:
            result, _ = self.__mqttc.subscribe(url, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                print(f"\tSUBCRIBE_SUCCESS: {url}")
                self.__subcriber_url.append(url)
            else:
                print(f"\tSUBCRIBE_FAILED:  {url}")

        elif type(url) == list:
            for topic in url :
                result, _ = self.__mqttc.subscribe(topic, 0)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    print(f"\tSUBCRIBE_SUCCESS: {topic}")
                    self.__subcriber_url.append(url)
                else:
                    print(f"\tSUBCRIBE_FAILED:  {topic}")
        self.set_data('MQTTClient', self.status())

    def loop_start(self)-> None:
        def inner_function():
            while True:
                rc = self.__mqttc.loop(0.1)
                if rc != mqtt.MQTT_ERR_SUCCESS:
                    try:
                        self.__mqtt_session_alive = False
                        print("\tConnect Result: {}".format(mqtt.error_string(rc)))
                        print("\tMqtt Reconnect...")
                        time.sleep(1)
                        self.__mqttc.reconnect()
                    except :
                        pass

        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    def publish_message(self, topic:str, msg, qos:int) -> None:
        self.__mqttc.publish(topic, payload = msg, qos = qos, retain = False)