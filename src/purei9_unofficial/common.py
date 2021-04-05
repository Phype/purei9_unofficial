
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

PowerModes = {
    1: "Low",
    2: "Medium",
    3: "High",
}

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
        raise Exception("Not implemented")
    
    def gohome(self):
        raise Exception("Not implemented")
    
    def getbattery(self):
        raise Exception("Not implemented")
    
    def getlocalpw(self):
        raise Exception("Not implemented")
    
    def isconnected(self):
        raise Exception("Not implemented")
