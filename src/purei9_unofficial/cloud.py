import base64
import hashlib
import json

from typing import List

import websocket
import requests
import requests.auth

from .util import log
from .common import AbstractRobot, RobotStates, BatteryStatus

def do_http(method, url, retries=2, **kwargs):
    try:
        log("<", url)
        r = requests.request(method, url, timeout=10, **kwargs)
        r.raise_for_status()
        log(">", r.text)
        return r
    except:
        log(">", "HTTP error")
        if retries > 0:
            return do_http(method, url, retries-1, **kwargs)

class CloudRobot(AbstractRobot):
    
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
        
    def getstatus(self):
        return RobotStates[self.robot_status]
        
    def getid(self) -> str():
        """Get the robot's id"""
        return self.id
    
    def getname(self) -> str:
        """Get the robot's name"""
        return self.name
    
    def getfirmware(self) -> str:
        """Get robot's firmware version"""
        return self.firmware
    
    def getbattery(self) -> str:
        """Get the current robot battery status"""
        return BatteryStatus[self.battery_status]
    
    def isconnected(self) -> bool:
        return self.is_connected
    
    def startclean(self):
        
        headers = self.cloudclient.credentials.copy()
        headers["RobotId"] = self.id
        
        ws = websocket.WebSocket()
        ws.connect("wss://mobile.rvccloud.electrolux.com/api/v1/websocket/AppUser", header = headers)
        ws.send(json.dumps({
            "Type": 1, # 1 Requst, 2 Response, 3 Event
            "Command": "AppUpdate",
            "Body": {
                "CleaningCommand": 1,
            }
        }))
        ws.recv()
        ws.close()
        
        return True
    
    def gohome(self):
        
        headers = self.cloudclient.credentials.copy()
        headers["RobotId"] = self.id
        
        ws = websocket.WebSocket()
        ws.connect("wss://mobile.rvccloud.electrolux.com/api/v1/websocket/AppUser", header = headers)
        ws.send(json.dumps({
            "Type": 1, # 1 Requst, 2 Response, 3 Event
            "Command": "AppUpdate",
            "Body": {
                "CleaningCommand": 3,
            }
        }))
        ws.recv()
        ws.close()
        
        return True
    
    def getlocalpw(self):
        return self.local_pw
    
    ###
        
    def getMaps(self):
        r = do_http("GET", self.cloudclient.apiurl + "/robots/" + self.id + "/interactivemaps", auth=self.cloudclient.httpauth)
        
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
        
        r = do_http("POST", self.apiurl + "/accounts/ConnectToAccount", json=self.credentials)
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
        r = do_http("GET", self.cloudclient.apiurl + "/robots/" + self.robot.id + "/interactivemaps/" + self.id, auth=self.cloudclient.httpauth)
        
        js = r.json()
        
        self.image = base64.b64decode(js["PngImage"])
        
        del js["PngImage"]
        self.info = js
        
        return self.info

###

class CloudRobotv2(AbstractRobot):
    
    def __init__(self, cloudclient, id):
        self.cloudclient = cloudclient
        self.id          = id
        self._info       = None
        
        
    def _getinfo(self):
        
        if self._info == None:
            r = do_http("GET", self.cloudclient.apiurl + "/Appliances/" + self.id, headers=self.cloudclient._getHeaders())
            self._info = r.json()["twin"]
            
        return self._info
    
    def _getall(self):
        r = do_http("GET", self.cloudclient.apiurl + "/Domains/Appliances/" + self.id, headers=self.cloudclient._getHeaders())
        
        """
        url = self.cloudclient.apiurl + "/Domains/Appliances/" + self.id + "/Certificate"
        log("<", url)
        r = requests.get(url, headers=self.cloudclient._getHeaders())
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        url = self.cloudclient.apiurl + "/Hashes/Appliances/" + self.id
        log("<", url)
        r = requests.get(url, headers=self.cloudclient._getHeaders())
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        #url = self.cloudclient.apiurl + "/oaq/appliances/" + self.id
        #log("<", url)
        #r = requests.get(url, headers=self.cloudclient._getHeaders())
        #r.raise_for_status()
        #log(">", json.dumps(r.json(), indent=2))
        
        #url = self.cloudclient.apiurl + "/geo/appliances/" + self.id
        #log("<", url)
        #r = requests.get(url, headers=self.cloudclient._getHeaders())
        #r.raise_for_status()
        #log(">", json.dumps(r.json(), indent=2))
        
        url = self.cloudclient.apiurl + "/robots/" + self.id + "/LifeTime"
        log("<", url)
        r = requests.get(url, headers=self.cloudclient._getHeaders())
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        """
        
        
        
    ###
    
    def getstatus(self):
        status = self._getinfo()["properties"]["reported"]["robotStatus"]
        return RobotStates[status]
    
    def startclean(self):
        self._sendCleanCommand("play")
        return True
    
    def gohome(self):
        self._sendCleanCommand("home")
        return True
        
    def getid(self) -> str():
        """Get the robot's id"""
        return self.id
    
    def getname(self) -> str:
        """Get the robot's name"""
        return self._getinfo()["properties"]["reported"]["applianceName"]
    
    def getfirmware(self) -> str:
        """Get robot's firmware version"""
        return self._getinfo()["properties"]["reported"]["firmwareVersion"]
    
    def getbattery(self) -> str:
        """Get the current robot battery status"""
        bat = self._getinfo()["properties"]["reported"]["batteryStatus"]
        return BatteryStatus[bat]
    
    def isconnected(self) -> bool:
        return self._getinfo()["connectionState"] == "Connected"
    
    def getlocalpw(self):
        return None
        
    ###
    
    def _sendCleanCommand(self, command):
        # play|stop|home
        # curl -v https://api.delta.electrolux.com/api/Appliances/900277283814002391100106/Commands -X PUT --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --data "{\"CleaningCommand\":\"home\"}" --http1.1 | jq -C .
        r = do_http("PUT", self.cloudclient.apiurl + "/Appliances/" + self.id + "/Commands", headers=self.cloudclient._getHeaders(), json={"CleaningCommand": command})

class CloudClientv2:
    
    def __init__(self, username=None, password=None, token=None):
        
        self.client_id     = "Wellbeing"
        self.client_secret = "vIpsOBEenIvjbawqL4HA29"
        
        # self.client_id     = "OsirisElux" # "OsirisAEG" # "OsirisChina"
        # self.client_secret = "5nK3!rGWCN3Jrjkmz"
        
        self.apiurl  = "https://api.delta.electrolux.com/api"
        self.headers = {}
        
        self.username = username
        self.password = password
        self.token    = token
        
    def gettoken(self):
        return self.token
    
    def settoken(self, token):
        self.token = token
        
    def _getHeaders(self):
        
        if not(self.token):
            
            r = do_http("POST", self.apiurl + "/Clients/" + self.client_id, json={"ClientSecret":self.client_secret})
            self.token = r.json()["accessToken"]
            
            r = do_http("POST", self.apiurl + "/Users/Login", json={"Username":self.username, "Password": self.password}, headers={"Authorization": "Bearer " + self.token})
            self.token = r.json()["accessToken"]
        
        return {"Authorization": "Bearer " + self.token}
        
    def getRobot(self, id):
        for r in self.getRobots():
            if r.getid() == id:
                return r
        
    def getRobots(self):
        #curl -v https://api.delta.electrolux.com/api/Domains/Appliances -X GET --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --http1.1 | jq -C
        robots = []
        r = do_http("GET", self.apiurl + "/Domains/Appliances", headers=self._getHeaders())
        
        appliances = r.json()
        for appliance in appliances:
            #curl -v https://api.delta.electrolux.com/api/Appliances/900277283814002391100106 -X GET --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --http1.1 | jq -C .
            appliance_id = appliance["pncId"]
            
            r = do_http("GET", self.apiurl + "/AppliancesInfo/" + appliance_id, headers=self._getHeaders())
            if r.json()["device"] == "ROBOTIC_VACUUM_CLEANER":
                robots.append(CloudRobotv2(self, appliance_id))
        
        return robots
