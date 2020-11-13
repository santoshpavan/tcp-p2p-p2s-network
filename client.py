#Client Code 
import socket
import sys
import threading
import os
import time
import platform

#Function for accepting peer connections
def accept_connection():

	# Listen for incoming connections
	sr.listen(3)

	while True:
		print('Waiting for a connection')
		connection, client_address = sr.accept()
		# New thread to deal with client connection
		st = threading.Thread(target = peer_connection,args=(connection, client_address,))
		st.daemon = True
		st.start()

#Function 
def peer_connection(connection, client_address):
	try:
		print('Connection from', client_address)
		while True:
			response = 'P2P-CI/1.0 200 OK\n'
			data = connection.recv(BUFFER_SIZE)
			print('Received {!r}'.format(data))
			if data:
				req = data.decode('utf-8').split('\n')		# Splitting received data in lines 0, 1, 2 and 3
				if req[0].split(' ')[0] == 'GET':
					rfc_num = req[0].split(' ')[2]		# Splitting line in words spaced by ' '
					rfc_fp = open(path + "/" + rfc_num + "_" + req[2].split(': ')[1], "rb")
					l = rfc_fp.read(BUFFER_SIZE)			
					while True:
						connection.send(l)
						if len(l) < BUFFER_SIZE:
							break
						l = rfc_fp.read(BUFFER_SIZE)
					rfc_fp.close()
					print('Done sending')
			else:
				print('No data from', client_address)
				response = '400 Bad Request\n'
			break
	finally:
		# Clean up the connection
		connection.close() 
				
# Client as Server & Client socket 
# Create TCP/IP sockets
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 	#client
sr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	#server
BUFFER_SIZE = 1024

path = input('Enter path to the RFCs\n')	
rfcs = os.listdir(path)	#RFCs path
upload_port = input('Enter upload port number for client as a server\n') #Upload port number by user
host_ip = input('Enter host IP address\n')	
server_ip = input('Enter centralised server IP address\n')

# Bind the socket to the port
c_as_s_addr = ('', int(upload_port))
sr.bind(c_as_s_addr)

# New thread for listening for incoming connections
st = threading.Thread(target = accept_connection)
st.daemon = True
st.start()

# Connect the socket to the port where the server is listening
server_addr = (server_ip, 7734)
print('Connecting to {} port {}'.format(*server_addr))
c.connect(server_addr)

lookup_list = {}
try:
	for x in rfcs:
			
		# Send data
		file_name = x.split('_')
		uinput = 'ADD RFC ' + file_name[0] + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ upload_port + '\nTitle: '+ file_name[1]
		message = bytes(uinput,'utf-8')
		print('Sending {!r}'.format(message))
		c.sendall(message)
		data = c.recv(BUFFER_SIZE)
		print('Server Response: {!r}'.format(data))
		
	while True:
		# Send data
		uinput = input('Enter your message\n')
		original_message = message = bytes(uinput,'utf-8')
		if message == b'LOOKUP':
			rfc_num = input('Enter RFC number\n')
			uinput = 'LOOKUP RFC ' + str(rfc_num) + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ upload_port
			message = bytes(uinput,'utf-8')
			print('Sending {!r}'.format(message))
			c.sendall(message)
			data = c.recv(BUFFER_SIZE)
			info = data.decode('utf-8')
			if "OK" in info:
				lines = info.split('\n')
				for line in lines[1:]:
					temp = line.split(" ")
					if len(temp) <= 4:
						continue
					if rfc_num not in lookup_list:
						lookup_list[rfc_num] = []
					lookup_list[rfc_num].append((temp[2], temp[3], temp[4]))
		elif message == b'LIST':
			uinput = 'LIST ALL P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ upload_port
			message = bytes(uinput,'utf-8')
			print('Sending {!r}'.format(message))
			c.sendall(message)
			data = c.recv(BUFFER_SIZE)
		elif message == b'GET':
			rfc_num = input('Enter RFC number\n')
			if rfc_num not in lookup_list:
				print("Please do rfc look up first")
				continue;
			peer_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #peer_client
			peer_ip = lookup_list[rfc_num][0][1]
			peer_port = lookup_list[rfc_num][0][2]
			rfc_title = lookup_list[rfc_num][0][0]
			uinput = 'GET RFC ' + rfc_num + ' P2P-CI/1.0\nHost:' + host_ip + "\nTitle: " + rfc_title + '\nOS: ' + platform.system() + platform.release() 
			message = bytes(uinput,'utf-8')
			peer_address = (peer_ip, int(peer_port) )
			print('Connecting to {} port {}'.format(*peer_address))
			peer_s.connect(peer_address)
			peer_s.sendall(message)

			fp = open(path + "/" + rfc_num + "_" + rfc_title, "wb")
			while True:
				data = peer_s.recv(BUFFER_SIZE)
				fp.write(data)
				if len(data) < BUFFER_SIZE:
					break
			print('Received file\n')			
			uinput = 'ADD RFC ' + rfc_num + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ upload_port + '\nTitle: '+ rfc_title
			message = bytes(uinput,'utf-8')
			print('Sending {!r}'.format(message))
			c.sendall(message)
			data = c.recv(BUFFER_SIZE)

			fp.close() 
		elif message == b'EXIT':
			uinput = 'EXIT P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ upload_port
			message = bytes(uinput,'utf-8')
			print('Sending {!r}'.format(message))
			c.sendall(message)
			data = c.recv(BUFFER_SIZE)
		else:
			print('Sending {!r}'.format(message))
			c.sendall(message)
			data = c.recv(BUFFER_SIZE)
		print('Server Response: {}'.format(data.decode('utf-8')))
		
		if original_message == b'EXIT':
			print("closing the connection")
			break

finally:
	print('closing socket')
	c.close()
	sys.exit()
