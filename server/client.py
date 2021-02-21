import socket

c = socket.socket()
c.connect(("localhost", 9998))
nickname = input("Please enter your nickname: ")
c.send(bytes(nickname, "utf-8"))
print(c.recv(1024).decode())
