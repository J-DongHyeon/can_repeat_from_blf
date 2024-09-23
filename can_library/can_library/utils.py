import re
import sys
import csv
import time
import json
import threading
import subprocess
import yaml

_platform = None

if sys.platform.startswith('win'):
    _platform = 'window'

elif sys.platform.startswith('linux'):
    _platform = 'linux'

class Utils(object):
    ip                   = None
    __tms_gps            = None
    __linux_set_time     = None
    _ipv4_address        = None

    _is_thread_running   = False
    _network_status      = ''

    @classmethod
    def get_ipv4_address(cls):
        if cls._ipv4_address is None:
            if sys.platform == "win32":
                try:
                    result = subprocess.run(["powershell", "(Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' }).IPAddress"],
                                            capture_output=True, text=True, check=True)
                    ipv4_addresses = result.stdout.strip().split("\n")
                    if ipv4_addresses:
                        cls._ipv4_address = ipv4_addresses[0]
                except subprocess.CalledProcessError as e:
                    print("Error:", e)
            elif sys.platform == "linux":
                try:
                    interface = 'mlan0'
                    result = subprocess.check_output(['ifconfig', interface]).decode('utf-8')
                    match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', result)
                    if match:
                        cls._ipv4_address = match.group(1)
                    else:
                        cls._ipv4_address =  None
                except subprocess.CalledProcessError as e:
                    print("Error:", e)
            else:
                print("현재 사용 중인 운영 체제는 Windows 또는 Linux이 아닙니다.")
        return cls._ipv4_address

    @staticmethod
    def get_hwaddr(interface='mlan0'):
        try:
            result = subprocess.check_output(['ifconfig', interface]).decode('utf-8')

            match = re.search(r'HWaddr (\S+)', result)

            if match:
                mac_address = match.group(1)
                cleaned_mac_address = mac_address.replace(":", "")
                return cleaned_mac_address
            else:
                return None
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def time_stamp():
        time_stamp = time.time()
        return time_stamp

    @staticmethod
    def _convert_hashmap_to_dict(hashmap:dict):
        if isinstance(hashmap, dict):
            return hashmap
        keys_str = str(hashmap.keySet())
        values_str = str(hashmap.values())

        keys_str = keys_str[1:-1]
        values_str = values_str[1:-1]

        keys_list = [item.strip() for item in keys_str.split(',')]
        values_list = [item.strip() for item in values_str.split(',')]
        result_dict = dict(zip(keys_list, values_list))
        return result_dict

    @classmethod
    def connection_status(cls):
        if not cls._is_thread_running:
            cls.__connectionStatus()
        return cls._network_status

    @classmethod
    def __connectionStatus(cls):
        cls._is_thread_running = True
        def inner_function():
            assert cls.ip is not None and cls.ip, "Empty or None value for Utils.ip is not allowed."
            while cls._is_thread_running:
                time_value = -1
                if sys.version_info.major == 2:
                    if _platform == 'window':
                        try:
                            result = subprocess.run(['ping', '-n', '1', cls.ip], capture_output=True, text=True, timeout=5)
                            time_index = result.stdout.find("시간=")

                            if time_index != -1:
                                time_value = result.stdout[time_index + len("시 간="):]
                                time_value = time_value.split()[0]
                                time_value = time_value[:-2]
                        except subprocess.CalledProcessError:
                            time_value = -1
                    elif _platform == 'linux':
                        try:
                            c = subprocess.check_output(['/bin/ping', '-c', '1', cls.ip])
                            time_value = c.split("/")[-2]
                        except subprocess.CalledProcessError:
                            time_value = -1

                elif sys.version_info.major == 3:
                    if _platform == 'window':
                        try:
                            result = subprocess.run(['ping', '-n', '1', cls.ip], capture_output=True, text=True, timeout=5)
                            time_index = result.stdout.find("시간=")

                            if time_index != -1:
                                time_value = result.stdout[time_index + len("시 간="):]
                                time_value = time_value.split()[0]
                                time_value = time_value[:-2]
                        except subprocess.CalledProcessError:
                            time_value = -1
                    elif _platform == 'linux':
                        try:
                            c = subprocess.check_output(['/bin/ping', '-c', '1', cls.ip]).decode()
                            time_value = c.split("/")[-2]
                        except subprocess.CalledProcessError:
                            time_value = -1

                if 100 > float(time_value) > 20:
                    cls._network_status = "NORMAL"
                elif 0 < float(time_value) <= 20:
                    cls._network_status = "GOOD"
                else:
                    cls._network_status = "BAD"
        t = threading.Thread(target=inner_function)
        t.daemon = True
        t.start()

    @staticmethod
    def __read_config(fn, config=None):
        try:
            ext = fn[-3:].lower()
            obj = {}
            if sys.version_info.major == 2:
                if ext == "json":
                    with open(fn,'r') as f:
                        obj = json.load(f)
                elif ext == "yml" or "yaml":
                    with open(fn, 'rt') as f:
                        obj = yaml.load(f)

                if(config != None):
                    for key in config.keys():
                        if(key in obj):
                            config[key] = obj[key]
                return obj
            elif sys.version_info.major == 3:
                if ext == "json":
                    with open(fn,'r') as f:
                        obj = json.load(f)
                elif ext == "yml" or "yaml":
                    with open(fn, 'rt') as f:
                        obj = yaml.full_load(f)

                if(config != None):
                    for key in config.keys():
                        if(key in obj):
                            config[key] = obj[key]
                return obj

        except Exception as e:
            print("error while reading configuration: " + str(e))

    @staticmethod
    def json_load(jsonData:json):
        return json.loads(jsonData)

# json.dumps 메소드를 이용하여 파이썬 컨테이너를 JSON 형태의 문자열로 반환
    @staticmethod
    def json_dump(dictData:dict):
        return json.dumps(dictData)

    @staticmethod
    def get_machine_id_from_ifconfig(csv_file_path):
        try:
            ifconfig_str  = subprocess.run(['ifconfig'], capture_output=True, text=True)
            ifconfig = ifconfig_str.stdout
            match = re.search(r"mlan0\s+Link encap:Ethernet\s+HWaddr\s+([0-9A-Fa-f:]+)", ifconfig)
            if match:
                mac_address = match.group(1).upper()
            else:
                print("HWaddr not found in the provided network information.")
                return None
            
            with open(csv_file_path, 'r') as f:
                reader = csv.reader(f)
                for line in reader:
                    if mac_address == line[1]:
                        return line[0]
        except FileNotFoundError:
            print(f"Error: The file {csv_file_path} does not exist.")
            return None
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None

        return None

# 특정 파일의 경로를 붙여서 반환
    @staticmethod
    def files_abspath(file_name:str):
        # return  '/home/root/can-library/files/'+ file_name
        return  '/ws/src/can_library/can_library/files/'+ file_name


class MovingAverageFilter:
    def __init__(self, buffer_size=1):
        self._old_average = 0.0
        self._buffer_size = buffer_size if buffer_size > 0 else 1

    def set_old_average(self, old_average):
        self._old_average = old_average

    def set_buffer_size(self, buffer_size):
        self._buffer_size = buffer_size if buffer_size > 0 else 1

    def get_old_average(self):
        return self._old_average

    def get_buffer_size(self):
        return self._buffer_size

    def moving_average(self, new_data):
        """
        Avg = (n-1)/n * old_Avg + new_data/n
        If buffer_size is large, the output value will have more latency.
        """
        self._old_average = ((self._buffer_size - 1) / self._buffer_size) * self._old_average + new_data / self._buffer_size
        return self._old_average