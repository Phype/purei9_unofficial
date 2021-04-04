import socket
import ssl
import struct
import json
import base64

from typing import List

from .util import log
from .message import BinaryMessage

class RobotClient:
	
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
	
	STATES = {
		1: "Cleaning",
		2: "Paused Cleaning",
		3: "Spot Cleaning",
		4: "Paused Spot Cleaning",
		5: "Return",
		6: "Paused Return",
		7: "Return for Pitstop",
		8: "Paused Return for Pitstop",
		9: "Charging",
		10: "Sleeping",
		11: "Error",
		12: "Pitstop",
		13: "Manual Steering",
		14: "Firmware Upgrade"
	}
	
	PROTOCOL_VERSION = 2016100701 # 2019041001
	
	def __init__(self, addr : str):
		self.port     = 3002
		self.addr     = addr
		self.robot_id = None
		self.stream   = None
	
	###
	
	def send(self, pkt : BinaryMessage): # minor, data=None, user1=0, user2=0):
		
		if type(pkt) != BinaryMessage:
			raise Exception("pkt must by of type BinaryMessage")
		
		log("<", str(pkt))
		self.stream.write(pkt.to_wire())
		self.stream.flush()
		
	def recv(self) -> BinaryMessage:
		pkt = BinaryMessage.from_stream(self.stream)
		log(">", str(pkt))
		return pkt
	
	def sendrecv(self, pkt : BinaryMessage) -> BinaryMessage:
		self.send(pkt)
		return self.recv()
	
	###
	
	def connect(self, localpw : str) -> bool:
		"""
		Connect to the robot

		Parameters:
				localpw (str): local robot password

		Returns:
				success (bool): Whether the connection was successful
		"""
		
		log("<", "Connecting to " + self.addr + ":" + str(self.port))
		tcp_socket = socket.create_connection((self.addr, self.port))
		
		ctx = ssl.create_default_context()
		ctx.check_hostname = False
		ctx.verify_mode = ssl.CERT_NONE
		
		tls_sock = ctx.wrap_socket(tcp_socket)
		log(">", "Connnected")
		
		log("i", "Server Cert\n-----BEGIN CERTIFICATE-----\n" + base64.b64encode(tls_sock.getpeercert(binary_form=True)).decode("ascii") + "\n-----END CERTIFICATE-----")
		
		tls_sock.do_handshake()
		self.stream = tls_sock.makefile("rwb")
		
		pkt = self.sendrecv(BinaryMessage.Text(BinaryMessage.MSG_HELLO, "purei9-cli", RobotClient.PROTOCOL_VERSION))
		
		if not(pkt.user1 == RobotClient.PROTOCOL_VERSION):
			raise Exception("Protocol version mismatch")
		
		self.robot_id = pkt.parsed
		log("i", "Hello from Robot ID: " + self.robot_id)
		
		pkt = self.sendrecv(BinaryMessage.Text(BinaryMessage.MSG_LOGIN, localpw))
		
		# weird protocol: login response does not indicate sucess, connection will just
		#                 be closed afterwards ...
		
		try:
			pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_PING))
		except:
			log("!", "Exception after login. This normally indicates a bad localpw.")
			return False
		
		log("i", "Connection Still alive, seems we are authenticated")
		return True
	
	def disconnect(self) -> None:
		self.stream.close()
		
	def getid(self) -> str():
		"""Get the robot's id"""
		return self.robot_id
	
	def getname(self) -> str:
		"""Get the robot's name"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETNAME))
		return pkt.parsed
	
	def getfirmware(self) -> dict:
		"""Get robot's firmware properties"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETFIRMWARE))
		return pkt.parsed
	
	def getsettings(self) -> dict:
		"""Get the current robot settings"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETSETTINGS))
		data = json.loads(pkt.parsed)
		return data
	
	def getstatus(self) -> str:
		"""Get the current state of the robot"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETSTATUS))
		return RobotClient.STATES[pkt.user1]
	
	def startclean(self) -> None:
		"""Tell the Robot to start cleaning"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_PLAY))
		
	def gohome(self) -> None:
		"""Tell the Robot to go home"""
		pkt = self.sendrecv(BinaryMessage.HeaderOnly(BinaryMessage.MSG_STARTCLEAN, user1=RobotClient.CLEAN_HOME))

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
	
	s.sendto(pkt.to_wire(), (broadcast_address, robot_port))
	
	while True:
		
		sender = None
	
		try:
			pkt, sender = s.recvfrom(0xffff)
		except socket.timeout:
			break
		
		pkt = BinaryMessage.from_wire(pkt)
		
		if pkt.major == 6 and pkt.minor == BinaryMessage.MSG_GET_ADDRESS_RESPONSE:
			robots_found.append(FoundRobot(sender[0], pkt.parsed["RobotID"], pkt.parsed["RobotName"]))
			
	s.close()
	
	if robots_found == [] and retry_count > 0:
		return find_robots(timeout, retry_count - 1)
	else:
		return robots_found
