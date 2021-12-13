from enum import Enum

class BatteryStatus(Enum):
    Dead = 1
    CriticalLow = 2
    Low = 3
    Medium = 4
    Normal = 5
    High = 6

class RobotStates(Enum):
    Cleaning = 1
    Paused_Cleaning = 2
    Spot_Cleaning = 3
    Paused_Spot_Cleaning = 4
    Return = 5
    Paused_Return = 6
    Return_for_Pitstop = 7
    Paused_Return_for_Pitstop = 8
    Charging = 9
    Sleeping = 10
    Error = 11
    Pitstop = 12
    Manual_Steering = 13
    Firmware_Upgrade = 14

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

class DustbinStates(Enum):
    unset = 0       # No information available
    connected = 1   # Dustbin is in the robot and empty 
    empty = 2       # Dustbin has been removed from the robot
    full = 3        # Dustbin is full and should be emptied

class CleaningSession:
    
    def __init__(self, endtime, duration, cleandearea, endstatus=None, imageurl=None, mapid=None, error=None):
        
        self.endtime     = endtime      # datetime
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
    
    capabilities = set(map(lambda x: x.lower(), capabilities.keys()))
    
    print(capabilities)
    
    if ("powerlevels" in capabilities) and not("ecomode" in capabilities):
        return "PUREi9.2"
    elif not("powerlevels" in capabilities) and ("ecomode" in capabilities):
        return "PUREi9"
    else:
        return "unknown"
