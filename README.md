purei9_unofficial
=================

Small proof-of-concept client to connect to Electrolux and AEG cleaner robots.

Compatibility
-------------

Only tested with an AEX RX9 (aka purei9) first Generation.

Update: Also seems to work with Purei9.2: https://community.home-assistant.io/t/integrating-eectrolux-pure-i9-robotic-vacuum/78648/11

Security
--------

Other than the purei9 app, this tool does not verify the robot's TLS certificate, so beware of MitMs in your LAN, eavedropping on your robot. In case you are curious how the trust model works anyway: The TLS certificate of the robot is self signed and verified against a known public key which is gathered from the purei9 cloud.

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

First you need to get your local robot pw to talk to the robot.

	$ python -m purei9_unofficial cloud -c user@email.com:mypassword status
	[
		{
			"RobotID": "900395798357985798375972",
			"Connected": true,
			"FirmwareVersion": "40.17",
			...
			"LocalRobotPassword": "29379204",
			...
		}
	]
	
You can also use the tool to locate any robots in the network

	$ python -m purei9_unofficial local find
	+---------------+--------------------------+---------+
	|   Address     |         RobotID          |  Name   |
	+---------------+--------------------------+---------+
	| 192.168.1.101 | 900395798357985798375972 | Cleaner |
	+---------------+--------------------------+---------+
	
Now you can connect to your robot.

	$ python -m purei9_unofficial local -a 192.168.1.101 -l 29379204 status
	
	 [<] Connecting to 192.168.1.101:3002
	 [>] Connnected
	 [i] Server Cert
	-----BEGIN CERTIFICATE-----
	...
	-----END CERTIFICATE-----
	...
	 [>] recv 3009 user1=0 user2=0 len=47
	{
		"id": "900395798357985798375972",
		"name": "Cleaner",
		"status": "Sleeping",
		"settings": {
			"EcoMode": false,
			"Language": "eng",
			"Mute": false
		}
	}

More usage:

    usage: purei9_unofficial [-h] [-d] [-o {table,json}] {cloud,local} ...

    positional arguments:
    {cloud,local}         command
        cloud               Connect to electrolux purei9 cloud (old API).
        local               Connect to robot(s) via local network.

    optional arguments:
    -h, --help            show this help message and exit
    -d, --debug           enable debug logging
    -o {table,json}, --output {table,json}
                            output format
                            

    usage: purei9_unofficial cloud [-h] [-v {1,2}] (-c CREDENTIALS | -t TOKEN) {status,start,home,maps} ...

    positional arguments:
    {status,start,home,maps}
                            subcommand, default=status
        status              Get status of all robots.
        start               Tell a robot to start cleaning.
        home                Tell a robot to go home.
        maps                Download maps (experimental).

    optional arguments:
    -h, --help            show this help message and exit
    -v {1,2}, --apiversion {1,2}
                            Cloud API version, v1=purei9, v2=wellbeing

    Credentials:
    One of these is required.

    -c CREDENTIALS, --credentials CREDENTIALS
                            elecrolux cloud credentails in username:password format
    -t TOKEN, --token TOKEN
                            electrolux v2 API token

                            
    purei9_unofficial local [-h] [-a ADDRESS] [-l LOCALPW] {find,status,start,home} ...

    positional arguments:
    {find,status,start,home}
                            subcommand, default=find
        find                Find all robots in the local subnet.
        status              Get status of the robot.
        start               Tell the robot to start cleaning.
        home                Tell the robot to go home.

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

If you want to use the library instead, here is some example code which assumes (1) you only have one robot in your electrolux account and (2) the robot is located in the same network as the computer you are running the code on. You can also have a look at the [CLI implementation](./src/purei9_unofficial/__main__.py).

    from purei9_unofficial.cloud import CloudClient
    from purei9_unofficial.local import RobotClient, find_robots

    # Get the list of robots in the cloud account
    cloudclient  = CloudClient("account_email", "account_password")
    robots       = cloudclient.getRobots()

    # Get the local robot password to authenticate at our robot
    localpw      = robots[0].getlocalpw()

    # Get the robots in our network
    local_robots = find_robots()

    # Create a RobotClient to connect to it
    robotclient  = RobotClient(local_robots[0].address)
    robotclient.connect(localpw)

    # Gets the status
    print(robotclient.getstatus())

