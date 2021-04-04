import sys
import json

import tabulate

from .local import RobotClient, find_robots
from .cloud import CloudClient

# import hexdump

def usage():
    print("Usage: " + sys.argv[0] + " [cloud <email> <password>] [status]")
    print("       " + sys.argv[0] + " [cloud <email> <password>] maps <robotid> [write_files]")
    print("       " + sys.argv[0] + " [local <address> <localpw> [status|name|firmware|start|home]]")
    print("       " + sys.argv[0] + " [search]")
    print("")
    print("    cloud: connect to purei9 cloud to get your localpw (does not work currently)")
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
            
            tbl.append([robot.id, robot.name, robot.local_pw, robot.is_connected, robot.robot_status, robot.battery_status, robot.firmware])
        
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
    rc = RobotClient(sys.argv[2])

    if rc.connect(sys.argv[3]):
        
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
            print(rc.getstatus())
            
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
