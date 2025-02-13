import re

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, MSG_DONTWAIT
from threading import Thread
from time import sleep

HOSTNAME = "nusa.foo.net"
TLD_PATTERN = re.compile(r"\.(com|org|net|edu|io|app)$")
DOMAIN_PATTERN = re.compile(r"@[a-zA-Z0-9]+\.")
USER_PATTERN = re.compile(r".+")
CR_LF = '\r\n'

def valid_email_address(connectionSocket: socket, address: str):
    if address.count("@") != 1:
        connectionSocket.sendall(f"550 INVALID EMAIL{CR_LF}".encode())
        return False
    
    username, domain = address.split("@")

    if re.match(USER_PATTERN, username) is None:
        connectionSocket.sendall(f"550 INVALID USERNAME{CR_LF}".encode())
        return False
    if re.match(DOMAIN_PATTERN, "@" + domain) is None:
        connectionSocket.sendall(f"550 INVALID DOMAIN{CR_LF}".encode())
        return False
    if re.search(TLD_PATTERN, domain) is None:
        connectionSocket.sendall(f"550 INVALID TLD{CR_LF}".encode())
        return False
    return True

def extract_headers():
    pass

def handle_data(connectionSocket: socket):
    response = connectionSocket.recv(1024).decode()
    data = response.split(CR_LF)

    while data[-2] != ".":
        print(response)
        response = connectionSocket.recv(1024).decode()
        data += response.split(CR_LF)

    print(data)
    return True

def handle_connection(connectionSocket: socket, addr):
    connectionSocket.sendall(f"220 {HOSTNAME}{CR_LF}".encode())
    response = connectionSocket.recv(1024).decode()
    # if response != f"EHLO {HOSTNAME}":
    #     connectionSocket.sendall(f"550 Error in EHLO{CR_LF}".encode())
    #     connectionSocket.close()
    #     return
    # else:
    connectionSocket.sendall(f"502 OK{CR_LF}".encode())
    
    response = connectionSocket.recv(1024).decode()
    # if response != f"HELO {HOSTNAME}":
    #     connectionSocket.sendall(f"550 Error in HELO{CR_LF}".encode())
    #     connectionSocket.close()
    #     return
    # else:
    connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    # Sender
    response = connectionSocket.recv(1024).decode()
    address = response.split(">")[0].split("<")[-1]
    if not valid_email_address(connectionSocket, address):
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    # Recipient
    response = connectionSocket.recv(1024).decode()
    address = response.split(">")[0].split("<")[-1]
    if not valid_email_address(connectionSocket, address):
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    response = connectionSocket.recv(1024).decode()
    if response != "DATA" + CR_LF:
        connectionSocket.sendall(f"550 Expected DATA{CR_LF}".encode())
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"354 OK{CR_LF}".encode())
    print("HERE!")
    if not handle_data(connectionSocket):
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    response = connectionSocket.recv(1024).decode()
    if response != "QUIT" + CR_LF:
        connectionSocket.sendall(f"550 Expected QUIT{CR_LF}".encode())
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"221 OK{CR_LF}".encode())

# Create a TCP socket that listens to port 9000 on the local host
welcomeSocket = socket(AF_INET, SOCK_STREAM)
welcomeSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
welcomeSocket.bind(("", 9000))
welcomeSocket.listen(4)    # Max backlog 4 connections

print ('Server is listening on port 9000')

while True:
    connectionSocket, addr = welcomeSocket.accept()
    print ("Accept a new connection", addr)
    handle_connection(connectionSocket, addr)


# Read AT MOST 1024 bytes from the socket
# decode(): converts bytes to text
# encode(): convert text to bytes
text = connectionSocket.recv(1024).decode()
print (f"Incoming text is {text}")
connectionSocket.sendall("This is a sample text".encode())
connectionSocket.close()

welcomeSocket.close()
print("End of server")