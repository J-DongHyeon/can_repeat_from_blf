import threading
from can_library.utils import Utils

class SystemInformation:
    __instance = None
    
    @staticmethod
    def getInstance():
        if SystemInformation.__instance == None:
            SystemInformation()
        return SystemInformation.__instance

    def __init__(self):
        if SystemInformation.__instance != None:
            raise Exception("systemInformation is singleton.")
        else:
            SystemInformation.__instance = self
        self.data = {}
        self.lock = threading.RLock()

    def set_data(self, key, value)-> dict:
        self.data[key] = value

    def getLoggingDataByClass(self, key)-> dict:
        return Utils.json_dump(self.data.get(key, None))
    
    def getAllLoggingData(self)-> dict:
        return Utils.json_dump([dict(self.data)])

def systemInformation_access(cls):
    def wrapper(*args, **kwargs):
        system_information = SystemInformation.getInstance()
        setattr(cls, "set_data", system_information.set_data)
        setattr(cls, "get_data", system_information.getLoggingDataByClass)
        return cls(*args, **kwargs)
    return wrapper