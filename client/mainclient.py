import socket

c = socket.socket()
c.connect(("localhost", 9999))
banner = open('banner.txt', 'r')
read_banner = banner.read()
print (read_banner)
banner.close()

while True:
    command = input("Please enter your command: ")
    c.send(bytes(command, "utf-8"))
    print("Got reply: ")
    print(c.recv(1024).decode())