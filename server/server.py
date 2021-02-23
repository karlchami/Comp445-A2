import socket
import argparse
import logging
import re
from _thread import *


def handle_user_commands(server, conn):
    username = ''
    while True:
        decoded_request = decode_request(conn.recv(1024).decode())
        if decoded_request["Command"] == "NICK":
            if nick_cmd(decoded_request, server, conn):
                connected_users = ",".join(server.get_connected_users())
                welcome_message = "NICK-Success " + username + "\n" \
                                  + "Connected users: " + connected_users
                conn.sendall(bytes(welcome_message, "utf-8"))
            else:
                conn.sendall(bytes("NICK-Fail", "utf-8"))
        else:
            conn.sendall(bytes("Invalid Request", "utf-8"))


def broadcast_message(server, username, message):
    users_list = server.get_connected_users()
    users_list.pop(username)
    for conn in users_list.values():
        conn.send(bytes(message, "utf-8"))


def decode_request(request):
    # Decodes a request into a dict object with Command and Parameters
    request_content = request.split()
    decoded_request = {}
    command = request_content[0]
    decoded_request["Command"] = command
    for i in range(1, len(request_content)):
        parameter = "Parameter" + str(i)
        decoded_request[parameter] = request_content[i]
    return decoded_request


def is_valid_command(command):
    # Validates whether the command in the decoded request is an implemented command
    valid_commands = ["NICK", "USER", "JOIN", "PING", "PRIVMSG", "QUIT"]
    if command in valid_commands:
        return True
    return False


# Handles addition or modification of nickname on server. Returns boolean as status indication for success/fail.
def nick_cmd(decoded_request, server, client_connection):
    parameter_count = len(decoded_request)
    # Nickname regex according to RFC 1459
    nickname_regex = re.compile(r'^[a-zA-Z]([0-9]|[a-zA-Z]|[-\[\]`^{}\\])*?$')
    # Validating Command according to 1459
    validation = decoded_request["Command"].isupper() and is_valid_command(decoded_request["Command"])
    for i in range(1, parameter_count):
        # Validating Parameters (nicknames) according to regex
        validation = validation and bool(nickname_regex.search(decoded_request["Parameter" + str(i)]))
    # Command processing stops if request format is invalid
    if not validation:
        return False
    # If command has 1 username parameter
    if parameter_count == 2 and not server.user_exist(decoded_request["Parameter1"]):
        new_user = UserConnection()
        new_user.add_nickname(decoded_request["Parameter1"])
        new_user.add_connection(client_connection)
        if new_user.is_connection_complete():
            info = new_user.get_connection_object()
            return server.add_connected_user(info[0], info[1])
        return True
    # If command has 2 username parameters
    if parameter_count == 3 and server.user_exist(decoded_request["Parameter1"]) and not server.user_exist(decoded_request["Parameter2"]):
        print("Here")
        return server.modify_connected_user(decoded_request["Parameter1"],
                                            decoded_request["Parameter2"],
                                            client_connection)
    return False


def user_cmd():
    return


def join_cmd():
    return


def ping_cmd():
    return


def privmsg_cmd():
    return


def quit_cmd():
    return


class UserConnection:
    nickname = ''
    user_connection_obj = {
            "username": "",
            "fullname": "",
            "hostname": "",
            "servername": "",
            "connection": socket
    }

    def __init__(self):
        pass

    def add_connection(self, conn):
        self.user_connection_obj["connection"] = conn

    def add_nickname(self, nick):
        self.nickname = nick

    def add_server_info(self, hostname, servername):
        self.user_connection_obj["hostname"] = hostname
        self.user_connection_obj["servername"] = servername

    def add_real_name(self, name):
        self.user_connection_obj["fullname"] = name

    # Returns validity (boolean) on whether a user connection has all the info it needs before being added to the server
    def is_connection_complete(self):
        validation = bool(self.nickname)
        for element in self.user_connection_obj:
            validation = validation and bool(self.user_connection_obj.get(element))
        return validation

    def get_connection_object(self):
        return self.nickname, self.user_connection_obj


class IRCServer:
    irc_socket = socket.socket()
    host = ''
    port = 0
    # Dictionary of usernames (key) and their connections (values)
    # TODO: Make dict include full info about user such as username, nickname and connection object
    connected_users = {}

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        # Bind socket to host and port
        self.irc_socket.bind((self.host, self.port))
        # Avoid dropping any clients in a queue
        self.irc_socket.listen(999)
        return self.irc_socket

    def close_connection(self):
        # Close IRC Server connection
        self.irc_socket.close()

    def get_host(self):
        return self.host

    def get_socket(self):
        # Return IRC server created and configured socket
        return self.irc_socket

    def add_connected_user(self, user, connection):
        # Add a new user connection to the server
        if not (user in self.connected_users):
            self.connected_users[user] = connection
            return True
        return False

    def modify_connected_user(self, old_user, new_user, conn):
        if (old_user in self.connected_users) and (self.connected_users.get(old_user).get("connection") == conn):
            self.connected_users[new_user] = self.connected_users.pop(old_user)
            return True
        return False

    def remove_connected_user(self, user):
        # Remove a user connection from the server
        if user in self.connected_users:
            self.connected_users.pop(user)

    def get_connected_users(self):
        # Get all connected users in the server
        return self.connected_users

    def user_exist(self, user):
        return user in self.connected_users


def main():
    # Parsing script arguments from CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Target port to use', required=True)
    args = vars(parser.parse_args())

    # Initialize logger
    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    logger = logging.getLogger()

    # IRC Server Config
    host = "localhost"
    port = int(args['port'])

    # Start up the IRC Server
    server = IRCServer(host, port)
    logger.info("Server object created")

    # Bind the IRC server to the specified configuration
    server.connect()
    server_socket = server.get_socket()
    logger.info("Server connection established")

    print("Server connection established, waiting for users to connect")

    while True:
        conn, address = server_socket.accept()
        start_new_thread(handle_user_commands, (server, conn))


if __name__ == '__main__':
    main()