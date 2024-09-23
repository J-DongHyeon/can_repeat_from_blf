import can
import threading
import queue
import time

from can_library.message_formatter import StatusMessage
from can_library.pycantools import PyCanTools
from can_library.utils import MovingAverageFilter



ENGINE_SPEED = "EngineSpeed"
FF1E_ENGINE_SPEED = "FF1E_EngineSpeed"
FUEL_LEVEL = "FuelLevel"
FFD8_FUEL_LEVEL = "FFD8_FuelLevel"
FF45_GAUGE_DATA_FUEL_LEVEL = "FF45_GaugeData_FuelLevel"
FUEL_LEVEL1 = "FuelLevel1"
FUEL_LEVEL2 = "FuelLevel2"
HYDRAULIC_OIL_TEMPERATURE = "HydraulicOilTemperature"
ENGINE_COOLANT_TEMPERATURE = "EngineCoolantTemperature"
FF45_GAUGE_DATA_COOLANT_TEMP = "FF45_GaugeData_CoolantTemp"
FFD8_COOLANT_TEMP = "FFD8_CoolantTemp"
ENGINE_FUEL_RATE = "EngineFuelRate"
FFDA_COOLANT_LEVEL = "FFDA_CoolantLevel"
ENGINE_COOLANT_LEVEL1 = "EngineCoolantLevel1"
ENGINE_TOTAL_HOURS_OF_OPERATION = "EngineTotalHoursOfOperation"
ENGINE_TOTAL_FUEL_USED = "EngineTotalFuelUsed"
FF21_ENGINE_TOTAL_FUEL_USED = "FE21_EngineTotalFuelUsed"


class TGU:
    KEY = [ENGINE_SPEED,
           FF1E_ENGINE_SPEED,
           FUEL_LEVEL,
           FFD8_FUEL_LEVEL,
           FF45_GAUGE_DATA_FUEL_LEVEL,
           FUEL_LEVEL1,
           FUEL_LEVEL2,
           HYDRAULIC_OIL_TEMPERATURE,
           ENGINE_COOLANT_TEMPERATURE,
           FF45_GAUGE_DATA_COOLANT_TEMP,
           FFD8_COOLANT_TEMP,
           ENGINE_FUEL_RATE,
           FFDA_COOLANT_LEVEL,
           ENGINE_COOLANT_LEVEL1,
           ENGINE_TOTAL_HOURS_OF_OPERATION,
           ENGINE_TOTAL_FUEL_USED,
           FF21_ENGINE_TOTAL_FUEL_USED
           ]


# 각 멤버 필드 초기화
    def __init__(self, channels, bitrates, bustype='socketcan', buffer_mode=False, buffer_size=1000, max_queue_size=100):
        self._channels = channels # can 포트 번호
        self._bitrates = bitrates # can 통신 속도
        self._bustype  = bustype
        self._buffer_mode = buffer_mode # 수신된 can 데이터를 버퍼에 모았다가 처리할지 바로 처리할지 on/off
        self._buffer_size = buffer_size # 버퍼 사이즈
        self._max_queue_size = max_queue_size # 각 can 포트의 메시지 큐 사이즈
        self._status_message = StatusMessage() # 장비 상태정보를 가지고 있는 객체
        self._receivers = {} # 각 can 포트 별로 can bus 객체를 저장하는 딕셔너리

        self._lock = threading.Lock() # 스레드 임계구역 처리를 위한 객체
        self._msg_queues = {ch: queue.Queue() for ch in channels} # 각 can 포트 별로 메시지 큐를 저장하는 딕셔너리
        self._is_running = False # can 데이터 수신 스레드의 동작 상태
        self._is_parsing = False # 메시지 큐로부터 can 데이터 파싱 중인지 동작 상태
        self._callbacks = {ch: [] for ch in channels} # 각 can 포트 별로 콜백 함수를 저장하는 딕셔너리

        self._engine_speed_avg_filter = MovingAverageFilter(buffer_size=20) # EngineSpeed CAN 데이터 이동평균 필터

        self.fake_data() # EngineTotalHoursOfOperation, EngineTotalIdleHours CAN 데이터를 수신하기 위한 CAN 데이터 전송
        print('\t[Initialize TGU]')

# 특정 can 포트의 콜백 함수 추가
    def add_callback(self, channel, callback):
        if channel in self._callbacks:
            self._callbacks[channel].append(callback)
        else:
            print(f"Channel {channel} not found.")

# EngineTotalHoursOfOperation, EngineTotalIdleHours CAN 데이터를 수신하기 위한 CAN 데이터 전송 (60초 주기)
# can.Message(arbitration_id = 0x18EA0021, data = [229, 254, 00, 00, 00, 00, 00, 00], is_extended_id=True)
# can.Message(arbitration_id = 0x18EA0021, data = [220, 254, 00, 00, 00, 00, 00, 00], is_extended_id=True)
    def fake_data(self):
        bus = can.interface.Bus(channel='can1', bustype='socketcan', bitrate=250000)
        total_operation_msg  = can.Message(arbitration_id = 0x18EA0021, data = [229, 254, 00, 00, 00, 00, 00, 00], is_extended_id=True)
        total_idle_msg  = can.Message(arbitration_id = 0x18EA0021, data = [220, 254, 00, 00, 00, 00, 00, 00], is_extended_id=True)

        def inner_function():
            while True:
                bus.send(total_operation_msg)
                time.sleep(1)
                bus.send(total_idle_msg)
                time.sleep(60)

        th = threading.Thread(target=inner_function)
        th.daemon = True
        th.start()

# can 데이터 수신 스레드, can 데이터 파싱 & 콜백함수 실행 스레드 생성 및 실행
    def start_all(self):
        self.is_running = True
        self.__receiver_threads = {} # 각 can 포트 별로 can 데이터 수신 스레드를 저장하는 딕셔너리
        self.__processor_threads = {} # 각 can 포트 별로 can 데이터 파싱 & 콜백함수 실행 스레드를 저장하는 딕셔너리
        for channel, bitrate in zip(self._channels, self._bitrates):
            self._receivers[channel] = can.interface.Bus(channel=channel, bustype=self._bustype, bitrate=bitrate) # 특정 can 포트를 통해서 can bus 에 접속할 수 있는 객체 생성
            self.__receiver_threads[channel] = threading.Thread(target=self._receive_messages, args=(channel,)) # 특정 can 포트로 들어오는 can 데이터를 수신하는 스레드 생성
            self.__receiver_threads[channel].start()
            self.__processor_threads[channel] = threading.Thread(target=self.process_data, args=(channel,)) # 특정 can 포트의 메시지 큐로부터 can 데이터 파싱 및 콜백 함수 실행 스레드 생성
            self.__processor_threads[channel].daemon = True
            self.__processor_threads[channel].start()

# 특정 can 포트의 can bus 로부터 can 데이터를 수신하여 메시지 큐에 저장
    def _receive_messages(self, channel):
        bus = self._receivers[channel]
        buffer = []
        while self.is_running:
            message = bus.recv(timeout=1.0) # 타임아웃 시 None 객체 반환
            if message is not None:
                if self._buffer_mode:
                    buffer.append(message)
                    # 버퍼모드 on 인 경우, 수신된 can 데이터 개수가 버퍼 사이즈보다 큰 경우에만 메시지 큐에 저장함
                    # can 데이터 개수가 버퍼 사이즈보다 작다면 메시지 큐에 저장하지 않음
                    if len(buffer) >= self._buffer_size:
                        self._add_to_queue(channel, buffer.copy())
                        buffer.clear()
                else:
                    self._add_to_queue(channel, message)
        if self._buffer_mode and buffer:
            self._add_to_queue(channel, buffer)
        # print(f"Stopped receiving messages on {channel}.")

# 특정 can 포트의 메시지 큐에 can 데이터 리스트 추가
# 메시지 큐의 각 원소는 can 데이터 리스트임
    def _add_to_queue(self, channel, messages):
        # 메시지 큐 원소 개수가 _max_queue_size 보다 크다면 이전 원소들은 제거
        if self._msg_queues[channel].qsize() >= self._max_queue_size:
            while self._msg_queues[channel].qsize() >= self._max_queue_size:
                self._msg_queues[channel].get()  # 오래된 메시지 제거
        self._msg_queues[channel].put(messages)

# can 데이터 수신 스레드, can 데이터 파싱 & 콜백함수 실행 스레드 종료
    def stop_all(self):
        self.is_running = False
        for channel, thread in self.__receiver_threads.items():
            thread.join()
        for channel, thread in self.__processor_threads.items():
            thread.join()

# 특정 can 포트의 메시지 큐로부터 can 데이터를 파싱하여 `_status_message` 필드 업데이트 & 콜백 함수 실행
    def process_data(self, channel):
        msg_queue = self._msg_queues[channel] # 특정 can 포트의 메시지 큐 반환
        while self.is_running:
            try:
                messages = msg_queue.get(timeout=1.0) # 메시지 큐로부터 can 데이터 리스트 반환
                if channel == 'can1' and not self._is_parsing: # can2 포트에 대해서만 can 데이터 파싱 진행
                    self._can_data_parser(messages)

                self.handle_message(channel, messages) # 특정 can 포트의 콜백 함수 실행
            except queue.Empty:
                continue

# 특정 can 포트의 콜백 함수에 can 데이터 리스트를 넘겨주고 실행
    def handle_message(self, channel, messages):
        for callback in self._callbacks[channel]:
            callback(channel, messages)

# `_status_message` 필드의 값을 json 형태의 문자열로 반환
    def get_status_message(self):
        return self._status_message.get_json_properties_data()

# can 데이터 리스트로부터 `KEY` 구조체 필드에 해당하는 can 데이터만 파싱하여 `_status_message` 필드 업데이트
    def _can_data_parser(self, data):
        if self._is_parsing:
            return  
        
        self._is_parsing = True

        dbc_list = PyCanTools._dbc_list
        frame_ids_in_dbc = PyCanTools._frame_ids_in_dbc
    
        try:
            if dbc_list is not None and frame_ids_in_dbc is not None:
                status = {}
                for msgs in data: # can 리스트에 있는 각각의 can 데이터에 대해 파싱 진행
                    arbitration_id = msgs.arbitration_id
                    if arbitration_id in frame_ids_in_dbc: # 수신된 can id 가 dbc 파일에 있는지 체크
                        # dbc 파일로부터 특정 can id 의 데이터를 디코드하여 {'항목명': value} 형태의 딕셔너리로 저장
                        dic = dbc_list.decode_message(arbitration_id, msgs.data)
                        # 위에서 디코드한 항목명이 `KEY` 구조체의 필드와 겹치는 경우 해당 항목명 반환 (필터링)
                        commonkeys = set(dic).intersection(self.KEY)
                        # 위에서 필터링한 항목명에 대해 {`항목명`: value} 형태의 can 데이터 딕셔너리로 저장
                        status.update({key: dic[key] for key in commonkeys})
                self._parse_for_mqtt(status)
        except Exception as e:
            print('-----------------------')
            print(e)
            print('-----------------------')
        finally:
            self._is_parsing = False

# can 데이터 딕셔너리를 인자로 받고, 해당 데이터의 `항목명` 에 따라 `_status_message` 필드 업데이트
    def _parse_for_mqtt(self, dic):
        for key in dic.keys():
            if key == ENGINE_SPEED or key == FF1E_ENGINE_SPEED:
                self._engine_speed_avg_filter.moving_average(dic[key])
                speed = int(round(self._engine_speed_avg_filter.get_old_average(), 1))
                self._status_message.engine_speed = speed
                self._status_message.machine_status = "Engine ON" if speed>=800 else "Engine OFF"
                self._status_message.work_status = "work" if speed>=1200 else "idle"
            elif key == FUEL_LEVEL or key == FFD8_FUEL_LEVEL or key == FF45_GAUGE_DATA_FUEL_LEVEL or key == FUEL_LEVEL1 or key == FUEL_LEVEL2:
                self._status_message.fuel_level = int(dic[key])
            elif key == HYDRAULIC_OIL_TEMPERATURE:
                self._status_message.hydraulic_oil_temp = float(dic[key])
            elif key == ENGINE_COOLANT_TEMPERATURE or key == FF45_GAUGE_DATA_COOLANT_TEMP or key == FFD8_COOLANT_TEMP:
                self._status_message.coolant_temp = float(dic[key])
            elif key == ENGINE_FUEL_RATE:
                self._status_message.engine_fuel_rate = float(dic[key])
            elif key == FFDA_COOLANT_LEVEL or key == ENGINE_COOLANT_LEVEL1:
                self._status_message.coolant_level = int(dic[key])
            elif key == ENGINE_TOTAL_HOURS_OF_OPERATION:
                self._status_message.engine_total_hours_of_operation = dic[key]
            elif key == ENGINE_TOTAL_FUEL_USED or key == FF21_ENGINE_TOTAL_FUEL_USED:
                self._status_message.engine_total_fuel_used = dic[key]