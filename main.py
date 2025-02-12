from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

# Create a TCP socket that listens to port 9000 on the local host
welcomeSocket = socket(AF_INET, SOCK_STREAM)
welcomeSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
welcomeSocket.bind(("", 9000))
welcomeSocket.listen(4)    # Max backlog 4 connections

print ('Server is listening on port 9000')
connectionSocket, addr = welcomeSocket.accept()
print ("Accept a new connection", addr)

# Read AT MOST 1024 bytes from the socket
# decode(): converts bytes to text
# encode(): convert text to bytes
text = connectionSocket.recv(1024).decode()
print (f"Incoming text is {text}")
connectionSocket.sendall("This is a sample text".encode())
connectionSocket.close()

welcomeSocket.close()
print("End of server")