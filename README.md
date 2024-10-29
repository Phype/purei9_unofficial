purei9_unofficial
=================

This project includes a client/library to connect to Electrolux and AEG cleaner robots.

Compatibility
-------------

Tested with an AEX RX9 (aka purei9) first Generation and second (aka purei9.2) Generation.

Links
-------------

In case you are just looking on using this, here are some links to alternative/related projects:

 - https://github.com/Ekman/home-assistant-pure-i9 - Homeassistant integration based on this library
 	- https://github.com/Phype/home-assistant-pure-i9 (my fork which sometimes has newer versions of purei9_unofficial, but is generally less polished)
 - https://github.com/JohNan/pyelectroluxgroup - Alternative python library which uses the new open API (https://developer.electrolux.one/)
 - https://github.com/JohNan/homeassistant-wellbeing - Homeassistant integration based on the pyelectroluxgroup library

Disclaimer
----------

The developer of this software is not affiliated at all with Electrolux. Electrolux, AEG and Purei9 are brand/product names by Electrolux AB which i do not have any rights upon.

Installation
------------

Install via pip

	pip install purei9_unofficial 
	
If you want to use the CLI (not only the library) you additionally need to install tabulate

	pip install tabulate 

Usage
-----

The library currently implements 3 interfaces which allows controlling the robot: locally (via a TCP connection on port 3002), and via the 2 different electrolux cloud services. The interface which uses the first version of the electrolux cloud API is the one with the most features implemented currently.

### connection via cloud

See your robots status

	$ python -m purei9_unofficial cloud -c user@email.com:mypassword status
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	|            id            |  name   | localpw  | connected |  status  | battery | firmware | powermode |
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	| 900395798357985798375972 | Cleaner | 01234567 |   True    | Sleeping |  High   |  42.19   |   HIGH    |
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	
Start a cleaning session

	$ python -m purei9_unofficial cloud -c user@email.com:mypassword start -r 900395798357985798375972

### local connection

**NOTE: Local mode seems to have been disabled for the purei9 and Purei9.2 models with a firmware update.**

First you need to get your local robot pw from the cloud API to talk to the robot on a local connection. Note that this only works if your robot was initalized with the old purei9 App (not the "wellbeing" App).

	$ python -m purei9_unofficial cloud -c user@email.com:mypassword status
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	|            id            |  name   | localpw  | connected |  status  | battery | firmware | powermode |
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	| 900395798357985798375972 | Cleaner | 01234567 |   True    | Sleeping |  High   |  42.19   |   HIGH    |
	+--------------------------+---------+----------+-----------+----------+---------+----------+-----------+
	
#### reset localpw
If when the above command is run, localpw is blank, you can reset it using the following instructions. This does not appear to interfer with the cloud connection as it does not use the localpw after set up. (Tested firmware version 42.19 on the first generation purei9, use at your own risk)

1. Flip your purei9 onto its back.
2. Connect your laptop to its network (Network Name: 3Dvision XXX-XXXX).
3. Search its network to local its ip address (will be different to its normal ip on your home network).
	```
	$ python -m purei9_unofficial local find
	+---------------+--------------------------+---------+
	|   Address     |         RobotID          |  Name   |
	+---------------+--------------------------+---------+
	| 192.168.6.1   | 900395798357985798375972 | Cleaner |
	+---------------+--------------------------+---------+
	```
4. Run the setlocalpw command, the command below would set it to 01234567
	```
	$ python3 -m purei9_unofficial local -a 192.168.6.1 -l 01234567 setlocalpw
	```
5. Flip the purei9 back over and put on charge.
6. From here local commands should work.

Note there may be a small delay between the robot being put on its back and the network being available. As well as between putting it on charge and the local commands being available.


You can also use the tool to locate any robots in the network

	$ python -m purei9_unofficial local find
	+---------------+--------------------------+---------+
	|   Address     |         RobotID          |  Name   |
	+---------------+--------------------------+---------+
	| 192.168.1.101 | 900395798357985798375972 | Cleaner |
	+---------------+--------------------------+---------+
	
Now you can connect to your robot locally, get the status and start/stop it.

	$ python -m purei9_unofficial local -a 192.168.1.101 -l 01234567 status
	$ python -m purei9_unofficial local -a 192.168.1.101 -l 01234567 start

### More usage

#### Common options

	$ python -m purei9_unofficial --help
	usage: purei9_unofficial/__main__.py [-h] [-d] [-o {table,json}] [-s] {cloud,local} ...

	positional arguments:
	  {cloud,local}         command
	    cloud               Connect to electrolux purei9 cloud (old API).
	    local               Connect to robot(s) via local network.

	optional arguments:
	  -h, --help            show this help message and exit
	  -d, --debug           enable debug logging
	  -o {table,json}, --output {table,json}
				output format
	  -s, --store-credentials
				Store/Use crendetials from /home/philipp/.local/share/purei9_unofficial
                            
#### Cloud

	$ python -m purei9_unofficial cloud --help
	usage: purei9_unofficial/__main__.py cloud [-h] [-v {1,2}] [-c CREDENTIALS] [-t TOKEN] {status,start,home,pause,stop,maps,history,mode} ...

	positional arguments:
	  {status,start,home,pause,stop,maps,history,mode}
				subcommand, default=status
	    status              Get status of all robots.
	    start               Tell a robot to start cleaning.
	    home                Tell a robot to go home.
	    pause               Tell a robot to pause cleaning.
	    stop                Tell a robot to stop cleaning.
	    maps                List maps and zones (experimental).
	    history             List history (experimental).
	    mode                Set a robots powermode.

	optional arguments:
	  -h, --help            show this help message and exit
	  -v {1,2}, --apiversion {1,2}
				Cloud API version, v1=purei9, v2=wellbeing
	  -c CREDENTIALS, --credentials CREDENTIALS
				elecrolux cloud credentails in username:password format
	  -t TOKEN, --token TOKEN
				electrolux v2 API token

#### Local
	
	$ python -m purei9_unofficial local --help
	usage: purei9_unofficial/__main__.py local [-h] [-a ADDRESS] [-l LOCALPW] {find,status,wifi,start,home,pause,stop,mode} ...

	positional arguments:
	  {find,status,wifi,start,home,pause,stop,mode}
				subcommand, default=find
	    find                Find all robots in the local subnet.
	    setlocalpw          Set localpw to localpw specified with -l (only works on setup mode).
	    status              Get status of the robot.
	    wifi                Get available wifi networks for the robot.
	    start               Tell the robot to start cleaning (note: toggles between play/pause).
	    home                Tell the robot to go home.
	    pause               Tell the robot to pause cleaning (note: toggles between play/pause).
	    stop                Tell the robot to stop cleaning.
	    mode                Set a robots powermode.

	optional arguments:
	  -h, --help            show this help message and exit

	Credentials:
	  Required for all commands except "find".

	  -a ADDRESS, --address ADDRESS
				robot ip address
	  -l LOCALPW, --localpw LOCALPW
				robot localpw (get via "cloud -v1 status")

Library usage
-------------

If you want to use the library instead, please have a look at the [CLI implementation](./src/purei9_unofficial/__main__.py).