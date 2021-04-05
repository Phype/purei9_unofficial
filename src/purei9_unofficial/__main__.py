import sys
import json

import tabulate

from .local import RobotClient, find_robots
from .cloud import CloudClient, CloudClientv2

# import hexdump

def usage():
    print("Usage: " + sys.argv[0] + " [cloud <email> <password>] [status]")
    print("       " + sys.argv[0] + " [cloud <email> <password>] maps <robotid> [write_files]")
    print("       " + sys.argv[0] + " [cloudv2 <email> <password>] [status]")
    print("       " + sys.argv[0] + " [cloudv2 <email> <password>] start <robotid>")
    print("       " + sys.argv[0] + " [cloudv2 <email> <password>] home <robotid>")
    print("       " + sys.argv[0] + " [local <address> <localpw> [status|name|firmware|start|home]]")
    print("       " + sys.argv[0] + " [search]")
    print("")
    print("    cloud: connect to purei9 cloud")
    print("")
    print("    local: connect to robot at <address> using <localpw>")
    print("           status   - show basic status")
    print("           firmware - show firmware info")
    print("           start    - start cleaning")
    print("           home     - stop cleaning and go home")
    print("")
    print("    search: search for robots in the local network")

if len(sys.argv) < 2:
    usage()
    
elif sys.argv[1] == "cloudv2":
    cc = CloudClientv2(sys.argv[2], sys.argv[3])
    
    cmd = "status"
    if len(sys.argv) > 4:
        cmd = sys.argv[4]
    
    if cmd == "status":
        
        robots = cc.getRobots()
        
        tbl = []
        tbl_hdr = ["Robot ID", "Name", "Localpw", "Connected", "Status", "Battery", "Firmware"]
        
        for robot in robots:
            
            tbl.append([robot.getid(), robot.getname(), "-", "-", robot.getstatus(), "-", "-"])
        
        print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
    
    if cmd == "start" or cmd == "home":
        robotid = sys.argv[5]
        
        robot = cc.getRobot(robotid)
        
        if cmd == "start":
            robot.startclean()
        elif cmd == "home":
            robot.gohome()

elif sys.argv[1] == "cloud":
    cc = CloudClient(sys.argv[2], sys.argv[3])
    cmd = "status"
    
    if len(sys.argv) > 4:
        cmd = sys.argv[4]
    
    if cmd == "status":
        
        robots = cc.getRobots()
        
        tbl = []
        tbl_hdr = ["Robot ID", "Name", "Localpw", "Connected", "Status", "Battery", "Firmware"]
        
        for robot in robots:
            
            tbl.append([robot.getid(), robot.getname(), robot.local_pw, robot.is_connected, robot.getstatus(), robot.battery_status, robot.firmware])
        
        print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
        
    elif cmd == "maps":
        if len(sys.argv) > 5:
            id = sys.argv[5]
        else:
            print("Requires argument: Robot ID")
            sys.exit(0)
        
        write = False
        if len(sys.argv) > 6:
            write = True
        
        robot   = cc.getRobot(id)
        
        tbl     = []
        tbl_hdr = ["Map ID", "Timestamp"]
        
        for m in robot.getMaps():
            
            m.get()
            
            tbl.append([m.id, m.info["Timestamp"]])
            
            if write:
                with open(m.id + ".png", "wb") as fp:
                    fp.write(m.image)
                
        print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
        
    else:
        print("Error: Unknown cmd " + cmd)

elif sys.argv[1] == "local":
    
    address = sys.argv[2]
    localpw = sys.argv[3]
    
    rc = RobotClient(address)

    if rc.connect(localpw):
        
        if len(sys.argv) > 4:
            action = sys.argv[4]
        else:
            action = "status"
            
        if action == "start":
            print(json.dumps(rc.startclean(), indent=2))
            
        elif action == "home":
            print(json.dumps(rc.gohome(), indent=2))
                
        elif action == "firmware":
            print(json.dumps(rc.getfirmware(), indent=2))
            
        elif action == "status":
            
            tbl = []
            tbl_hdr = ["Robot ID", "Name", "Localpw", "Connected", "Status", "Battery", "Firmware"]
            tbl.append([rc.getid(), rc.getname(), localpw, "-", rc.getstatus(), rc.getbattery(), rc.getfirmware()])
            
            print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
            
        elif action == "name":
            print(rc.getname())
        
        else:
            log("!", "Unknown action " + action)
            print(json.dumps(None))
        
        # print("ID:       " + rc.robot_id)
        # print("Name:     " + rc.getname())
        # print("Status:   " + rc.getstatus())
        # print("Settings: " + str(rc.getsettings()))
        
        # print(json.dumps(rc.getfirmware(), indent=2))
        
    else:
        print(json.dumps(None))
        

elif sys.argv[1] == "search":
    robots = find_robots()
    
    tbl_hdr = ["Address", "RobotID", "Name"]
    tbl = []
    
    for robot in robots:
        tbl.append([robot.address, robot.id, robot.name])
    
    print(tabulate.tabulate(tbl, headers=tbl_hdr, tablefmt="pretty"))
    
    
else:
    usage()
