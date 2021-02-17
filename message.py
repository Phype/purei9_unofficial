import struct

class BinaryMessage:
    
    MAGIC = 30194250
    
    MAJOR_HDRONLY   = 1
    MAJOR_TEXT      = 2
    MAJOR_INTMAP    = 3
    MAJOR_BLOB      = 4
    MAJOR_BLOBMAP   = 5
    MAJOR_STRINGMAP = 6
    
    def __init__(self):
        self.magic = BinaryMessage.MAGIC
        self.major = 1
        self.minor = 0
        self.user1 = 0
        self.user2 = 0
        self.payload = b""
        
        self.parsed = None
    
    def to_wire(self):
        return struct.pack("<IIIIII", self.magic, self.major, self.minor, self.user1, self.user2, len(self.payload)) + self.payload
    
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
        
        if self.major == BinaryMessage.MAJOR_STRINGMAP:
            
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
        
        return self
    
    def __str__(self):
        return "BinaryMessage " + str({
            "magic": self.magic,
            "major": self.major,
            "minor": self.minor,
            "user1": self.user1,
            "user2": self.user2,
            "payload": self.payload,
            "parsed": self.parsed
        })
