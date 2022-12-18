import struct

port_tcp = 3002
port_udp = 3000

class BinaryMessage:
    
    MAGIC = 30194250
    
    MAJOR_HDRONLY   = 1
    MAJOR_TEXT      = 2
    MAJOR_INTMAP    = 3
    MAJOR_BLOB      = 4
    MAJOR_BLOBMAP   = 5
    MAJOR_STRINGMAP = 6

    MSG_HELLO        = 3000
    MSG_LOGIN        = 3005
    MSG_PING         = 1000
    MSG_GET_ADDRESS_REQUEST = 1002
    MSG_GET_NETWORKS_LIST = 1003
    MSG_GET_ADDRESS_RESPONSE = 4001
    MSG_GETNAME      = 1011
    MSG_GETFIRMWARE  = 1010
    MSG_GETSETTINGS  = 1023
    MSG_STARTCLEAN   = 1014
    MSG_GETSTATUS    = 1012
    MSG_GET_BATTERY_STATUS_REQUEST = 1016 #  -984
    MSG_GET_CAPABILITIES_REQUEST = 1031
    
    MSG_GET_POWER_MODE_REQUEST = 1027
    MSG_SET_POWER_MODE_REQUEST = 1028
    MSG_SET_POWER_MODE_RESPONSE = 1029
    
    MSG_GET_MESSAGE_LIST_REQUEST = 1020
    SET_LOCAL_ROBOT_PASSWORD_REQUEST = 3004
    
    def __init__(self, major = 1, minor = 0, user1 = 0, user2 = 0, payload = b""):
        self.magic = BinaryMessage.MAGIC
        self.major = major
        self.minor = minor
        self.user1 = user1
        self.user2 = user2
        self.payload = payload
        self.parsed = None
    
    def to_wire(self):
        return struct.pack("<IIIIII", self.magic, self.major, self.minor, self.user1, self.user2, len(self.payload)) + self.payload
    
    @staticmethod
    def HeaderOnly(minor, user1 = 0, user2 = 0):
        return BinaryMessage(BinaryMessage.MAJOR_HDRONLY, minor, user1, user2)
    
    @staticmethod
    def Text(minor, parsed, user1 = 0, user2 = 0):
        return BinaryMessage(BinaryMessage.MAJOR_TEXT, minor, user1, user2, parsed.encode("utf-8"))
    
    @staticmethod
    def StringMap(minor, parsed, user1 = 0, user2 = 0):
        mymap = {"test": "123"}

        payload = b""

        for key, value in parsed.items():
            key = key.encode("utf-8")
            value = value.encode("utf-8")

            payload += struct.pack("<I", len(key))
            payload += key
            payload += struct.pack("<I", len(value))
            payload += value

        return BinaryMessage(BinaryMessage.MAJOR_STRINGMAP, minor, user1, user2, payload)

    ###
    
    @staticmethod
    def from_stream(stream):
        hdr = stream.read(24)
        
        if not(len(hdr) == 24):
            raise Exception("Read too short (" + str(len(hdr)) + ")")
        
        magic, major, minor, user1, user2, length = struct.unpack("<IIIIII", hdr)
        
        body = stream.read(length)
        
        if not(len(body) == length):
            raise Exception("Read too short (" + str(len(body)) + ")")
        
        return BinaryMessage.from_wire(hdr + body)
    
    @staticmethod
    def from_wire(packet):
        if len(packet) < 24:
            raise Exception("Packet too short")
        
        self = BinaryMessage()
        
        self.magic, self.major, self.minor, self.user1, self.user2, length = struct.unpack("<IIIIII", packet[:24])
        
        if not(self.magic == BinaryMessage.MAGIC):
            raise Exception("Magic mismatch")
        
        self.payload = packet[24:]
        
        if not(len(self.payload) == length):
            raise Exception("Packet length mismatch")
        
        ###########
        
        if self.major == BinaryMessage.MAJOR_HDRONLY:
            pass
        
        elif self.major == BinaryMessage.MAJOR_TEXT:
            self.parsed = self.payload.decode("utf-8")
            pass
        
        elif self.major == BinaryMessage.MAJOR_BLOB:
            self.parsed = self.payload
        
        elif self.major == BinaryMessage.MAJOR_BLOBMAP:
            
            data = self.payload
            obj  = {}
            
            while True:
                
                if len(data) == 0:
                    break
                
                if len(data) < 4:
                    raise Exception("Packet length mismatch")
                
                length  = struct.unpack("<I", data[:4])[0]
                key     = data[4:4+length]
                data    = data[4+length:]
                
                if len(data) < 4:
                    raise Exception("Packet length mismatch")
                
                length = struct.unpack("<I", data[:4])[0]
                value  = data[4:4+length]
                data   = data[4+length:]
                
                obj[key.decode("utf-8")] = value
        
            self.parsed = obj
        
        elif self.major == BinaryMessage.MAJOR_STRINGMAP:
            
            data = self.payload
            obj  = {}
            
            while True:
                
                if len(data) == 0:
                    break
                
                if len(data) < 4:
                    raise Exception("Packet length mismatch")
                
                length  = struct.unpack("<I", data[:4])[0]
                key     = data[4:4+length]
                data    = data[4+length:]
                
                if len(data) < 4:
                    raise Exception("Packet length mismatch")
                
                length = struct.unpack("<I", data[:4])[0]
                value  = data[4:4+length]
                data   = data[4+length:]
                
                obj[key.decode("utf-8")] = value.decode("utf-8")
        
            self.parsed = obj
            
        # print("Debug pkt = " + str(self))
        
        return self
    
    def __str__(self):
        return "BinaryMessage " + str(self.json())
    
    def json(self):
        return {
            "magic": self.magic,
            "major": self.major,
            "minor": self.minor,
            "user1": self.user1,
            "user2": self.user2,
            "payload": self.payload.decode("iso-8859-1", "ignore"),
            "parsed": self.parsed.decode("iso-8859-1", "ignore") if type(self.parsed) == bytes else self.parsed
        }
