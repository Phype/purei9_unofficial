import itertools
import unittest

from .util import load_secrets

from .. import local

SECRETS_LOCAL = load_secrets()["local"]
ADDRESS = SECRETS_LOCAL["address"]
LOCALPW = SECRETS_LOCAL["localpassword"]

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

    def test_connect(self):
        rc = local.RobotClient(ADDRESS)
        rc.connect(LOCALPW)

if __name__ == '__main__':
    unittest.main()
