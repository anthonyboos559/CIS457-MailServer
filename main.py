import re

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread

HOSTNAME = "nusa.foo.net"
TLD_PATTERN = re.compile(r"\.(com|org|net|edu|io|app)$")
DOMAIN_PATTERN = re.compile(r"@[a-zA-Z0-9]+\.")
USER_PATTERN = re.compile(r".+")
CR_LF = '\r\n'

def valid_email_address(connectionSocket: socket, address: str):
    if address.count("@") != 1:
        connectionSocket.sendall(f"553 INVALID EMAIL{CR_LF}".encode())
        return False
    
    username, domain = address.split("@")

    if re.match(USER_PATTERN, username) is None:
        connectionSocket.sendall(f"553 INVALID USERNAME{CR_LF}".encode())
        return False
    if re.match(DOMAIN_PATTERN, "@" + domain) is None:
        connectionSocket.sendall(f"553 INVALID DOMAIN{CR_LF}".encode())
        return False
    if re.search(TLD_PATTERN, domain) is None:
        connectionSocket.sendall(f"553 INVALID TLD{CR_LF}".encode())
        return False
    return True

def handle_data(connectionSocket: socket):
    response = connectionSocket.recv(1024).decode()
    data = response.split(CR_LF)
    headers = {}
    prev_head = None
    for header in data:
        if header == "":
            break
        head = header.split(":")
        if len(head) > 2:
            headers[head[0]] = ":".join(head[1:])
        elif len(head) == 1:
            if prev_head is None:
                connectionSocket.sendall(f"451 Error processing headers{CR_LF}".encode())
                return
            else:
                headers[prev_head] = headers[prev_head] + head[0]
        else:
            headers[head[0]] = head[1]
        prev_head = head[0] # For use when the header is broken up with a CRLF (5 recipients)
    
    subject = headers.get("Subject", "")
    if subject == "":
        connectionSocket.sendall(f"451 Subject cannot be blank{CR_LF}".encode())
        return

    while data[-2] != ".":
        response = connectionSocket.recv(1024).decode()
        data += response.split(CR_LF)

    print(CR_LF.join(data[:-3]))
    return True

def handle_connection(connectionSocket: socket, addr):
    connectionSocket.sendall(f"220 {HOSTNAME}{CR_LF}".encode())

    #EHLO
    response = connectionSocket.recv(1024).decode()
    connectionSocket.sendall(f"502 OK{CR_LF}".encode())
    
    #HELO
    response = connectionSocket.recv(1024).decode()
    connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    # Sender adddress
    response = connectionSocket.recv(1024).decode()
    address = response.split(">")[0].split("<")[-1]
    if not valid_email_address(connectionSocket, address):
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    # Recipient addresses
    response = connectionSocket.recv(1024).decode()
    address = response.split(">")[0].split("<")[-1]
    if not valid_email_address(connectionSocket, address):
        connectionSocket.close()
        return
    else:
        recipients = 1
        connectionSocket.sendall(f"250 OK{CR_LF}".encode())
    
    response = connectionSocket.recv(1024).decode()
    while "RCPT TO" in response:
        print(response)
        address = response.split(">")[0].split("<")[-1]
        if not valid_email_address(connectionSocket, address):
            connectionSocket.close()
            return
        else:
            recipients += 1
            if recipients <= 5:
                connectionSocket.sendall(f"250 OK{CR_LF}".encode())
            else:
                connectionSocket.sendall(f"550 TOO MANY RECIPIENTS{CR_LF}".encode())
                connectionSocket.close()
                return
        response = connectionSocket.recv(1024).decode()

    if response != "DATA" + CR_LF:
        connectionSocket.sendall(f"550 Expected DATA{CR_LF}".encode())
        connectionSocket.close()
        return
    else:
        connectionSocket.sendall(f"354 OK{CR_LF}".encode())

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
    connectionSocket.close()
    print("Closed connection with", addr)

def main():
    # Create a TCP socket that listens to port 9000 on the local host
    welcomeSocket = socket(AF_INET, SOCK_STREAM)
    welcomeSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    welcomeSocket.bind(("", 9000))
    welcomeSocket.listen(4)    # Max backlog 4 connections

    print ('Server is listening on port 9000')

    while True:
        connectionSocket, addr = welcomeSocket.accept()
        print ("Accept a new connection", addr)
        thread = Thread(target=handle_connection, args=(connectionSocket, addr))
        thread.start()
    
    welcomeSocket.close()

if __name__ == "__main__":
    main()