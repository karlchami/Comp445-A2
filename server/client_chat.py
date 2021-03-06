import socket
import select
import sys
import ast


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

    def get_socket(self):
        return self.client_socket

    def process_input(self, msg):
        if msg.lower().startswith("/connect") and not self.isConnected:
            split_connect_command = msg.split(" ")
            if len(split_connect_command) == 4:
                self.add_prompt(msg)
                self.nickname = split_connect_command[1]
                self.username = split_connect_command[2]
                self.fullname = split_connect_command[3]
                self.create_user_connection()
        if msg.lower().startswith("/msg") and self.isConnected:
            self.send_channel_message(msg)

    def send_channel_message(self, msg):
        privmsg_command = "PRIVMSG #global :" + msg[5:]
        self.client_socket.send(bytes(privmsg_command, "utf-8"))
        self.client_socket.recv(1024).decode()

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

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        return self.client_socket

    def is_client_connected(self):
        return self.isConnected

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
                self.add_prompt(f"User {self.nickname} successfully joined #global channel \n")
            elif "Fail" in nick_decoded_message["Response_Status"] or "Fail" in user_decoded_response_message["Response_Status"]:
                self.add_prompt("Wrong prompt parameters or potential duplicate \n")

    def receive_message(self, msg):
        response = msg.decode().split(";")
        self.add_received_msg(response[0], response[1])


if __name__ == '__main__':

    client = IRCClient("localhost", 9999)

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
