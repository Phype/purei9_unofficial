import json
import time
import logging
import datetime

from typing import List

from .cloudv3_gigya import gigya_login
from .common import AbstractRobot, RobotStates, BatteryStatus, PowerMode, ZoneType, capabilities2model, CleaningSession, DustbinStates
from .util import do_http, CachedData

logger = logging.getLogger(__name__)

class CloudRobot(AbstractRobot, CachedData):
    
    def __init__(self, cloudclient, id):
        CachedData.__init__(self)
        
        self.cloudclient = cloudclient
        self.id          = id
    
    def _getinfo_inner(self):
        r = do_http("GET", self.cloudclient.apiurl + "/appliances/" + self.id, headers=self.cloudclient._getHeaders())
        return r.json()
    
    def getmodel(self):
        capabilities = self._getinfo()["properties"]["reported"]["capabilities"]
        return capabilities2model(capabilities)
    
    def getstatus(self):
        status = self._getinfo()["properties"]["reported"]["robotStatus"]
        return RobotStates(status)

    # TODO: Non Standard
    def getdustbinstatus(self):
        dustbinstatus = self._getinfo()["properties"]["reported"]["dustbinStatus"]
        
        try:
            return DustbinStates[dustbinstatus]
        except:
            
            # Bug #16 - API sometimes returns "notConnected" instead of "empty", work-around this
            if dustbinstatus == "notConnected":
                return DustbinStates.empty
            else:
                return DustbinStates.unset
    
    def startclean(self):
        self._sendCleanCommand("play")
        return True
    
    def spotclean(self):
        self._sendCleanCommand("spot")
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
        return BatteryStatus(bat)
    
    def isconnected(self) -> bool:
        return self._getinfo()["connectionState"] == "Connected"
    
    def getlocalpw(self):
        return None
    
    def getsupportedpowermodes(self):
        
        capabilities = self._getinfo()["properties"]["reported"]["capabilities"]
        if "PowerLevels" in capabilities:
            return [PowerMode.LOW, PowerMode.MEDIUM, PowerMode.HIGH]
        elif "EcoMode" in capabilities:
            return [PowerMode.MEDIUM, PowerMode.HIGH]
        else:
            return [PowerMode.MEDIUM]
    
    def getpowermode(self):
        
        i = self._getinfo()["properties"]["reported"]
        
        powermode = i["powerMode"] if "powerMode" in i else None
        isecomode = i["ecoMode"] if "ecoMode" in i else None
        
        if powermode is not None:
            powermode = PowerMode(powermode)
        
        elif isecomode is not None:
            if isecomode:
                powermode = PowerMode.MEDIUM
            else:
                powermode = PowerMode.HIGH
        else:
            powermode = PowerMode.MEDIUM
            
        return powermode
    

    def setpowermode(self, mode):
        
        i = self._getinfo()["properties"]["reported"]
        
        powermode = i["powerMode"] if "powerMode" in i else None
        isecomode = i["ecoMode"] if "ecoMode" in i else None
        
        if powermode is not None:
            self._update({"powerMode": mode.value})
            
        elif isecomode is not None:
            if mode == PowerMode.MEDIUM:
                self._update({"ecoMode": True})
            elif mode == PowerMode.HIGH:
                self._update({"ecoMode": False})
            else:
                raise Exception("Robot does not support " + str(mode))
        else:
            raise Exception("Robot does not support setting powermode")
        
        return None
    
    def getMaps(self):
        
        r = do_http("GET", self.cloudclient.pureapiurl + "/appliances/" + self.id + "/interactive-maps", headers=self.cloudclient._getHeaders())
        
        return list(map(lambda x: CloudMap(self, x), r.json()))
    
    def cleanZones(self, mapId, zoneIds, powerModes=None):
        
        if powerModes != None:
            zones = list(map(lambda x: {"ZoneId": x[0], "PowerMode": x[1].value}, zip(zoneIds, powerModes)))
        else:
            zones = list(map(lambda zoneId: {"ZoneId": zoneId}, zoneIds))
        
        self._sendCommand({"CustomPlay": { "PersistentMapId": mapId, "Zones": zones }})
    
    def getCleaningSessions(self):
        
        r = do_http("GET", self.cloudclient.pureapiurl + "/appliances/" + self.id + "/history", headers=self.cloudclient._getHeaders())
        
        return list(map(lambda item: CleaningSession(
                endtime=datetime.datetime.strptime(item["timeStamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S"), 
                duration=item["cleaningSession"]["cleaningDuration"] / 10000000.0 if "cleaningSession" in item else None, 
                cleandearea=item["cleanedArea"], 
                #endstatus=item["cleaningSession"]["completion"]
            ), r.json()))
        
    ###
    
    def _sendCleanCommand(self, command):
        self._sendCommand({"CleaningCommand": command})
    
    def _sendCommand(self, command):
        r = do_http("PUT", self.cloudclient.apiurl + "/appliances/" + self.id + "/command", headers=self.cloudclient._getHeaders(), json=command)
        self._mark_changed()
    
    def _update(self, command):
        r = do_http("PUT", self.cloudclient.apiurl + "/appliances/" + self.id, headers=self.cloudclient._getHeaders(), json=command)
        self._mark_changed()

class CloudClient:
    
    def __init__(self, username=None, password=None, token=None, countrycode=None):
        
        self.client_id     = "AEGOneApp"
        self.client_secret = "G6PZWyneWAZH6kZePRjZAdBbyyIu3qUgDGUDkat7obfU9ByQSgJPNy8xRo99vzcgWExX9N48gMJo3GWaHbMJsohIYOQ54zH2Hid332UnRZdvWOCWvWNnMNLalHoyH7xU"
        self.user_agent    = "AEG/2.26 android/10"
        self.x_api_key     = "PEdfAP7N7sUc95GJPePDU54e2Pybbt6DZtdww7dz"
        
        self.baseurl = "https://api.ocp.electrolux.one"
        self.userurl = self.baseurl + "/one-account-user/api/v1"
        self.authorizationurl = self.baseurl + "/one-account-authorization/api/v1"
        self.authenticationurl = self.baseurl + "/one-account-authentication/api/v1"
        self.apiurl  = self.baseurl + "/appliance/api/v2"
        self.pureapiurl = self.baseurl + "/purei/api/v2"
        self.headers = {}
        self.countrycode = countrycode
        
        self.username = username
        self.password = password
        
        self.token = None

        if token:
            self.settoken(token)
        elif countrycode == None:
            raise Exception("Need countrycode to use username/password authentication")
        
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
        
    def _getHeaders(self, no_login=False):
        
        if not(no_login) and (not(self.token) or time.time() > self.token["expires"]):
            
            r = do_http("POST", self.authorizationurl + "/token", json={
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
                "grantType": "client_credentials",
                "scope": ""
            }, headers={
                "x-api-key": self.x_api_key,
                "User-Agent": self.user_agent,
                "Authorization": "Bearer",
            })

            self.settoken(r.text)

            r = do_http("GET", self.userurl + "/identity-providers?brand=aeg&countryCode=" + self.countrycode,
                headers=self._getHeaders(no_login=True))

            data = r.json()[0]
            self.baseurl = data["httpRegionalBaseUrl"]
            idToken, countryCode = gigya_login(self.username, self.password, data["apiKey"], data["domain"])
            
            r = do_http("POST", self.authorizationurl + "/token", json={
                "clientId": self.client_id,
                "idToken": idToken,
                "grantType": "urn:ietf:params:oauth:grant-type:token-exchange"
            }, headers={
                "Origin-Country-Code": countryCode,
                "User-Agent": self.user_agent
            })
            
            self.settoken(r.text)
        
        return {
            "Authorization": "Bearer " + self.token["accessToken"],
            "x-api-key": self.x_api_key,
            "User-Agent": self.user_agent,
            "Context-Brand": "aeg"
        }
    
    def tryLogin(self):
        self.getRobots()
        
    def getRobot(self, id):
        return CloudRobot(self, id)
        
    def getRobots(self):
        robots = []
        r = do_http("GET", self.apiurl + "/appliances", headers=self._getHeaders())
        
        appliances = r.json()
        for appliance in appliances:
            appliance_id = appliance["applianceId"]
            
            r = do_http("GET", self.apiurl + "/appliances/" + appliance_id + "/info", headers=self._getHeaders())
            if r.json()["deviceType"] == "ROBOTIC_VACUUM_CLEANER":
                robots.append(CloudRobot(self, appliance_id))
        
        return robots

class CloudMap:
    
    def __init__(self, cloudrobot, js):
        
        self.cloudclient    = cloudrobot.cloudclient
        self.robot          = cloudrobot
        self.id             = js["id"]
        
        if "name" in js:
            self.name = js["name"]
        else:
            self.name = None
        
        if "zones" in js:
            self.zones = list(map(lambda x: CloudZone(self, x), js["zones"]))
        else:
            self.zones = []
        
        if "sequenceNumber" in js:
            self.sequenceNumber = js["sequenceNumber"]
        else:
            self.sequenceNumber = None
        
        self.info        = None
        self.image       = None
        
        # self._get()
        
    def getImage(self):       
        r = do_http("GET", self.cloudclient.pureapiurl + "/appliances/" + self.robot.id + "/interactive-maps/" + self.id + "/sequences/" + str(self.sequenceNumber) + "/maps", headers=self.cloudclient._getHeaders(), params={"mapFormat": "rawgzip"})
        
        with open("D:\\" + self.robot.id + "-" + self.id + ".gz", "wb") as fp:
            fp.write(r.content)
        
        return None
    
class CloudZone:
    
    def __init__(self, cloudmap, js):
        
        self.cloudclient  = cloudmap.cloudclient
        self.map          = cloudmap
        self.id           = js["id"]
        
        self.name         = js["name"]
        self.type         = ZoneType[js["zoneType"]]
        self.roomcategory = js["roomCategory"]

