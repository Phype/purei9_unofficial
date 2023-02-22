import itertools
import unittest
import time
import datetime

from .util import load_secrets

from ..cloudv2 import CloudClient
from .. import common

SECRETS  = load_secrets()
USERNAME = SECRETS["cloud"]["username"]
PASSWORD = SECRETS["cloud"]["password"]
ROBOTID  = SECRETS["local"]["robotid"]
LOCALPW  = SECRETS["local"]["localpassword"]

class TestCloud(unittest.TestCase):

    def test_01(self):
        cc = CloudClient(USERNAME, PASSWORD)
        cc.tryLogin()
        
        ###
        # Token generation
        ###
        
        token = cc.gettoken()
        
        cc2 = CloudClient(token=token)
        cc2.tryLogin()
        
        ###
        # Robot list
        ###
        
        self.assertIn(ROBOTID, map(lambda rc: rc.getid(), cc.getRobots()), "Robot not found in cloud list")
        rc = cc.getRobot(ROBOTID)
        
        ###
        # Basic Stuff
        ###
        
        rc.getid()
        rc.getname()
        rc.getfirmware()
        rc.getbattery()
        
        ###
        # Sessions
        ###
        
        for session in rc.getCleaningSessions():
            assert type(session.endtime) == datetime.datetime
        
        ###
        # PowerMode
        ###
        
        oldmode = rc.getpowermode()
        
        toset = common.PowerMode.HIGH
        if oldmode == common.PowerMode.HIGH:
            toset = common.PowerMode.MEDIUM
        
        rc.setpowermode(toset)
        time.sleep(0.5)
        
        isset = rc.getpowermode()
        
        time.sleep(0.5)
        rc.setpowermode(oldmode)
        
        self.assertEqual(isset, toset, "Powermode did not change")
        
        ###
        # Maps
        ###
        
        for m in rc.getMaps():
            break

if __name__ == '__main__':
    unittest.main()
