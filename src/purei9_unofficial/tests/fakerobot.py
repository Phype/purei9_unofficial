import socket
import select
import sys
import ssl
import traceback
import struct
import os

from ..message import BinaryMessage, port_tcp, port_udp

ADDR = "0.0.0.0"

ROBOTID = "000000000000000000000000"
ROBOTNAME = "fakerobot.py"

try:
	ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

	print(" + Invoking OpenSSL to generate self-sogned cert\n")

	os.system('printf "\n\n\n\n\n\n\n\n\n" | openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -sha256 -days 3605 -nodes')
	ctx.load_cert_chain('/tmp/cert.pem', '/tmp/key.pem')

	print("\n\n + Certificate loaded")

	sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	sock_udp.bind((ADDR, port_udp))
	sock_tcp.bind((ADDR, port_tcp))

	sock_tcp.listen(1)

	print(" + Socket open")

	# pkt, addr = sock_udp.recvfrom(0xFFFF)

	while True:
		rlist, wlist, xlist = select.select([sock_udp, sock_tcp], [], [], 10)

		if len(rlist) > 0:
			if rlist[0] == sock_tcp:
				sock_client, client_addr = sock_tcp.accept()
				print(" > TCP connection from ", client_addr)

				sock_client = ctx.wrap_socket(sock_client, server_side=True).makefile("rwb")

				try:
					while True:
						msg = BinaryMessage.from_stream(sock_client)
						
						print(" > ", msg)

						if msg.minor == BinaryMessage.MSG_HELLO:
							msg = BinaryMessage.Text(BinaryMessage.MSG_HELLO, ROBOTID, 2016100701)

						elif msg.minor == BinaryMessage.MSG_LOGIN:
							msg = BinaryMessage.HeaderOnly(BinaryMessage.MSG_LOGIN, 1)

						elif msg.minor == BinaryMessage.MSG_GET_CAPABILITIES_REQUEST:
							msg = BinaryMessage.Text(BinaryMessage.MSG_GET_CAPABILITIES_REQUEST, '{"Capabilities": {}}')

						elif msg.minor == BinaryMessage.MSG_GETSTATUS:
							msg = BinaryMessage.HeaderOnly(BinaryMessage.MSG_GETSTATUS, 10)

						elif msg.minor == BinaryMessage.MSG_GET_POWER_MODE_REQUEST:
							msg = BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_POWER_MODE_REQUEST, 2)

						elif msg.minor == BinaryMessage.MSG_GET_BATTERY_STATUS_REQUEST:
							msg = BinaryMessage.HeaderOnly(BinaryMessage.MSG_GET_BATTERY_STATUS_REQUEST, 5)

						elif msg.minor == BinaryMessage.MSG_GETFIRMWARE:
							msg = BinaryMessage.StringMap(BinaryMessage.MSG_GETFIRMWARE, {
								"FirmwareVersion": "0.00"
							})


						elif msg.minor == BinaryMessage.MSG_PING:
							msg = BinaryMessage.HeaderOnly(BinaryMessage.MSG_PING)
						else:
							pass

						print(" < ", msg)

						pkt = msg.to_wire()
						sock_client.write(pkt)
						sock_client.flush()

				except:
					traceback.print_exc()
				finally:
					sock_client.close()

			if rlist[0] == sock_udp:
				pkt, client_addr = sock_udp.recvfrom(0xFFFF)
				print(" > UDP message from ", client_addr)

				msg = BinaryMessage.from_wire(pkt)

				print(" < ", msg)
				if msg.minor == BinaryMessage.MSG_GET_ADDRESS_REQUEST:

					msg = BinaryMessage.StringMap(BinaryMessage.MSG_GET_ADDRESS_RESPONSE, {
						"RobotID": ROBOTID,
						"RobotName": ROBOTNAME
					})
					
					sock_udp.sendto(msg.to_wire(), client_addr)

finally:
	sock_udp.close()
	sock_tcp.close()





