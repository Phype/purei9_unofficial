from enum import Enum

BatteryStatus = {
    1: "Dead",
    2: "CriticalLow",
    3: "Low",
    4: "Medium",
    5: "Normal",
    6: "High",
}

RobotStates = {
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

class PowerMode(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class ZoneType(Enum):
    clean = 0
    avoid = 1
    
class CleaningSessionResult(Enum):
    unknown0 = 0
    unknown1 = 1
    unknown2 = 2
    unknown3 = 3
    endedNotFindingCharger = 4
    unknown5 = 4
    unknown6 = 5
    unknown7 = 6
    unknown8 = 7
    cleaningFinishedSuccessfulInCharger = 9
    cleaningFinishedSuccessfulInStartPose = 10
    abortedByUser = 11
    unknown12 = 12
    unknown13 = 13
    unknown14 = 14
    unknown15 = 15
    unknown16 = 16
    unknown17 = 17

class CleaningSession:
    
    def __init__(self, starttime, duration, cleandearea, endstatus=None, imageurl=None, mapid=None, error=None):
        
        self.starttime   = starttime    # datetime
        self.duration    = duration     # duration in seconds
        self.cleandearea = cleandearea  # area in m2
        
        self.endstatus   = endstatus    # end status (Needs an enum)
        self.imageurl    = imageurl     # url of image if available
        self.mapid       = mapid        # map id
        self.error       = error        # String(?)

class AbstractRobot:
    
    def __init__(self):
        pass
    
    def getid(self):
        raise Exception("Not implemented")
    
    def getstatus(self):
        raise Exception("Not implemented")
    
    def getfirmware(self):
        raise Exception("Not implemented")
    
    def getname(self):
        raise Exception("Not implemented")
    
    def startclean(self):
        """Tell the Robot to start cleaning (note: this is a start/pause toggle)"""
        raise Exception("Not implemented")
    
    def stopclean(self):
        """Tell the Robot to stop cleaning"""
        raise Exception("Not implemented")
    
    def pauseclean(self):
        """Tell the Robot to pause cleaning (note: this is a start/pause toggle)"""
        raise Exception("Not implemented")
    
    def gohome(self):
        """Tell the Robot to go home"""
        raise Exception("Not implemented")
    
    def getbattery(self):
        raise Exception("Not implemented")
    
    def getlocalpw(self):
        raise Exception("Not implemented")
    
    def isconnected(self):
        raise Exception("Not implemented")


def capabilities2model(capabilities):
	if ("PowerLevels" in capabilities) and not("EcoMode" in capabilities):
		return "PUREi9.2"
	elif not("PowerLevels" in capabilities) and ("EcoMode" in capabilities):
		return "PUREi9"
	else:
		return "unknown"
