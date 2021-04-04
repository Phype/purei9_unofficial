import base64
import hashlib

from typing import List

import requests
import requests.auth

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
		else:
			self.name           = None
			self.is_connected   = None
			self.firmware       = None
			self.robot_status   = None
			self.battery_status = None
			self.local_pw       = None
			
	def getlocalpw(self):
		return self.local_pw
		
	def getMaps(self):
		r = requests.get(self.cloudclient.apiurl + "/robots/" + self.id + "/interactivemaps", auth=self.cloudclient.httpauth)
		
		return list(map(lambda x: CloudMap(self, x["Id"]), r.json()))

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
		
	def getRobots(self) -> List[CloudRobot]:
		"""Get all robots linked to the cloud account"""
        
		r = requests.post(self.apiurl + "/accounts/ConnectToAccount", json=self.credentials)
		try:
			return list(map(lambda r: CloudRobot(self, r["RobotID"], r), r.json()["RobotList"]))
		except:
			log("!", "Cannot login: " + str(r))
			
			for k in r.headers:
				log("i", k + ": " + r.headers[k])
			log("i", r.text)
			
	def getRobot(self, id) -> CloudRobot:
		"""Make a CloudRobot instance with a given id. id is not checked."""
		return CloudRobot(self, id)
	
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
