import socket

# IPV4 and TCP by default
s = socket.socket()
print("Socket Created")

# Bind socket to IP and port number
s.bind(("localhost", 9998))

# Buffer for 3 client connections
s.listen(3)
print("Waiting for connections")

while True:
    c, address = s.accept()
    print("Client connected with ", address)
    c.send(bytes("Welcome to my connection", "utf-8"))
    c.close()

