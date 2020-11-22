import socket
import ssl
import struct
import time
import sys
import json
import sys
import base64
import hashlib

import requests
import requests.auth

import tabulate

# import hexdump

DEBUG = True

def log(lvl, msg):
	if not(DEBUG) and lvl != "!":
		return
	
	sys.stderr.write(" [" + lvl + "] " + msg + "\n")
	sys.stderr.flush()

class CloudClient:
	
	def __init__(self, email, password):
		password = CloudClient.chksum(password)
		self.apiurl = "https://mobile.rvccloud.electrolux.com/api/v1"
		self.credentials = {
			"AccountPassword": password,
			"Email": email,
		}
		self.httpauth = requests.auth.HTTPBasicAuth(email, password)
		
	@staticmethod
	def chksum(pw):
		buf = pw + "947X6kdLJyrhlCDzUyzFwT4s4NZL3O8eLs0PE4Hi7hU="
		buf = buf.encode("utf-16")[2:]
		return base64.b64encode(hashlib.sha256(buf).digest()).decode("ascii")
		
	def getRobots(self):
		r = requests.post(self.apiurl + "/accounts/ConnectToAccount", json=self.credentials)
		try:
			return list(map(lambda r: CloudRobot(self, r["RobotID"], r), r.json()["RobotList"]))
		except:
			log("!", "Cannot login: " + str(r))
			
			for k in r.headers:
				log("i", k + ": " + r.headers[k])
			log("i", r.text)
			
	def getRobot(self, id):
		return CloudRobot(self, id)
	

class CloudRobot:
	
	def __init__(self, cloudclient, id, info=None):
		self.cloudclient = cloudclient
		self.id          = id
		self.info        = info
		
		if info:
		
			self.name           = info["RobotName"]
			self.is_connected   = info["Connected"]
			self.firmware       = info["FirmwareVersion"]
			self.robot_status   = info["RobotStatus"]
			self.battery_status = info["BatteryStatus"]
			self.local_pw       = info["LocalRobotPassword"]
		
	def getMaps(self):
		r = requests.get(self.cloudclient.apiurl + "/robots/" + self.id + "/interactivemaps", auth=self.cloudclient.httpauth)
		
		return list(map(lambda x: CloudMap(self, x["Id"]), r.json()))
	
class CloudMap:
	
	def __init__(self, cloudrobot, id):
		
		self.cloudclient = cloudrobot.cloudclient
		self.robot       = cloudrobot
		self.id          = id
		self.info        = None
		self.image       = None
		
	def get(self):
		r = requests.get(self.cloudclient.apiurl + "/robots/" + self.robot.id + "/interactivemaps/" + self.id, auth=self.cloudclient.httpauth)
		
		js = r.json()
		
		self.image = base64.b64decode(js["PngImage"])
		
		del js["PngImage"]
		self.info = js
		
		return self.info

class RobotClient:
	
	MSG_HELLO        = 3000
	MSG_LOGIN        = 3005
	MSG_PING         = 1000
	MSG_GETNAME      = 1011
	MSG_GETFIRMWARE  = 1010
	MSG_GETSETTINGS  = 1023
	MSG_STARTCLEAN   = 1014
	MSG_GETSTATUS    = 1012
	
	CLEAN_PLAY  = 1
	CLEAN_SPOT  = 2
	CLEAN_HOME  = 3
	CLEAN_PAUSE = 4 # Unused by App?
	CLEAN_STOP  = 5 # Unused by App?
	
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
	
	STATE_CLEANING  = 1
	STATE_PAUSED    = 2
	STATE_SPOTCLEAN = 3
	STATE_PAUSEDSPOTCLEAN = 4
	STATE_RETURN            = 5
	STATE_PAUSEDRETURN        = 6
	STATE_RETURNPITSTOP       = 7
	STATE_PAUSEDRETURNPITSTOP = 8
	STATE_SPOTCLEAN = 3
	
	PROTOCOL_VERSION = 2016100701 # 2019041001
	
	def __init__(self, addr, localpw):
		self.port    = 3002
		self.addr    = addr
		self.localpw = localpw
		
		self.ctx = ssl.create_default_context()
		self.ctx.check_hostname = False
		self.ctx.verify_mode = ssl.CERT_NONE
		
		self.robot_id = None
	
	def send(self, minor, data=None, user1=0, user2=0):
		
		if data != None:
			major = 2
			length = len(data)
		else:
			major = 1
			length = 0
		
		magic = 30194250
		
		log("<", "send " + str(minor) + " user1=" + str(user1) + " user2=" + str(user2) + " len=" + str(length))
		
		pkt = struct.pack("<IIIIII", magic, major, minor, user1, user2, length)
		
		if data:
			pkt += data
		
		self.sock.send(pkt)
		
	def recv(self):
		hdr = self.sock.recv(24)
		if len(hdr) != 24:
			raise Exception("Cannot read")
		
		magic, major, minor, user1, user2, length = struct.unpack("<IIIIII", hdr)
		data = self.sock.recv(length)
		
		log(">", "recv " + str(minor) + " user1=" + str(user1) + " user2=" + str(user2) + " len=" + str(length))
		
		return minor, data, user1, user2
	
	def sendrecv(self, minor, data=None, user1=0, user2=0):
		self.send(minor, data, user1, user2)
		return self.recv()
	
	def connect(self):
		log("<", "Connecting to " + self.addr + ":" + str(self.port))
		self.conn = socket.create_connection((self.addr, self.port))
		self.sock = self.ctx.wrap_socket(self.conn)
		log(">", "Connnected")
		
		log("i", "Server Cert\n-----BEGIN CERTIFICATE-----\n" + base64.b64encode(self.sock.getpeercert(binary_form=True)).decode("ascii") + "\n-----END CERTIFICATE-----")
		
		self.sock.do_handshake()
		
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_HELLO, "purei9-cli".encode("utf-8"), user1=RobotClient.PROTOCOL_VERSION)
		assert user1 == RobotClient.PROTOCOL_VERSION, "Protocol version mismatch"
		
		self.robot_id = data.decode("utf-8")
		log("i", "Hello from Robot ID: " + self.robot_id)
		
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_LOGIN, self.localpw.encode("utf-8"))
		
		# weird protocol: login response does not indicate sucess, connection will just
		#                 be closed afterwards ...
		
		try:
			minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_PING)
		except:
			log("!", "Exception after login. This normally indicates a bad localpw.")
			return False
		
		log("i", "Connection Still alive, seems we are authenticated")
		return True
	
	def info(self):
		return {
			"id": self.robot_id,
			"name": self.getname(),
			"status": self.getstatus(),
			"settings": self.getsettings()
		}
		
	def getname(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_GETNAME)
		return data.decode("utf-8")
	
	def getfirmware(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_GETFIRMWARE)
		
		lst = []
		while len(data) > 4:
			l     = struct.unpack("<I", data[:4])[0]
			data  = data[4:]
			value = data[:l]
			data  = data[l:]
			lst.append(value)
		
		i = 0
		obj = {}
		while i+1 < len(lst):
			obj[lst[i].decode("utf-8")] = lst[i+1].decode("utf-8")
			i += 2
		
		return obj
	
	def getsettings(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_GETSETTINGS)
		data = json.loads(data.decode("utf-8"))
		return data
	
	def getstatus(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_GETSTATUS)
		return RobotClient.STATES[user1]
	
	def startclean(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_STARTCLEAN, user1=RobotClient.CLEAN_PLAY)
		return {
			"minor": minor,
			"data": data.decode("ascii"),
			"user1": user1,
			"user2": user2
		}
		
	def gohome(self):
		minor, data, user1, user2 = self.sendrecv(RobotClient.MSG_STARTCLEAN, user1=RobotClient.CLEAN_HOME)
		return {
			"minor": minor,
			"data": data.decode("ascii"),
			"user1": user1,
			"user2": user2
		}
	

if __name__ == "__main__":

	def usage():
		print("Usage: " + sys.argv[0] + " [cloud <email> <password>] [status]")
		print("       " + sys.argv[0] + " [cloud <email> <password>] maps <robotid> [write_files]")
		print("       " + sys.argv[0] + " [local <address> <localpw> [status|firmware|start|home]]")
		print("")
		print("    cloud: connect to purei9 cloud to get your localpw (does not work currently)")
		print("")
		print("    local: connect to robot at <address> using <localpw>")
		print("           status   - show basic status")
		print("           firmware - show firmware info")
		print("           start    - start cleaning")
		print("           home     - stop cleaning and go home")

	if len(sys.argv) < 2:
		usage()

	elif sys.argv[1] == "cloud":
		cc = CloudClient(sys.argv[2], sys.argv[3])
		cmd = "status"
		
		if len(sys.argv) > 4:
			cmd = sys.argv[4]
		
		if cmd == "status":
			
			robots = cc.getRobots()
			
			tbl = []
			tbl_hdr = ["Robot ID", "Name", "Localpw", "Connected", "Status", "Battery", "Firmware"]
			
			for robot in robots:
				
				tbl.append([robot.id, robot.name, robot.local_pw, robot.is_connected, robot.robot_status, robot.battery_status, robot.firmware])
			
			print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
			
		elif cmd == "maps":
			if len(sys.argv) > 5:
				id = sys.argv[5]
			else:
				print("Requires argument: Robot ID")
				sys.exit(0)
			
			write = False
			if len(sys.argv) > 6:
				write = True
			
			robot = cc.getRobot(id)
			
			tbl = []
			tbl_hdr = ["Map ID", "Timestamp"]
			
			for m in robot.getMaps():
				
				m.get()
				
				tbl.append([m.id, m.info["Timestamp"]])
				
				if write:
					with open(m.id + ".png", "wb") as fp:
						fp.write(m.image)
					
			print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
			
		else:
			print("Error: Unknown cmd " + cmd)

	elif sys.argv[1] == "local":
		rc = RobotClient(sys.argv[2], sys.argv[3])

		if rc.connect():
			
			if len(sys.argv) > 4:
				action = sys.argv[4]
			else:
				action = "status"
				
			if action == "start":
				print(json.dumps(rc.startclean(), indent=2))
				
			elif action == "home":
				print(json.dumps(rc.gohome(), indent=2))
					
			elif action == "firmware":
				print(json.dumps(rc.getfirmware(), indent=2))
				
			elif action == "status":
				print(json.dumps(rc.info(), indent=2))
			
			else:
				log("!", "Unknown action " + action)
				print(json.dumps(None))
			
			# print("ID:       " + rc.robot_id)
			# print("Name:     " + rc.getname())
			# print("Status:   " + rc.getstatus())
			# print("Settings: " + str(rc.getsettings()))
			
			# print(json.dumps(rc.getfirmware(), indent=2))
			
		else:
			print(json.dumps(None))

	else:
		usage()
