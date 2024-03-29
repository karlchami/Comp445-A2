import socket
import select
import sys
import ast
import argparse


class IRCClient:

    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.nickname = str()
        self.username = str()
        self.fullname = str()
        self.servername = "localserver"
        self.isConnected = False
        self.client_socket = None

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        return self.client_socket

    def disconnect_from_server(self):
        self.client_socket.send(bytes("QUIT", "utf-8"))
        if "Success" in ast.literal_eval(self.client_socket.recv(1024).decode())["Response_Status"]:
            self.isConnected = False
            self.add_prompt("Leaving server. \n")
            self.client_socket.close()
            exit()

    def process_input(self, msg):
        if msg.lower().startswith("/connect") and not self.isConnected:
            split_connect_command = msg.split(" ")
            if len(split_connect_command) == 4:
                self.add_prompt(msg)
                self.nickname = split_connect_command[1]
                self.username = split_connect_command[2]
                self.fullname = split_connect_command[3]
                if len(self.nickname) > 9:
                    self.add_prompt("NICK cannot exceed 9 characters. \n")
                    return None
                self.create_user_connection()
        if msg.lower().startswith("/modify") and self.isConnected:
            split_modify_command = msg.split(" ")
            if len(split_modify_command) == 3:
                if len(split_modify_command[1]) <=9 and len(split_modify_command[2]) <= 9:
                    self.modify_nickname(split_modify_command[1], split_modify_command[2])
                else:
                    self.add_prompt("NICK cannot exceed 9 characters. \n")
                    return None
        if msg.lower().startswith("/msg") and self.isConnected:
            self.send_channel_message(msg)
        if msg.lower().startswith("/quit") and self.isConnected:
            self.disconnect_from_server()

    def modify_nickname(self, old, new):
        modify_command = f"NICK {old} {new}"
        self.client_socket.send(bytes(modify_command, "utf-8"))
        modify_reply = self.client_socket.recv(1024).decode()
        modify_decoded_message = ast.literal_eval(modify_reply)
        if "Success" in modify_decoded_message["Response_Status"]:
            self.add_prompt(f"Nickname {old} changed to {new}")
            self.nickname = new
        elif "ERR_NICKCOLLISION" in modify_decoded_message["Response_Status"]:
            self.add_prompt("Wrong prompt parameters or potential duplicate. \n")

    def create_user_connection(self):
        nick_command = user_command = str()
        if hasattr(self, "nickname"):
            nick_command = "NICK " + self.nickname
        if hasattr(self, "username") and hasattr(self, "server_host") and hasattr(self, "servername") and hasattr(self, "fullname"):
            user_command = f"USER {self.username} {self.server_host} {self.servername} :{self.fullname}"
        if not self.client_socket:
            self.connect_to_server()
        if nick_command and user_command:
            self.client_socket.send(bytes(nick_command, "utf-8"))
            nick_reply = self.client_socket.recv(1024).decode()
            nick_decoded_message = ast.literal_eval(nick_reply)
            self.client_socket.send(bytes(user_command, "utf-8"))
            user_reply = self.client_socket.recv(1024).decode()
            user_decoded_response_message = ast.literal_eval(user_reply)
            if "Joined" in nick_decoded_message["Response_Status"] or "Joined" in user_decoded_response_message["Response_Status"]:
                self.isConnected = True
                self.add_prompt(f"User {self.nickname} successfully joined #global channel. \n")
            elif "ERR_NICKCOLLISION" in nick_decoded_message["Response_Status"] or "ERR_ALREADYREGISTRED" in user_decoded_response_message["Response_Status"]:
                self.add_prompt("Wrong prompt parameters or potential duplicate. \n")

    def send_channel_message(self, msg):
        privmsg_command = "PRIVMSG #global :" + msg[5:]
        self.client_socket.send(bytes(privmsg_command, "utf-8"))
        self.client_socket.recv(1024).decode()

    def receive_message(self, msg):
        response = msg.decode().split(";")
        if len(response) == 2:
            self.add_received_msg(response[0], response[1])
        else:
            self.add_prompt(f"{response[0]} left the server \n")

    def add_msg(self, msg):
        sys.stdout.write(f"[{self.nickname}] {msg}")
        sys.stdout.flush()

    @staticmethod
    def add_received_msg(user, msg):
        sys.stdout.write(f"[{user}] {msg}")
        sys.stdout.flush()

    @staticmethod
    def add_prompt(msg):
        sys.stdout.write(f"[Prompt] {msg}")
        sys.stdout.flush()

    def get_socket(self):
        return self.client_socket

    def is_client_connected(self):
        return self.isConnected


if __name__ == '__main__':

    # Parsing script arguments from CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Target port to use', required=True)
    args = vars(parser.parse_args())

    port = int(args['port'])

    client = IRCClient("localhost", port)

    banner = open("banner.txt", "r").read()
    print(banner)

    while not client.is_client_connected():
        message = sys.stdin.readline()
        client.process_input(message)

    client_socket = client.get_socket()
    sockets_list = [sys.stdin, client_socket]

    while True:
        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])

        for socks in read_sockets:
            if socks == client_socket:
                message = socks.recv(2048)
                client.receive_message(message)
            else:
                message = sys.stdin.readline()
                client.process_input(message)
