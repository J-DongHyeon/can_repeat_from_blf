import os
import sys
import subprocess
import time
import threading
import datetime

class TmsGps(object):
    __bus = None

    def __init__(self):
        self.nmea_dic = dict()
        self.__lock_readNMEA = threading.Lock()
        self.__lock_nmea_dic = threading.Lock()
        host_name = os.popen('hostname').read()
        self.__hostname  = host_name.replace('\n', '')
        self.__addr = 0x42
        self.__connect()
        self.__th_activeRead = threading.Thread(target=self.__th_put_nmea_dic, args=())
        self.__th_activeRead.daemon = True
        self.__th_activeRead.start()

    def set_time(self, seconds = 0) -> dict:
        if sys.version_info.major == 2:
            version_check = self.nmea_dic.has_key('RMC')
        elif sys.version_info.major == 3:
            version_check = 'RMC' in self.nmea_dic

        if version_check:
            time_tuple = (self.nmea_dic['RMC'].datestamp.year,
                          self.nmea_dic['RMC'].datestamp.month,
                          self.nmea_dic['RMC'].datestamp.day,
                          self.nmea_dic['RMC'].timestamp.hour,
                          self.nmea_dic['RMC'].timestamp.minute,
                          self.nmea_dic['RMC'].timestamp.second,
                          self.nmea_dic['RMC'].timestamp.microsecond)
            timestamp = int(time.mktime(datetime.datetime(*time_tuple[:6]).timetuple())) + seconds + (time_tuple[6] / 1000000.0)
            localtime = time.localtime(timestamp)
            time_tuple = (localtime.tm_year, localtime.tm_mon, localtime.tm_mday, localtime.tm_hour, localtime.tm_min, localtime.tm_sec, time_tuple[6])
            if self.__hostname == 'tms':
                self.__linux_set_time(time_tuple)
                os.system('hwclock -w')
                print('setTime Success, Current Date is: {}'.format(subprocess.check_output('date')))
                return True
        else:
            return False
        
    def __connect(self):
        from smbus2 import SMBus
        try:
            if self.__hostname == 'tms':
                TmsGps.__bus = SMBus(1)
            else:
                TmsGps.__bus = None
        except Exception as e:
            print(e)

    def __iter__(self):
        try:
            while True:
                with self.__lock_readNMEA:
                    msg = self.__read_nmea_from_bus()
                if msg != None:
                    yield msg
                time.sleep(0.1)
        except Exception as e:
            print('Exit')
            pass

    def __th_put_nmea_dic(self):
        while True:
            with self.__lock_readNMEA:
                msg = self.__read_nmea_from_bus()
            if msg is not None:
                with self.__lock_nmea_dic:
                    self.nmea_dic[msg.sentence_type] = msg
                
            time.sleep(0.1)

    def get_nmea(self, type:dict) -> dict:
        with self.__lock_nmea_dic:
            if sys.version_info.major == 2:
                if self.nmea_dic.has_key(type):
                    return self.nmea_dic[type]
                else:
                    return None
            elif sys.version_info.major == 3:
                if type in self.nmea_dic:
                    return self.nmea_dic[type]
                else:
                    return None

    def __read_nmea_from_bus(self):
        import pynmea2
        response = []
        try:
            if self.__hostname == 'tms':
                while True:
                    c = TmsGps.__bus.read_byte(self.__addr)
                    if c == 0xFF:
                        return None
                    elif c == 10:
                        break
                    else:
                        response.append(c)
                nmea = ''.join(chr(c) for c in response)
                if "*" not in nmea:
                    return None
                else:
                    return pynmea2.parse(nmea)
            else:
                time.sleep(3)
                return pynmea2.parse('$GPRMC,141114.999,A,3730.0264,N,12655.2351,E,15.51,202.12,101200,,*3C')

        except IOError:
            time.sleep(0.5)
            print('Bus reconnecting')
            self.__connect()
        except Exception as e:
            print(e)

    def __linux_set_time(self, time_tuple:tuple):
        import ctypes
        CLOCK_REALTIME = 0

        class timespec(ctypes.Structure):
            _fields_ = [('tv_sec', ctypes.c_long),
                        ('tv_nsec', ctypes.c_long)]
        librt = ctypes.CDLL(ctypes.util.find_library("rt"))
        ts = timespec()
        ts.tv_sec = int(time.mktime(datetime.datetime(*time_tuple[:6]).timetuple()))
        ts.tv_nsec = time_tuple[6] * 1000  # Millisecond to nanosecond
        librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))