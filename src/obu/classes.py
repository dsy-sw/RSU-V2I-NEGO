import struct
from struct import pack, unpack
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json

from abc import ABCMeta, abstractmethod

from config.contant import *
# from ..util.tools import Counter

    

@dataclass_json
@dataclass
class _MessageHeader:  # for send
    magic: int = 0xf1f1  # 2bytes
    msg_type: int = 0  # 1byte
    crc16: int = 0  # 2bytes
    packet_len: int = 0  # 2bytes
    
    def __post_init__(self, data: bytes = None):
        self.fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER
        self.header_fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER
        self.data_fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER
        self.data_list = self.__match_args__
        self.header_list = _MessageHeader.__match_args__
        self.scaling_list = {'lat':1/10**7,
                     'lon':1/10**7,
                     'elevation':0.1,
                     'transmission_and_speed':0.02*3.6,
                     'heading':0.0125,
                     'width':0.1,
                     'length':0.1,
        }
    def unpack_header(self, packet: bytes, _fmt: str = None) -> bool:
        if _fmt is None:
            _fmt = self.header_fmt
        self.magic, self.msg_type, self.crc16, self.packet_len = unpack(_fmt, packet[:7])
        return True

    def get_msg_type(self, hdata=None, _fmt=None):
        if hdata is None:
            return self.msg_type

        if _fmt is None:
            _fmt = self.header_fmt
        magic, msg_type, crc16, packet_len = unpack(_fmt, hdata[:7])
        return msg_type

    
    def pack_header(self, header_fmt: str = None) -> bytes:
        data_list = []
        if header_fmt is None:
            header_fmt = self.header_fmt
        for key in self.header_list:
            value = self.__getattribute__(key)
            data_list.append(value)
        return pack(header_fmt,*data_list)
    
    
    def pack_data(self, _fmt = None):
        if _fmt is None:
            _fmt = self.fmt
        _data_list = []
        for key in self.data_list:
            value = self.__getattribute__(key)
            if key in self.scaling_list:
                value = int(value / self.scaling_list[key])
            _data_list.append(value)

        # checksum
        # if len(_data_list) != (len(self.data_list) - len(self.header_list)):
        #     print(f"{_data_list = }")
        #     raise ValueError
        # try:
        #     packed_data = pack(_fmt, *_data_list)
        # except struct.error:
        #     packed_data = b''
        # packed_header = self.pack_header()

        packed_data = pack(_fmt, *_data_list)
            
        return packed_data
        
    def unpack_data(self, data, _fmt:str = None):
        if _fmt is None:
            _fmt = self.fmt
        unpacked_data = unpack(_fmt, data)

        if len(self.data_list) != len(unpacked_data):
            raise ValueError
        
        _scaling_list = self.scaling_list
        for name, value in zip(self.data_list, unpacked_data):
            if name in _scaling_list:
                value = value * _scaling_list[name]
            self.__setattr__(name,value)

        return True
    
@dataclass_json  # 타입 정의된 데이터만 dict, json으로 변환됨
@dataclass
class Message:  # for receive
    raw_packet: bytes
    data_field = None
    
    def __post_init__(self):
        if self.unpack_header(self.raw_packet):
            pass
        
    def unpack_header(self, packet: bytes, _fmt: str = DataFormat.BYTE_ORDER+DataFormat.HEADER) -> bool:
        self.magic, self.msg_type, self.crc16, self.packet_len = unpack(_fmt, packet[:7])
        self.data_field = 0
        return True

@dataclass
class BsmData(_MessageHeader):
    msg_type: int = BSM.msg_type
    packet_len: int = BSM.packet_len
    msg_count: int = 0  # 1byte uint / 0...127
    tmp_id: int = 0  # 4bytes uint 
    dsecond: int = 0  # 2bytes uint / unit: miliseconds
    lat: int = 0  # 4bytes int / unit: microdegrees/10
    lon: int = 0  # 4bytes int / unit: microdegrees/10
    elevation: int = 0  # 2bytes uint / WGS84 / -4096 ~ 61439 / unit: 10cm  !question
    semi_major: int = 0  # 1byte uint
    semi_minor: int = 0  # 1byte uint
    orientation: int = 0  # 2bytes uint
    transmission_and_speed: int = 0  # 2bytes uint / 0...11 bit * 0.02
    heading: int = 0  # 2bytes uint / unit of 0.0125 degrees / 0 ~ 359.9875
    steering_wheel_angle: int = 0  # 1byte uint
    accel_long: int = 0  # 2bytes int
    accel_lat: int = 0  # 2bytes int
    accel_vert: int = 0  # 1byte uint
    yaw_rate: int = 0  # 2bytes int
    brake_system_status: int = 0  # 2bytes uint
    width: int = 0  # 2bytes uint / unit: cm
    length: int = 0  # 2bytes uint / unit: cm
    l2id: int = 0  # 4bytes uint

    
    def __init__(self, data: bytes = None):
        super().__post_init__()
        self.fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER+DataFormat.BSM
        self.data_fmt =  DataFormat.BYTE_ORDER+DataFormat.BSM
        self.data_list = self.__match_args__

        # define header
        # self.msg_type = BSM.msg_type
        # self.packet_len = BSM.packet_len
    
        if data is not None:
            self.unpack_data(data, self.fmt)

    def pack_data(self, data_fmt = None):
        if data_fmt is None:
            data_fmt = self.data_fmt
        _data_list = []

        for key in self.data_list:
            if key in self.header_list:
                continue
            value = self.__getattribute__(key)
            if key in self.scaling_list:
                value = int(value / self.scaling_list[key])
            _data_list.append(value)
        self.msg_count += 1

        # checksum
        if len(_data_list) != (len(self.data_list) - len(self.header_list)):
            raise ValueError

        packed_data = pack(data_fmt, *_data_list)
        packed_header = self.pack_header()
        return packed_header+packed_data

@dataclass
class BsmLightData(_MessageHeader):
    msg_count: int = 0  # 4bytes uint / 0...127
    tmp_id: int = 0  # 4bytes uint 
    dsecond: int = 0  # 2bytes uint / unit: miliseconds
    lat: int = 0  # 4bytes int / unit: microdegrees/10
    lon: int = 0  # 4bytes int / unit: microdegrees/10
    elevation: int = 0  # 2bytes int / WGS84 / -4096 ~ 61439 / unit: 10cm
    semi_major: int = 0  # 1byte uint
    semi_minor: int = 0  # 1byte uint
    orientation: int = 0  # 2bytes uint
    transmission_and_speed: int = 0  # 2bytes uint / 0...11 bit * 0.02
    heading: int = 0  # 2bytes uint / unit of 0.0125 degrees / 0 ~ 359.9875
    steering_wheel_angle: int = 0  # 1byte uint
    accel_long: int = 0  # 2bytes int
    accel_lat: int = 0  # 2bytes int
    accel_vert: int = 0  # 1byte uint
    yaw_rate: int = 0  # 2bytes int
    brake_system_status: int = 0  # 2bytes uint
    width: int = 0  # 2bytes uint / unit: cm
    length: int = 0  # 2bytes uint / unit: cm
    l2id: int = 0  # 4bytes uint
    light: int = 0  # 2bytes uint
    
    
    def __init__(self, data: bytes = None):
        super().__post_init__()
        self.fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER+DataFormat.BSM
        self.data_fmt =  DataFormat.BYTE_ORDER+DataFormat.BSM
        self.data_list = BsmData.__match_args__
    
    def pack_data(self, data_fmt = None):
        if data_fmt is None:
            data_fmt = self.data_fmt
        _data_list = []

        for key in self.data_list:
            if key in self.header_list:
                continue
            value = self.__getattribute__(key)
            if key in self.scaling_list:
                value = int(value / self.scaling_list[key])
            _data_list.append(value)
        self.msg_count += 1

        # checksum
        if len(_data_list) != (len(self.data_list) - len(self.header_list)):
            raise ValueError

        packed_data = pack(data_fmt, *_data_list)
        packed_header = self.pack_header()
        return packed_header+packed_data


@dataclass
class DmmData(_MessageHeader):
    sender: int = 0  # 4bytes uint
    receiver: int = 0xffffffff  # 4bytes uint
    maneuver_type: int = 0  # 2bytes uint
    remain_distance: int = 0  # 1byte uint
    
    def __init__(self, l2id: int, maneuver: int = 0, dist: int = 0):
        self.msg_type = DMM.msg_type
        self.packet_len = DMM.packet_len
        self.sender = l2id
        self.maneuver_type = maneuver
        self.remain_distance = dist

    def unpack_data(self, data, packet_len = None, _fmt = DataFormat.DMM):
        if len(data) != packet_len:
            raise ValueError
        

@dataclass
class DnmRequestData(_MessageHeader):
    sender: int = 0  # 4bytes uint
    receiver: int = 0  # 4bytes uint
    remain_distance: int = 0  # 1byte uint

    def __init__(self, l2id: int):
        self.msg_type = DMM.msg_type
        self.packet_len = DMM.packet_len



@dataclass
class DnmResponseData(_MessageHeader):
    msg_type: int = DNM_REP.msg_type
    packet_len: int = DNM_REP.packet_len
    sender: int = 0  # 4bytes uint
    receiver: int = 0  # 4bytes uint
    agreement_flag: int = 0  # 1byte uint / 0: disagreement 1: agreement

    def __init__(self, l2id: int, receiver: int, agreement_flag: int = 0):
        super().__post_init__()
        self.sender = l2id
        self.receiver = receiver
        self.agreement_flag = agreement_flag
        self.fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER+DataFormat.DNM_RESPONSE
        

@dataclass
class DnmDoneData(_MessageHeader):
    sender: int = 0  # 4bytes uint
    receiver: int = 0  # 4bytes uint
    nego_driving_done: int = 0  # 1byte uint


        

@dataclass
class EdmData(_MessageHeader):
    sender: int = 0  # 4bytes uint
    maneuver_type: int = 0  # 2bytes uint
    remain_distance: int = 0  # 1byte uint



@dataclass
class L2idRequestData(_MessageHeader):
    msg_type: int = L2ID.msg_type

    def __post_init__(self):
        super().__post_init__()
        self.data_fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER+DataFormat.L2ID_REQUEST

    def pack_data(self, data_fmt=None):
        return self.pack_header()
        

@dataclass
class L2idResponseData(_MessageHeader):
    l2id: int = 0  # 4bytes uint

@dataclass
class CimData(_MessageHeader):
    msg_type: int = CIM.msg_type
    packet_len: int = CIM.packet_len
    sender: int = 0
    vehicle_type: int = 10

    def __init__(self):
        super().__post_init__()
        self.fmt = DataFormat.BYTE_ORDER+DataFormat.HEADER+DataFormat.CIM
        self.data_list = CimData.__match_args__



if __name__ == "__main__":
    test_bytes = b'\x00\x02\x02\x00\x02\x00\x02\x00\x01\x01\x00\x01\x00\x01'
    _test_data = bytes.fromhex('F1F1010000002B00000000010000165E581A4B776578000000000000000000000000000000000000000000C801F400000000')
    _test_data = bytes.fromhex('F1F1010000000300000000000000FFFFFF')
    # print(f"{_test_data =}")
    # test_data = _test_data.to_bytes()
    # a = Message(test_bytes)
    b = L2idRequestData()
    b.pack_data()
    b.pack_data()
    b.pack_data()
    print(b)
    

'''
1. data 관리를 어찌 할 것인가,,,
    - 데이터를 msg header의 인자로 넣고, 관리 or 한 꺼번에 관리
    - 받는 데이터는 매번 생성?

2. 차량<->미들웨어의 데이터 관리를 어찌,,,
    - 데이터와 주기가 매번 다름
'''