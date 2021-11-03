import socket
import ssl
import struct
import json
import base64
import logging

from typing import List

from .message import BinaryMessage

from .common import AbstractRobot, RobotStates, BatteryStatus, PowerMode, capabilities2model, DustbinStates

logger = logging.getLogger(__name__)

class RobotClient(AbstractRobot):
    
    CLEAN_PLAY  = 1
    CLEAN_SPOT  = 2
    CLEAN_HOME  = 3
    CLEAN_PAUSE = 4 # Unused by App?
    CLEAN_STOP  = 5 # Unused by App?
    
    STATE_CLEANING            = 1
    STATE_PAUSED              = 2
    STATE_SPOTCLEAN           = 3
    STATE_PAUSEDSPOTCLEAN     = 4
    STATE_RETURN              = 5
    STATE_PAUSEDRETURN        = 6
    STATE_RETURNPITSTOP       = 7
    STATE_PAUSEDRETURNPITSTOP = 8
    
    def __init__(self, addr : str):
        self.port     = 3002
        self.addr     = addr
        self.robot_id = None
        self.stream   = None
        self.protocol_version = None
        
    ###
    
    def getmodel(self):
        capabilities = self.getcapabilities()["Capabilities"]
        return capabilities2model(capabilities)
    
    def getstatus(self) -> str:
        """Get the current state of the robot"""
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETSTATUS))
        return RobotStates(pkt.user1)
    
    def getdustbinstatus(self):
        return DustbinStates.unset
    
    def startclean(self) -> None:
        """Tell the Robot to start cleaning"""
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_PLAY))
        return True
    
    def spotclean(self) -> None:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_SPOT))
        return True
        
    def gohome(self) -> None:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_HOME))
        return True
        
    def pauseclean(self) -> None:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_PAUSE))
        return True
        
    def stopclean(self) -> None:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_STOP))
        return True
        
    def getid(self) -> str():
        """Get the robot's id"""
        return self.robot_id
    
    def getname(self) -> str:
        """Get the robot's name"""
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETNAME))
        return pkt.parsed
    
    def getfirmware(self) -> str:
        """Get robot's firmware version"""
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETFIRMWARE))
        return pkt.parsed["FirmwareVersion"]
    
    def getbattery(self) -> str:
        """Get the current robot battery status"""
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_BATTERY_STATUS_REQUEST))
        return BatteryStatus(pkt.user1)
    
    def isconnected(self) -> bool:
        return self.stream != None
    
    ###
    
    def getwifinetworks(self) -> List[str]:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_NETWORKS_LIST))
        networks = []
        for key in pkt.parsed:
            networks.append(pkt.parsed[key].decode("utf-8"))
        return networks
    
    def getcapabilities(self) -> dict:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_CAPABILITIES_REQUEST))
        return json.loads(pkt.parsed)
    
    def getsupportedpowermodes(self):
        
        capabilities = self.getcapabilities()["Capabilities"]
        if "PowerLevels" in capabilities:
            return [PowerMode.LOW, PowerMode.MEDIUM, PowerMode.HIGH]
        elif "EcoMode" in capabilities:
            return [PowerMode.MEDIUM, PowerMode.HIGH]
        else:
            return [PowerMode.MEDIUM]
    
    def getpowermode(self) -> PowerMode:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_POWER_MODE_REQUEST))
        return PowerMode(pkt.user1)
    
    def setpowermode(self, mode):
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_SET_POWER_MODE_REQUEST, user1=mode.value))
        return None
    
    def getsettings(self) -> dict:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETSETTINGS))
        data = json.loads(pkt.parsed)
        return data
    
    def getmessages(self) -> list:
        pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_MESSAGE_LIST_REQUEST))
        data = json.loads(pkt.parsed)
        return data["Messages"]
    
    def setlocalpw(self, pw):
        pkt = self.sendrecv(BinaryMessage.Text(BinaryMessage.SET_LOCAL_ROBOT_PASSWORD_REQUEST, pw))
        return
    
    ###
    
    def send(self, pkt : BinaryMessage): # minor, data=None, user1=0, user2=0):
        
        if type(pkt) != BinaryMessage:
            raise Exception("pkt must by of type BinaryMessage")
        
        logger.debug("send " + str(pkt))
        self.stream.write(pkt.to_wire())
        self.stream.flush()
        
    def recv(self) -> BinaryMessage:
        pkt = BinaryMessage.from_stream(self.stream)
        logger.debug("recv " + str(pkt))
        return pkt
    
    def sendrecv(self, pkt : BinaryMessage) -> BinaryMessage:
        self.send(pkt)
        return self.recv()
    
    def connect(self, localpw):
    
        # versions = [2019041001, 2016100701, 2016062801]
        success, other_version = self._connect(localpw, 2016100701)
        
        if not(success):
            logger.debug("Protocol version mismatch, retrying with version " + str(other_version))
            success, other_version = self._connect(localpw, other_version)
            
        if success:
            return True
        else:
            raise Exception("Protocol version mismatch")
    
    def _connect(self, localpw, version):
        """
        Connect to the robot

        Parameters:
                localpw (str): local robot password

        Returns:
                success (bool): Whether the connection was successful
        """
        
        
        logger.debug("Connecting to " + self.addr + ":" + str(self.port) + " version=" + str(version))
        tcp_socket = socket.create_connection((self.addr, self.port))
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        tls_sock = ctx.wrap_socket(tcp_socket)
        logger.debug("Connnected")
        
        logger.debug("Server Cert\n-----BEGIN CERTIFICATE-----\n" + base64.b64encode(tls_sock.getpeercert(binary_form=True)).decode("ascii") + "\n-----END CERTIFICATE-----")
        
        tls_sock.do_handshake()
        self.stream = tls_sock.makefile("rwb")
        
        pkt = self.sendrecv(BinaryMessage.Text(BinaryMessage.MSG_HELLO, "purei9-cli", version))
        
        if not(pkt.user1 == version):
            return False, pkt.user1
            # raise Exception("Protocol version mismatch (" + str(pkt.user1) + " != " + str(version) + ")")
        
        self.robot_id = pkt.parsed
        logger.debug("Hello from Robot ID: " + self.robot_id)
        
        if localpw != None:
        
            pkt = self.sendrecv(BinaryMessage.Text(BinaryMessage.MSG_LOGIN, localpw))
            
            if not(pkt.user1 == 1):
                raise Exception("Bad localpw.")
    
            pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_PING))
            
            logger.debug("Connection Still alive, seems we are authenticated")
        
        return True, version
    
    def disconnect(self) -> None:
        self.stream.close()

class FoundRobot:
    
    def __init__(self, address, id, name):
        self.address = address
        self.id      = id
        self.name    = name
        
    def getclient(self) -> RobotClient:
        return RobotClient(self.address)

def find_robots(timeout = 0.2 , retry_count = 1) -> List[FoundRobot]:
    """Scan for robots in the local subnet using UDP broadcast"""
    
    robots_found = []
    
    broadcast_address = "255.255.255.255"
    robot_port        = 3000
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(timeout)
    s.bind(("0.0.0.0", 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    local_endpoint = s.getsockname()
    local_port     = local_endpoint[1]
    
    pkt = BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_ADDRESS_REQUEST, local_port)
    # pkt.user2 = 0xDEADBEEF # 8094
    
    logger.debug("sendto " + broadcast_address + "#" + str(robot_port) + " " + str(pkt))
    s.sendto(pkt.to_wire(), (broadcast_address, robot_port))
    
    while True:
        
        sender = None
    
        try:
            pkt, sender = s.recvfrom(0xffff)
        except socket.timeout:
            break
        
        pkt = BinaryMessage.from_wire(pkt)
        logger.debug("recvfrom " + sender[0] + "#" + str(sender[1]) + " " + str(pkt))
        
        if pkt.major == 6 and pkt.minor == BinaryMessage.MSG_GET_ADDRESS_RESPONSE:
            robots_found.append(FoundRobot(sender[0], pkt.parsed["RobotID"], pkt.parsed["RobotName"]))
            
    s.close()
    
    if robots_found == [] and retry_count > 0:
        return find_robots(timeout * 2.0, retry_count - 1)
    else:
        return robots_found
