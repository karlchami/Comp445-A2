import socket

c = socket.socket()
c.connect(("localhost", 9998))
while True:
    command = input("Please enter your command: ")
    c.send(bytes(command, "utf-8"))
    print("Got reply: ")
    print(c.recv(1024).decode())
