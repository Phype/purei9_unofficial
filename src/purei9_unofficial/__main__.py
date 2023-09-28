import sys
import json
import argparse
import logging

from .local import RobotClient, find_robots
from .credentialstore import CredentialStore, CREDENTIAL_STORE_PATH
from .common import PowerMode

# Setup logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.WARNING)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root.addHandler(handler)

logger = logging.getLogger(__name__)

# create the top-level parser
args_main = argparse.ArgumentParser(prog=sys.argv[0])
args_main.add_argument("-d", '--debug', action='store_true', help='enable debug logging')
args_main.add_argument("-o", '--output', type=str, help='output format', choices=["table", "json"], default="table")
args_main.add_argument("-s", '--store-credentials', action='store_true', help='Store/Use crendetials from ' + CREDENTIAL_STORE_PATH)

cmds_main = args_main.add_subparsers(help='command', dest="command")

# cloud v1/v2/v2.1
args_cloud = cmds_main.add_parser('cloud', help='Connect to electrolux purei9 cloud (old API).')

args_cloud.add_argument('-v', "--apiversion", type=int, help='Cloud API version, 1=purei9, 2=wellbeing, 3=electrolux one', choices=[1,2,3], default=2)

#credentials_sub = args_cloud.add_argument_group("Credentials", "One of these is required.")
#credentials = credentials_sub.add_mutually_exclusive_group(required=True)

args_cloud.add_argument('-c', "--credentials", type=str, help='elecrolux cloud credentails in username:password format')
args_cloud.add_argument('-t', "--token", type=str, help='electrolux v2 API token')

cmds_cloud = args_cloud.add_subparsers(help='subcommand, default=status', dest="subcommand")

cmds_cloud_status = cmds_cloud.add_parser('status', help='Get status of all robots.')

cmds_cloud_start = cmds_cloud.add_parser('start', help='Tell a robot to start cleaning.')
cmds_cloud_start.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_spot = cmds_cloud.add_parser('spot', help='Tell the robot to do a spot clean.')
cmds_cloud_spot.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_home = cmds_cloud.add_parser('home', help='Tell a robot to go home.')
cmds_cloud_home.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_pause = cmds_cloud.add_parser('pause', help='Tell a robot to pause cleaning.')
cmds_cloud_pause.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_stop = cmds_cloud.add_parser('stop', help='Tell a robot to stop cleaning.')
cmds_cloud_stop.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_maps = cmds_cloud.add_parser('maps', help='List maps and zones (experimental).')
cmds_cloud_maps.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_cleanzone = cmds_cloud.add_parser('cleanzone', help='Clean a specific zone.')
cmds_cloud_cleanzone.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_cleanzone.add_argument("--mapid",    type=str, help='Persisten Map id.',  required=False)
cmds_cloud_cleanzone.add_argument("--zoneid",   type=str, help='Persisten Zone id.', required=False)
cmds_cloud_cleanzone.add_argument("--mapname",  type=str, help='Persisten Map name.',  required=False)
cmds_cloud_cleanzone.add_argument("--zonename", type=str, help='Persisten Zone name.', required=False)

cmds_cloud_history = cmds_cloud.add_parser('history', help='List history (experimental).')
cmds_cloud_history.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)

cmds_cloud_mode = cmds_cloud.add_parser('mode', help='Set a robots powermode.')
cmds_cloud_mode.add_argument("-r", "--robotid", type=str, help='ID of robot.', required=True)
cmds_cloud_mode.add_argument("-m", "--mode", type=str, choices=list(map(lambda x: x.name, list(PowerMode))), help='Mode to set.', required=True)

# local
args_local = cmds_main.add_parser('local', help='Connect to robot(s) via local network.')

credentials_local = args_local.add_argument_group("Credentials", 'Required for all commands except "find".')
credentials_local.add_argument('-a', "--address", type=str, help='robot ip address')
credentials_local.add_argument('-l', "--localpw", type=str, help='robot localpw (get via "cloud -v1 status")')

cmds_local = args_local.add_subparsers(help='subcommand, default=find', dest="subcommand")

cmds_local_find = cmds_local.add_parser('find', help='Find all robots in the local subnet.')

cmds_local_setlocalpw = cmds_local.add_parser('setlocalpw', help='Set localpw to localpw specified with -l (only works on setup mode)')

cmds_local_find = cmds_local.add_parser('status', help='Get status of the robot.')
cmds_local_wifi = cmds_local.add_parser('wifi', help='Get available wifi networks for the robot.')
cmds_local_start = cmds_local.add_parser('start', help='Tell the robot to start cleaning (note: toggles between play/pause).')
cmds_local_home = cmds_local.add_parser('home', help='Tell the robot to go home.')
cmds_local_home = cmds_local.add_parser('spot', help='Tell the robot to do a spot clean.')
cmds_local_pause = cmds_local.add_parser('pause', help='Tell the robot to pause cleaning (note: toggles between play/pause).')
cmds_local_stop = cmds_local.add_parser('stop', help='Tell the robot to stop cleaning.')

cmds_local_custom = cmds_local.add_parser('custom', help='Send custom message specified as json.')
cmds_local_custom.add_argument("custompacket", help='JSON encoded packet')

cmds_local_mode = cmds_local.add_parser('mode', help='Set a robots powermode.')
cmds_local_mode.add_argument("-m", "--mode", type=str, choices=list(map(lambda x: x.name, list(PowerMode))), help='Mode to set.', required=True)

args = args_main.parse_args()

credentialstore = CredentialStore(do_store=args.store_credentials)

OUTPUT = None

def exiterror(s, parser):
    parser.print_help()
    print("\nError: " + s)
    sys.exit(1)

if args.debug:
    handler.setLevel(logging.DEBUG)

if args.command == "cloud":
        
    # username = None
    # password = None
    # token    = args.token
    
    if args.credentials != None:
        parts = args.credentials.split(":", 2)
        credentialstore.cloud_email = parts[0]
        credentialstore.cloud_passwort = parts[1]
        
    client = None
        
    if args.apiversion == 1:
        from . import cloud

        if credentialstore.cloud_email == None:
            exiterror("No crentials supplied.", args_cloud)
        
        client = cloud.CloudClient(credentialstore.cloud_email, credentialstore.cloud_passwort)
        
    elif args.apiversion == 2:
        from . import cloudv2

        if args.token != None:
            credentialstore.cloud_token = args.token

        if credentialstore.cloud_email == None and credentialstore.cloud_token == None:
            exiterror("No crentials supplied.", args_cloud)
        
        client = cloudv2.CloudClient(username=credentialstore.cloud_email, password=credentialstore.cloud_passwort, token=credentialstore.cloud_token)
        
    elif args.apiversion == 3:
        from . import cloudv3

        if args.token != None:
            credentialstore.cloud_token_v3 = args.token

        if credentialstore.cloud_email == None and credentialstore.cloud_token_v3 == None:
            exiterror("No crentials supplied.", args_cloud)
        
        client = cloudv3.CloudClient(username=credentialstore.cloud_email, password=credentialstore.cloud_passwort, token=credentialstore.cloud_token_v3)
        
    credentialstore.save()
    
    if args.subcommand == "status":
        
        robots = client.getRobots()
        
        OUTPUT = list(map(lambda rc: {
                "id": rc.getid(),
                "model": rc.getmodel(),
                "name": rc.getname(),
                "localpw": rc.getlocalpw(),
                "connected": rc.isconnected(),
                "status": rc.getstatus().name,
                "dustbin": rc.getdustbinstatus().name,
                "battery": rc.getbattery().name,
                "firmware": rc.getfirmware(),
                "powermode": rc.getpowermode().name
            }, robots))
        
    elif args.subcommand in ["start", "home", "pause", "stop", "maps", "history", "mode", "cleanzone", "spot"]:
        if args.robotid == None:
            exiterror("Requires robotid.", args_cloud)
        
        rc = client.getRobot(args.robotid)
        
        if args.subcommand == "start":
            OUTPUT = rc.startclean()
        
        if args.subcommand == "spot":
            OUTPUT = rc.spotclean()
        
        if args.subcommand == "home":
            OUTPUT = rc.gohome()
        
        if args.subcommand == "pause":
            OUTPUT = rc.pauseclean()
        
        if args.subcommand == "stop":
            OUTPUT = rc.stopclean()
        
        if args.subcommand == "history":
            OUTPUT = []
            
            i = 0
            for sess in map(lambda x: {"endtime": x.endtime.isoformat(), "duration": x.duration, "cleandearea": x.cleandearea, "imageurl": x.imageurl, "endstatus": x.endstatus}, rc.getCleaningSessions()):
                
                if args.output == "table":
                    from .imageascii import draw2shade
                    
                    try:
                        if i < 10:
                            sess["imageurl"] = draw2shade(sess["imageurl"]) + "_"
                            i += 1
                        else:
                            sess["imageurl"] = "(not shown)"
                    except:
                        pass
                
                OUTPUT.append(sess)
        
        if args.subcommand == "maps":
            OUTPUT = []
        
            for m in rc.getMaps():
                
                js = m.getImage()
                image = None
                if js:
                    if args.output == "table":
                        from .imageascii import image_json_2_ascii
                        image = image_json_2_ascii(js)
                    else:
                        image = js["PngImage"]
                
                OUTPUT.append({
                    "image": image,
                    "id": m.id,
                    "name": m.name, 
                    "zones": list(map(lambda zone: zone.name, m.zones)), 
                })
        
        if args.subcommand == "cleanzone":
        
            cloudmap = None
            cloudzone = None
        
            if args.mapid == None and args.mapname == None:
                exiterror("Requires mapid or mapname.", args_cloud)
                    
            if args.zoneid == None and args.zonename == None:
                exiterror("Requires zoneid or zonename.", args_cloud)
                    
            for m in rc.getMaps():
                if args.mapid != None and args.mapid == m.id:
                    cloudmap = m
                    break
                    
                if args.mapname != None and args.mapname == m.name:
                    cloudmap = m
                    break
            
            if cloudmap == None:
                exiterror("Map not found.", args_cloud)
                
            logger.debug("Map found: " + cloudmap.id)
                
            for zone in cloudmap.zones:
                
                if args.zoneid != None and args.zoneid == zone.id:
                    cloudzone = zone
                    break
                    
                if args.zonename != None and args.zonename == zone.name:
                    cloudzone = zone
                    break
                
            logger.debug("Zone found: " + zone.id)
            
            if cloudzone == None:
                exiterror("Zone not found.", args_cloud)
                    
            rc.cleanZones(cloudmap.id, [cloudzone.id])
                
        if args.subcommand == "mode":
            OUTPUT = rc.setpowermode(PowerMode[args.mode])
        
    else:
        exiterror("Subcommand not specifed.", args_cloud)
            
    if args.apiversion == 2:
        credentialstore.cloud_token = client.gettoken()      
    elif args.apiversion == 3:
        credentialstore.cloud_token_v3 = client.gettoken()
    
    credentialstore.save()

elif args.command == "local":
    if args.subcommand == "find":
        OUTPUT = list(map(lambda robot: {"address": robot.address, "id": robot.id, "name": robot.name}, find_robots()))
        
    elif args.subcommand in ["setlocalpw"]:
        if args.address == None or args.localpw == None:
            exiterror("Requires address and localpw.", args_local)
        
        rc = RobotClient(args.address)
        rc.connect(None)
        rc.setlocalpw(args.localpw)
        
    elif args.subcommand in ["status", "start", "pause", "stop", "home", "wifi", "mode", "spot", "custom"]:
        if args.address == None or args.localpw == None:
            exiterror("Requires address and localpw.", args_local)
        else:
            rc = RobotClient(args.address)
            rc.connect(args.localpw)
            
            if args.subcommand == "status":
                OUTPUT = [{
                    "id": rc.getid(),
                    "model": rc.getmodel(),
                    "name": rc.getname(),
                    "localpw": args.localpw,
                    "connected": rc.isconnected(),
                    "status": rc.getstatus(),
                    "dustbin": rc.getdustbinstatus().name,
                    "battery": rc.getbattery().name,
                    "firmware": rc.getfirmware(),
                    "powermode": rc.getpowermode().name
                }]
            elif args.subcommand == "custom":
                
                from .message import BinaryMessage
                
                custompacket = json.loads(args.custompacket)
                custompacket = BinaryMessage(**custompacket)
                
                OUTPUT = rc.sendrecv(custompacket).json()
                
                print(OUTPUT)
            
            elif args.subcommand == "start":
                OUTPUT = rc.startclean()
            elif args.subcommand == "spot":
                OUTPUT = rc.spotclean()
            elif args.subcommand == "home":
                OUTPUT = rc.gohome()
            elif args.subcommand == "pause":
                OUTPUT = rc.pauseclean()
            elif args.subcommand == "stop":
                OUTPUT = rc.stopclean()
            elif args.subcommand == "wifi":
                OUTPUT = list(map(lambda x: {"name": x}, rc.getwifinetworks()))
            elif args.subcommand == "mode":
                OUTPUT = rc.setpowermode(PowerMode[args.mode])
    else:
        exiterror("Subcommand not specifed.", args_local)
else:
    exiterror("Command not specifed.", args_main)
    
if OUTPUT != None:
    
    if args.output == "table":
        try:
            import tabulate
        except:
            logger.warn("Cannot use tabular output because missing \"tabulate\" package")
            args.output = "json"
    
    if args.output == "table":
        if type(OUTPUT) != type([]):
            OUTPUT = [[OUTPUT]]
        print(tabulate.tabulate(OUTPUT, headers="keys", tablefmt="pretty"))
    if args.output == "json":
        print(json.dumps(OUTPUT, indent=2))

sys.exit(0)
