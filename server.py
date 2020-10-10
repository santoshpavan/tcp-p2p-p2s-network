import socket
import threading
import re
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

PORT_NUMBER = 7734
BACKLOG_CONNECTIONS = 5
BUFFER_SIZE = 2048
VERSION = "P2P-CI/1.0"
STATUS_CODE = [200, 400, 404, 505]
PHRASE = ["OK", "Bad Request", "Not Found", "P2P-CI Version Not Supported"]

# does not check for validity of hostname
ADD_SYNTAX = r"ADD\sRFC\s[0-9]+\sP2P-CI\/1.0\nHost:\s?.+\nPort:\s?[0-9]+\nTitle:\s?.+\n?"
LOOKUP_SYNTAX = r"LOOKUP\sRFC\s[0-9]+\sP2P-CI\/1.0\nHost:\s?.+\nPort:\s?[0-9]+\nTitle:\s?.+\n?"
LISTALL_SYNTAX = r"LIST ALL\sP2P-CI\/1.0\nHost:\s?.+\nPort:\s?[0-9]+\n?"

# Lists of connected peers
peer_list = []
# List of RFCs located within peers
rfc_list = []

def addRequestHandler(hostname, port_number, rfc_title, rfc_number):
    print("add")
    peer_list.append([hostname, port_number])
    rfc_list.append([rfc_number, rfc_title, hostname])
    response = f"{VERSION} {STATUS_CODE[0]} {PHRASE[0]}\n"
    response += f"RFC {rfc_number} {rfc_title} {hostname} {port_number}"
    return response

def lookupRequestHandler(hostname, port_number, rfc_title, rfc_number):
    print("lookup")
    response = ""
    for ele in rfc_list:
        if ele[0] == rfc_number and ele[2] == rfc_title:
            response += f"{rfc_number} {rfc_title} {hostname} {port_number}\n"
    if len(response) == 0:
        # not found
        response = invalidRequestHandler(2)
    else:
        # okay
        response = f"{VERSION} {STATUS_CODE[0]} {PHRASE[0]}\n" + response
    return response

def listallRequestHandler(hostname, port_number):
    response = ""
    
    print("listall")
    for ele_rfc in rfc_list:
        for ele_peer in peer_list:
            if ele_rfc[2] == ele_peer[0]:
                response += f"{ele_peer[0]} {ele_peer[1]} {ele_rfc[0]} {ele_rfc[1]}\n"
    if len(response) == 0:
        # not found
        response = invalidRequestHandler(2)
    else:
        # okay
        response = f"{VERSION} {STATUS_CODE[0]} {PHRASE[0]}\n" + response
    return response

def closeConnectionHandler(hostname, port_number):
    # deleting peer details from the list
    print("close...")
    for ele in peer_list:
        if ele[0] == hostname:
            peer_list.remove(ele)
    for ele in rfc_list:
        if ele[0] == hostname:
            rfc_list.remove(ele)
    return "-1"

def invalidRequestHandler(index):
    print("invalid...")
    response = f"{VERSION} {STATUS_CODE[index]} {PHRASE[index]}\n"
    return response

# def collectMessage(peer_socket):
#     print("collecting message...")
#     full_message = ""
#     while True:   
#         buffer = peer_socket.recv(BUFFER_SIZE).decode()
#         if len(buffer) < 1:
#             break
#         print(buffer)
#         full_message += buffer
#     print("collection done...")
#     return full_message

def peerHandler(peer_socket, peer_address):
    # message = collectMessage(peer_socket)
    print("\n----\n")
    logging.debug("thread started")
    while True:
        message = peer_socket.recv(BUFFER_SIZE).decode()
        
        print(message+"\n")
        message_lines = message.splitlines()
        
        if len(message_lines) < 2:
            response = invalidRequestHandler(1)

        elif message_lines[0].split()[-1].strip() != VERSION:
            response = invalidRequestHandler(3)

        else:
            request_type = message_lines[0].split()[0].strip()
            hostname = message_lines[1].split(":")[1].strip()
            port_number = int(message_lines[2].split(":")[1].strip())

            if request_type == "ADD" and re.match(ADD_SYNTAX, message):
                rfc_title = message_lines[3].split(":")[1].strip()
                rfc_number = int(message_lines[0].split("RFC")[1].split()[0])
                response = addRequestHandler(hostname, port_number, rfc_title, rfc_number)

            elif request_type == "LOOKUP" and re.match(LOOKUP_SYNTAX, message):
                rfc_title = message_lines[3].split(":")[1].strip()
                rfc_number = int(message_lines[0].split("RFC")[1].split()[0])
                response = lookupRequestHandler(hostname, port_number, rfc_title, rfc_number)

            elif request_type == "LIST" and re.match(LISTALL_SYNTAX, message):
                response = listallRequestHandler(hostname, port_number)

            elif request_type == "END":
                response = closeConnectionHandler(hostname, port_number)

            else:
                response = invalidRequestHandler(1)
        
        if response == "-1":
            print("Connection terminating")
            response = "Connection Terminated"
            peer_socket.send(response.encode())
            peer_socket.close()
            break

        else:
            print("sending response")
            peer_socket.send(response.encode())
    logging.debug("Thead ended")

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((socket.gethostname(), PORT_NUMBER))
print(f"Listening on port {PORT_NUMBER}...")
serverSocket.listen(BACKLOG_CONNECTIONS)

# waiting for connections
while True:
    # establishing connection with the peer
    peer_socket, peer_address = serverSocket.accept()
    print(f"Connection from {peer_address} established...")
    # create a new thread to handle this connection
    peerThread = threading.Thread(target=peerHandler, args=(peer_socket, peer_address,))
    peerThread.start()
    logging.debug("main thread")
    print("all done!-----")

serverSocket.close()