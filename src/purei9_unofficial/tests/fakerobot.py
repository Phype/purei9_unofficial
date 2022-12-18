import socket
import select
import sys

from ..message import BinaryMessage, port_tcp, port_udp

ADDR = "0.0.0.0"

try:
	sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	sock_udp.bind((ADDR, port_udp))
	sock_tcp.bind((ADDR, port_tcp))

	sock_tcp.listen(1)

	# pkt, addr = sock_udp.recvfrom(0xFFFF)

	while True:
		rlist, wlist, xlist = select.select([sock_udp, sock_tcp], [], [], 10)

		if len(rlist) > 0:
			if rlist[0] == sock_tcp:
				sock_client, client_addr = sock_tcp.accept()
				print("TCP connection from ", client_addr)
				sock_client.close()

			if rlist[0] == sock_udp:
				pkt, client_addr = sock_udp.recvfrom(0xFFFF)
				print("UDP message from ", client_addr)

				msg = BinaryMessage.from_wire(pkt)

				print(msg)
				if msg.minor == BinaryMessage.MSG_GET_ADDRESS_REQUEST:

					msg = BinaryMessage.StringMap(BinaryMessage.MSG_GET_ADDRESS_RESPONSE, {
						"RobotID": "000000000000000000000000",
						"RobotName": "fakerobot.py"
					})
					
					sock_udp.sendto(msg.to_wire(), client_addr)

finally:
	sock_udp.close()
	sock_tcp.close()





