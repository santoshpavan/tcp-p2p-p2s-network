import socket
import threading
import os
import sys
import time
import copy

peer_list = {}
rfc_list = {}
peer_port_list = {}


def peer_con(connection, client_address):
	try:
		print('Connection from', client_address)
		peer_list[client_address] = []
		# Receive the data in small chunks and retransmit it
		while True:
			response = 'P2P-CI/1.0 200 OK\n'
			data = connection.recv(4096)
			print('Received {!r}'.format(data))
			if data:
				req = data.decode('utf-8').split('\n')
				if req[0].split(' ')[0] == 'ADD':
					rfc_num = req[0].split(' ')[2]
					if rfc_num not in rfc_list:
						rfc_list[rfc_num] = []
					rfc_list[rfc_num].append((req[1].split(': ')[1],req[2].split(': ')[1],req[3].split(': ')[1], client_address))
					print(rfc_list)	

				elif req[0].split(' ')[0] == 'LOOKUP':
					rfc_num = req[0].split(' ')[2]
					if rfc_num in rfc_list:
						for x in rfc_list[rfc_num]:
							response+= 'RFC '+rfc_num+' '+x[2]+' '+x[0]+' '+x[1]+'\n'
					else:
						response = '404 NOT FOUND\n'
				
				elif req[0].split(' ')[0] == 'LIST':
					for rfc_num in rfc_list:
						for x in rfc_list[rfc_num]:
							response+= 'RFC '+rfc_num+' '+x[2]+' '+x[0]+' '+x[1]+'\n'

				elif req[0].split(' ')[0] == 'EXIT':
					#print("In Exit")
					del peer_list[client_address]
					rfc_list_temp = copy.copy(rfc_list)
					for rfc_num in rfc_list_temp:
						for x in rfc_list_temp[rfc_num]:
							if client_address == x[3]:
								rfc_list[rfc_num].remove(x)
								if rfc_list[rfc_num] == []:
									del rfc_list[rfc_num]
					response += "Client connection closed " + str(client_address)
					print(response)
					message = bytes(response,'utf-8')
					connection.sendall(message)
					time.sleep(1)
					break
				
				else :
					response = '400 Bad Request\n'
			else:
				print('No data from', client_address)
				response = '400 Bad Request\n'
			print(response)
			message = bytes(response,'utf-8')
			connection.sendall(message)
			time.sleep(1)

	finally:
		# Clean up the connection
		connection.close()


# Create a TCP/IP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('', 7734)
print('starting up on {} port {}'.format(*server_address))
s.bind(server_address)

# Listen for incoming connections
s.listen(3)

while True:
	# Wait for a connection
	print('Waiting for a connection')
	connection, client_address = s.accept()
	#peer_con(connection, client_address)

	st = threading.Thread(target = peer_con,args=(connection, client_address,))
	st.start()






