import socket
import threading

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(("localhost", 9999))

def get_nick_user():
    global nick_in
    global username_in
    global hostname_in
    global portname_in
    global realname_in
    loop = True
    while loop:
        nick_in = input("Please enter your NICK: ")
        c.send(bytes("NICK " + nick_in, "utf-8"))
        print("Got reply: ")
        nick_response = c.recv(1024).decode()
        if nick_response == "Invalid Request":
            print(nick_response)
            print("Please enter valid Nick credentials")
        elif(len(nick_in) > 9):
            print("NICK cannot contain more than 9 characters.")
        else:
            loop = False
            print(nick_response)
            print(f"NICK: %s, successfully registered." % (nick_in))

    loop = True
    while loop:
        print("Please enter your USER credentials: ")
        username_in = input("Please enter your Username: ")
        hostname_in = input("Please enter your host name: ")
        portname_in = input("Please enter your port name: ")
        realname_in = input("Please enter your real name: ")

        c.send(bytes(f"USER %s %s %s :%s" % (username_in, hostname_in, portname_in, realname_in), "utf-8"))
        print("Got reply: ")
        user_response = c.recv(1024).decode()
        if user_response == "Invalid Request":
            print(user_response)
            print("Please enter valid user credentials")
        else:
            loop = False
            print(user_response)
            print(
                f"USER: %s %s %s :%s, successfully registered." % (username_in, hostname_in, portname_in, realname_in))

def print_banner():
    banner_file = open("banner.txt", "r")
    print(banner_file.read())

def receive_msg():
    while True:
        msg = c.recv(1024).decode()
        if "{'Command': 'PRIVMSG'," in msg:
            continue
        print(msg)

print_banner()
get_nick_user()
while True:
    receive_thread = threading.Thread(target=receive_msg).start()
    command = input()
    c.send(bytes(f"PRIVMSG #global :[%s] - " % (nick_in) + command, "utf-8"))


