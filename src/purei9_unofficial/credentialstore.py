import os
import pathlib
import json

CREDENTIAL_STORE_PATH = str(pathlib.Path.home()) + "/.local/share/purei9_unofficial"
class CredentialStore:
    
    def __init__(self, do_store=False):
        self.path = CREDENTIAL_STORE_PATH
        self.do_store = do_store
        
        self.cloud_email    = None
        self.cloud_passwort = None
        self.cloud_token    = None
        self.cloud_token_v3 = None
        
        self.load()
        
    def save(self):
        if self.do_store:
            try:
                os.mkdir(CREDENTIAL_STORE_PATH)
            except:
                pass
            
            with open(CREDENTIAL_STORE_PATH + "/" + "settings.json", "w") as fp:
                fp.write(json.dumps({
                    "cloud_email": self.cloud_email,
                    "cloud_passwort": self.cloud_passwort,
                    "cloud_token": self.cloud_token,
                    "cloud_token_v3": self.cloud_token_v3,
                }, indent=4))
            
    def load(self):
        if self.do_store:
            try:
                os.mkdir(CREDENTIAL_STORE_PATH)
            except:
                pass
            
            try:
                with open(CREDENTIAL_STORE_PATH + "/" + "settings.json", "r") as fp:
                    data = json.loads(fp.read())
                    
                    self.cloud_email = data["cloud_email"]
                    self.cloud_passwort = data["cloud_passwort"]
                    self.cloud_token = data["cloud_token"]
                    self.cloud_token_v3 = data["cloud_token_v3"]
            except:
                pass
        
        
