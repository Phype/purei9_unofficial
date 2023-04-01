# Local mode seems broken?
"""
import itertools
import unittest
import time

from .util import load_secrets

from .. import local
from .. import common

SECRETS_LOCAL = load_secrets()["local"]
ADDRESS = SECRETS_LOCAL["address"]
LOCALPW = SECRETS_LOCAL["localpassword"]
ROBOTID = SECRETS_LOCAL["robotid"]

class TestLocal(unittest.TestCase):

    def test_find(self):
        for r in itertools.chain(local.find_robots(), local.find_robots(), local.find_robots()):
            if r.address == ADDRESS:
                return
        
        raise Exception("Did not find expected robot at " + ADDRESS)

    def test_connect_wrongpw(self):
        rc = local.RobotClient(ADDRESS)
        
        msg = ""
        
        try:
            rc.connect("0000000")
        except Exception as e:
            msg = str(e)
            
        self.assertIn("Bad localpw", msg)

    def test_connect_status(self):
        rc = local.RobotClient(ADDRESS)
        rc.connect(LOCALPW)
        
        self.assertEqual(rc.getid(), ROBOTID)
        
        rc.getstatus()
        rc.getbattery()
        rc.getfirmware()
        
        rc.disconnect()
        
    def test_set_powermode(self):
        
        rc = local.RobotClient(ADDRESS)
        rc.connect(LOCALPW)
        
        oldmode = rc.getpowermode()
        
        toset = common.PowerMode.HIGH
        if oldmode == common.PowerMode.HIGH:
            toset = common.PowerMode.MEDIUM
            
        rc.setpowermode(toset)
        
        rc.disconnect()
        time.sleep(0.5)
        
        rc = local.RobotClient(ADDRESS)
        rc.connect(LOCALPW)
        
        isset = rc.getpowermode()
        rc.setpowermode(oldmode)
        
        rc.disconnect()
        
        self.assertEqual(isset, toset, "Powermode did not change")

if __name__ == '__main__':
    unittest.main()
"""