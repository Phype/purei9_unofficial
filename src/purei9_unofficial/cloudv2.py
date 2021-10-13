import base64
import hashlib
import json
import time
import functools
import logging

from typing import List

import websocket
import requests
import requests.auth

from .common import AbstractRobot, RobotStates, BatteryStatus, PowerMode
from .util import do_http, CachedData

logger = logging.getLogger(__name__)

class CloudRobot(AbstractRobot, CachedData):
    
    def __init__(self, cloudclient, id):
        CachedData.__init__(self)
        
        self.cloudclient = cloudclient
        self.id          = id
    
    def _getinfo_inner(self):
        r = do_http("GET", self.cloudclient.apiurl + "/Appliances/" + self.id, headers=self.cloudclient._getHeaders())
        return r.json()["twin"]
    
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
    
    def pauseclean(self):
        self._sendCleanCommand("pause")
        return True
    
    def stopclean(self):
        self._sendCleanCommand("stop")
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
    
    def getpowermode(self):
        return None
        
    ###
    
    def _sendCleanCommand(self, command):
        # play|stop|home
        # curl -v https://api.delta.electrolux.com/api/Appliances/900277283814002391100106/Commands -X PUT --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --data "{\"CleaningCommand\":\"home\"}" --http1.1 | jq -C .
        r = do_http("PUT", self.cloudclient.apiurl + "/Appliances/" + self.id + "/Commands", headers=self.cloudclient._getHeaders(), json={"CleaningCommand": command})
        self._mark_changed()

class CloudClient:
    
    def __init__(self, username=None, password=None, token=None):
        
        self.client_id     = "Wellbeing"
        self.client_secret = "vIpsOBEenIvjbawqL4HA29"
        
        # self.client_id     = "OsirisElux" # "OsirisAEG" # "OsirisChina"
        # self.client_secret = "5nK3!rGWCN3Jrjkmz"
        
        self.apiurl  = "https://api.delta.electrolux.com/api"
        self.headers = {}
        
        self.username = username
        self.password = password
        
        self.token = None
        self.settoken(token)
        
    def gettoken(self):
        return json.dumps(self.token)
    
    def settoken(self, token):
        if token:
            self.token = json.loads(token)
            if not("expires" in self.token):
                if "expiresIn" in self.token:
                    self.token["expires"] = time.time() + self.token["expiresIn"] - 60
                else:
                    self.token["expires"] = time.time() + 60
            
        else:
            self.token = None
            
        
    def _getHeaders(self):
        
        if not(self.token) or time.time() > self.token["expires"]:
            
            r = do_http("POST", self.apiurl + "/Clients/" + self.client_id, json={"ClientSecret":self.client_secret})
            self.settoken(r.text)
            
            r = do_http("POST", self.apiurl + "/Users/Login", json={"Username":self.username, "Password": self.password}, headers={"Authorization": "Bearer " + self.token["accessToken"]})
            self.settoken(r.text)
        
        return {"Authorization": "Bearer " + self.token["accessToken"]}
    
    def tryLogin(self):
        self.getRobots()
        
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
                robots.append(CloudRobot(self, appliance_id))
        
        return robots
