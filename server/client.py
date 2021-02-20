import socket

c = socket.socket()

c.connect(("localhost", 9998))

print(c.recv(1024).decode())