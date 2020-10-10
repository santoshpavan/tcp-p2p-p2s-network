import socket
import threading

PORT_NUMBER = 7734
BACKLOG_CONNECTIONS = 5
BUFFER_SIZE = 16
VERSION = "P2P-CI/1.0"
STATUS_CODE = [200, 400, 404, 505]
PHRASE = ["OK", "Bad Request", "Not Found", "P2P-CI Version Not Supported"]

# Lists of connected peers
peer_list = []
# List of RFCs located within peers
rfc_list = []

def addRequestHandler(hostname, port_number, rfc_title, rfc_number):
    peer_list.append([hostname, port_number])
    rfc_list.append([rfc_number, rfc_title, hostname])
    response = f"{VERSION} {STATUS_CODE[0]} {PHRASE[0]}\n"
    response += f"RFC {rfc_number} {rfc_title} ICP {hostname} {port_number}"
    return response

def lookupRequestHandler(hostname, port_number, rfc_title, rfc_number):
    response = ""
    for ele in rfc_list:
        if ele[0] == rfc_number and ele[2] == rfc_title:
            response += f"{rfc_number} {rfc_title} {hostname} {port_number}\n"
    if len(response) == 0:
        index = 2
    response = f"{VERSION} {STATUS_CODE[index]} {PHRASE[index]}"
    return response

def listallRequestHandler():
    response = ""
    for ele in rfc_list:
        response += f"{ele[0]} {ele[1]} {ele[2]} {ele[3]}\n"
    if len(response) == 0:
        index = 2
    response = f"{VERSION} {STATUS_CODE[index]} {PHRASE[index]}\n" + response
    return response

def invalidRequestHandler():
    response = f"{VERSION} {STATUS_CODE[1]} {PHRASE[1]}"
    return response

def collectMessage(peerSocket):
    full_message = ""
    while True:   
        buffer = peerSocket.recv(BUFFER_SIZE)
        if len(buffer) == 0:
            break
        full_message += buffer
    return full_message

def peerHandler(peerSocket, peerAddress):
    message = collectMessage(peerSocket).decode()
    message_lines = message.splitlines()

    request_type = message_lines[0].split()[0]
    hostname = message_lines[1].split(":")[1].strip()
    port_number = int(message_lines[2].split(":")[1].strip())

    if request_type == "ADD":
        rfc_title = message_lines[3].split(":")[1].strip()
        rfc_number = int(message_lines[0].split("RFC")[1].split()[0])
        addRequestHandler(hostname, port_number, rfc_title, rfc_number)
    elif request_type == "LOOKUP":
        rfc_title = message_lines[3].split(":")[1].strip()
        rfc_number = int(message_lines[0].split("RFC")[1].split()[0])
        lookupRequestHandler(hostname, port_number, rfc_title, rfc_number)
    elif request_type == "LIST" and message_lines[0].split()[1]=="ALL":
        listallRequestHandler()
    else:
        invalidRequestHandler()

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((socket.gethostname(), PORT_NUMBER))
serverSocket.listen(BACKLOG_CONNECTIONS)

# waiting for connections
while True:
    # establishing connection with the peer
    peerSocket, peerAddress = serverSocket.accept()
    # create a new thread to handle this connection
    peerThread = threading.Thread(target=peerHandler, args=(peerSocket, peerAddress))

serverSocket.close()