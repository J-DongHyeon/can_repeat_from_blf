import cantools

from can_library.message_formatter import PeakSystemInterface, MessageFormatter
from can_library.utils import Utils

class PyCanTools(object):

# 클래스 멤버 필드이며, 프로세스 실행과 동시에 생성
# 여러 객체에서 write & read 함
# _frame_ids_in_dbc: dbc 파일의 can id 리스트
# _filtered_frame_ids: dbc 파일에서 필터링하고자 하는 frame id
# _dbc_list: dbc 파일에서 필요한 데이터만 파싱된 파이썬 객체
    msg_field            = None
    _frame_ids_in_dbc    = None
    _filtered_frame_ids  = None
    _dbc_list            = []

# param 으로 dbc 파일의 정보가 들어감
# dbcframeIds: dbc 파일에서 필터링하고자 하는 frame id
# dbcPath: dbc 파일의 경로
# 위의 4가지 클래스 멤버 필드가 초기화됨
    @classmethod
    def _update_dbc_interface(cls, param=None)-> None:
        if param is not None :
            json_to_dict = Utils.json_load(param)
            frame_ids    = json_to_dict.get('dbcframeIds')
            dbc_path     = json_to_dict.get('dbcPath')
            msg_field    = json_to_dict.get('canIdentifiers')
            PyCanTools._dbc_filter_frame_ids(frame_ids)
            PyCanTools._load_dbc(dbc_path)
            PyCanTools.msg_field = msg_field

    @classmethod
    def _get_current_dbc_data(cls)-> dict:
        dbc_list = PyCanTools._dbc_list
        dbc_to_dict = []
        for dbc_message in dbc_list.messages:
            dbc_to_dict.append(cls.__dbc_message_to_dict(dbc_message))

        return Utils.json_dump(dbc_to_dict)

    @classmethod
    def _encode_signal_data(cls, message_name, signal_name, data)-> object:
        dbc_list = PyCanTools._dbc_list

        message = dbc_list.get_message_by_name(message_name)
        
        if message:
            signal_names = [signal.name for signal in message.signals]
            signal_values = {name: data if name == signal_name else 0 for name in signal_names}
            try:
                encoded_data = message.encode(signal_values)
                peak_msg = PeakSystemInterface(can_id=hex(message.frame_id), can_data=encoded_data)
                return peak_msg.get_binary()
            except Exception as e:
                print(f"Error Encode {e}")
                return None
        else:
            print(f"Message '{message_name}' not found in DBC list.")

    @classmethod
    def _is_dbc_defined(cls)-> bool:
        if cls._dbc_list:
            return True
        else:
            return False
        
    @classmethod
    def _can_tools_function_names(cls, list_index:int)-> list:
        function_names = ['json_to_dict_extractor', 
                          'bytearray_convert_to_dict_data', 
                          'bytearray_convert_to_parser_data']
        return function_names[list_index]
    
    @classmethod
    def _get_dbc_list(cls)-> dict:
        return cls._dbc_list
        
    @classmethod
    def _dbc_filter_frame_ids(cls, frame_ids:str)-> None:
        if isinstance(frame_ids, str):
            hex_value = "0x" + frame_ids.upper()  
            int_value = int(hex_value, 16)
            cls._filtered_frame_ids = [int_value]
        elif isinstance(frame_ids, list):
            cls._filtered_frame_ids = [int("0x" + val.upper(), 16) for val in frame_ids]

# dbc 파일의 경로를 인자로 받고, dbc 파일 중 필요한 데이터만 파싱하여 파이썬 객체로 생성
    @classmethod
    def _load_dbc(cls, dbc_content: str) -> list:
        try:
            ext = dbc_content[-3:].lower()
            if(ext == "dbc" or ext == "DBC"):
                # dbc 파일 중 필요한 데이터만 파싱하여 파이썬 객체로 생성
                local_dbc_list = cantools.database.load_file(dbc_content)
            else:  
                local_dbc_list = cantools.database.load_string(dbc_content)

            cls._frame_ids_in_dbc = []

            if cls._filtered_frame_ids is None:
                cls._frame_ids_in_dbc = [msg.frame_id for msg in local_dbc_list.messages]
                cls._dbc_list = local_dbc_list
            else:
                filtered_messages = [msg for msg in local_dbc_list.messages if msg.frame_id in cls._filtered_frame_ids]
                cls._frame_ids_in_dbc = [msg.frame_id for msg in filtered_messages]
                cls._dbc_list = cantools.db.Database(messages=filtered_messages)

        except cantools.errors.Error as e:
            print(f"DBC를 로드하는 중 오류 발생: {e}")
            cls._dbc_list = None
            cls._frame_ids_in_dbc = []

        except Exception as e:
            print(f"로드 중 예상치 못한 오류 발생: {e}")
            cls._dbc_list = None
            cls._frame_ids_in_dbc = []

    @classmethod
    def _json_to_dict_extractor(cls, mqtt_msg):
        frame_id = int(mqtt_msg["id"], 16)
        data = bytes(int(byte, 16) for byte in mqtt_msg["dt"])
            
        if frame_id in cls._frame_ids_in_dbc:
            dic = cls._dbc_list.decode_message(frame_id, data)
            
            if isinstance(cls.msg_field, list):
                for field in cls.msg_field:
                    if field in dic:
                        yield {field: dic[field]}
            elif cls.msg_field is None or cls.msg_field in dic:
                yield  dic[cls.msg_field] if cls.msg_field else dic
        return None

    @classmethod
    def _bytearray_convert_to_dict_data(cls, message):
        peak_msg = PeakSystemInterface()
        peak_msg.byte_array_to_msg_format(message)
        binary_to_dict = peak_msg.trace_message()
        binary_to_dict['can_data'] = MessageFormatter.hex_str_to_list(binary_to_dict['can_data'])
        yield {"timestamp": binary_to_dict['timestamp'],
               "channel": binary_to_dict['channel'],
               "canId": binary_to_dict['can_id'],
               "canData": binary_to_dict['can_data']}

    @classmethod
    def _bytearray_convert_to_parser_data(cls, message):
        peak_msg = PeakSystemInterface()
        convert_msg = peak_msg.byte_array_to_msg_format(message)
        
        if convert_msg['can_id'] in cls._frame_ids_in_dbc:
            dic = cls._dbc_list.decode_message(convert_msg['can_id'], convert_msg['can_data'])
            
            if isinstance(cls.msg_field, list):
                for field in cls.msg_field:
                    if field in dic:
                        yield {field: dic[field]}
            elif cls.msg_field is None or cls.msg_field in dic:
                yield  dic[cls.msg_field] if cls.msg_field else dic
        return None
    
    @classmethod
    def _crawl_bytearray_can_messages_from_trc(cls, trc_file_path:str)-> object:
        '''
        message = {
            "tm": float(parts[1]),
            "id": parts[3],  
            # "ch": int(parts[0].strip(")")),
            "dt": parts[5:]  
        }
        '''
        ext = trc_file_path[-3:].lower()
        if(ext == "trc"):
            with open(trc_file_path, 'r') as trc_file:
                for line in trc_file:
                    parts = line.split()
                    if len(parts) >= 5 and parts[2] == "Rx":
                        try:
                            peak_msg = PeakSystemInterface(can_id    = parts[3], 
                                                           can_data  = parts[5:],
                                                           timestamp = float(parts[1]))
                            convert_to_peak_msg = peak_msg.get_binary()
                            yield convert_to_peak_msg
                        except Exception as e:
                            return None

    @classmethod
    def _decode_raw_can_data(cls, message)-> dict:
        frame_id = int(message.arbitration_id)
        dic = None
        if frame_id in cls._frame_ids_in_dbc:
            dic = cls._dbc_list.decode_message(frame_id, message.data)

        return dic 
    
    @classmethod
    def __dbc_message_to_dict(cls, message)-> None:
        return {
            'messageName': message.name,
            'hex'        : hex(message.frame_id),
            'children'   : [signal.name for signal in message.signals]
        }
    
    # MQTT msg
    # @classmethod 
    # def crawl_can_messages_from_trc(cls, trc_file_path:str):
    #     with open(trc_file_path, 'r') as trc_file:
    #         for line in trc_file:
    #             parts = line.split()
    #             if len(parts) >= 5 and parts[2] == "Rx":
    #                 try:
    #                     message = {
    #                         "tm": float(parts[1]),
    #                         "id": parts[3],  
    #                         "ch": int(parts[0].strip(")")),
    #                         "dt": parts[5:]  
    #                     }
    #                     print(message)
    #                     yield message
    #                 except can.CanError:
    #                     print("Error occurred while sending virtual CAN message.")
    #                     return None
    #                 except KeyboardInterrupt:
    #                     print("CAN reader terminated.")
    #                     return None
    #                 except Exception as e:
    #                     return None
                    