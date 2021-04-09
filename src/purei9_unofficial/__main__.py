import sys
import json
import argparse


import tabulate

from .util import setDebug

from .local import RobotClient, find_robots
from .cloud import CloudClient, CloudClientv2


# create the top-level parser
args_main = argparse.ArgumentParser(prog=sys.argv[0])
args_main.add_argument("-d", '--debug', action='store_true', help='enable debug logging')
args_main.add_argument("-o", '--output', type=str, help='output format', choices=["table", "json"], default="table")
cmds_main = args_main.add_subparsers(help='command', dest="command")

# cloud v1/v2
args_cloud = cmds_main.add_parser('cloud', help='Connect to electrolux purei9 cloud (old API).')

args_cloud.add_argument('-v', "--apiversion", type=int, help='Cloud API version, v1=purei9, v2=wellbeing', choices=[1,2], default=1)

credentials_sub = args_cloud.add_argument_group("Credentials", "One of these is required.")
credentials = credentials_sub.add_mutually_exclusive_group(required=True)
credentials.add_argument('-c', "--credentials", type=str, help='elecrolux cloud credentails in username:password format')
credentials.add_argument('-t', "--token", type=str, help='electrolux v2 API token')

cmds_cloud = args_cloud.add_subparsers(help='subcommand, default=status', dest="subcommand")

cmds_cloud_status = cmds_cloud.add_parser('status', help='Get status of all robots.')

cmds_cloud_start = cmds_cloud.add_parser('start', help='Tell a robot to start cleaning.')
cmds_cloud_start.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_home = cmds_cloud.add_parser('home', help='Tell a robot to go home.')
cmds_cloud_home.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_maps = cmds_cloud.add_parser('maps', help='Download maps (experimental).')
cmds_cloud_maps.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

# local
args_local = cmds_main.add_parser('local', help='Connect to robot(s) via local network.')

credentials_local = args_local.add_argument_group("Credentials", 'Required for all commands except "find".')
credentials_local.add_argument('-a', "--address", type=str, help='robot ip address')
credentials_local.add_argument('-l', "--localpw", type=str, help='robot localpw (get via "cloud -v1 status")')

cmds_local = args_local.add_subparsers(help='subcommand, default=find', dest="subcommand")

cmds_local_find = cmds_local.add_parser('find', help='Find all robots in the local subnet.')

cmds_local_find = cmds_local.add_parser('status', help='Get status of the robot.')
cmds_local_start = cmds_local.add_parser('start', help='Tell the robot to start cleaning.')
cmds_local_home = cmds_local.add_parser('home', help='Tell the robot to go home.')

args = args_main.parse_args()

OUTPUT = None

def exiterror(s, parser):
    parser.print_help()
    print("\nError: " + s)
    sys.exit(1)

if args.debug:
    setDebug(True)

if args.command == "cloud":
        
    username = None
    password = None
    token    = args.token
    
    if args.credentials != None:
        username, password = args.credentials.split(":")
        
    client = None
        
    if args.apiversion == 1:
        if args.credentials == None:
            exiterror("Cloud API v1 cannot use token.", args_cloud)
        client = CloudClient(username, password)
    elif args.apiversion == 2:
        client = CloudClientv2(username=username, password=password, token=token)
        
    if args.subcommand == "status":
        OUTPUT = list(map(lambda rc: {
                "id": rc.getid(),
                "name": rc.getname(),
                "localpw": rc.getlocalpw(),
                "connected": rc.isconnected(),
                "status": rc.getstatus(),
                "battery": rc.getbattery(),
                "firmware": rc.getfirmware(),
            }, client.getRobots()))
        
    elif args.subcommand in ["start", "home", "maps"]:
        if args.robotid == None:
            exiterror("Requires robotid.", args_cloud)
        
        rc = client.getRobot(args.robotid)
        
        if args.subcommand == "start":
            OUTPUT = rc.startclean()
        
        if args.subcommand == "home":
            OUTPUT = rc.gohome()
        
        if args.subcommand == "maps":
            OUTPUT = []
            for map in rc.getMaps():
                map.get()
                OUTPUT.append(map.info)
        
    else:
        exiterror("Subcommand not specifed.", args_cloud)

elif args.command == "local":
    if args.subcommand == "find":
        OUTPUT = list(map(lambda robot: {"address": robot.address, "id": robot.id, "name": robot.name}, find_robots()))
    elif args.subcommand in ["status", "start", "home"]:
        if args.address == None or args.localpw == None:
            exiterror("Requires address and localpw.", args_local)
        else:
            rc = RobotClient(args.address)
            rc.connect(args.localpw)
            
            if args.subcommand == "status":
                OUTPUT = [{
                    "id": rc.getid(),
                    "name": rc.getname(),
                    "localpw": args.localpw,
                    "connected": rc.isconnected(),
                    "status": rc.getstatus(),
                    "battery": rc.getbattery(),
                    "firmware": rc.getfirmware(),
                }]
            elif args.subcommand == "start":
                OUTPUT = rc.startclean()
            elif args.subcommand == "home":
                OUTPUT = rc.gohome()
    else:
        exiterror("Subcommand not specifed.", args_local)
else:
    exiterror("Command not specifed.", args_main)
    
if OUTPUT != None:
    if args.output == "table":
        if type(OUTPUT) != type([]):
            OUTPUT = [[OUTPUT]]
        print(tabulate.tabulate(OUTPUT, headers="keys", tablefmt="pretty"))
    elif args.output == "json":
        print(json.dumps(OUTPUT, indent=2))

sys.exit(0)
