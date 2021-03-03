import socket
import time
import threading

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(("localhost", 9999))

nick = "n2"
c.send(bytes("NICK "+ nick, "utf-8"))
print("Got reply: ")
print(c.recv(1024).decode())

time.sleep(2)

username = "user2"
hostname = "host2"
portname = "port2"
realname = "Name2"
c.send(bytes(f"USER %s %s %s :%s"%(username,hostname,portname,realname), "utf-8"))
print("Got reply: ")
print(c.recv(1024).decode())

def receive_msg():
    while True:
        msg = c.recv(1024).decode()
        if "{'Command': 'PRIVMSG'," in msg:
            continue
        print(msg)

while True:
    receive_thread = threading.Thread(target=receive_msg).start()
    command = input()
    c.send(bytes(f"PRIVMSG #global :[%s] - " % (nick) + command, "utf-8"))




