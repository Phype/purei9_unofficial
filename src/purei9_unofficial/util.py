import sys

DEBUG = False

def setDebug(debug):
    global DEBUG
    DEBUG = debug

def log(lvl, msg):
    if not(DEBUG) and lvl != "!":
        return
    
    sys.stderr.write(" [" + lvl + "] " + msg + "\n")
    sys.stderr.flush()

