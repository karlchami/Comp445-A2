import socket
import argparse
import logging
import re
from _thread import *

# Initialize logger
logging.basicConfig(filename="server.log", level=logging.DEBUG)
logger = logging.getLogger()


def handle_user_commands(server, conn):
    logger.info("New thread")
    username = ''
    user_connection_info = UserConnection()
    while True:
        decoded_request = decode_request(conn.recv(1024).decode())
        if decoded_request["Command"] == "NICK":
            logger.info("NICK command triggered")
            response = nick_cmd(decoded_request, server, conn, user_connection_info)
            connected_users = ",".join(server.get_connected_users())
            welcome_message = response + "\n" + "Connected users: " + connected_users
            conn.sendall(bytes(welcome_message, "utf-8"))
            logger.info("NICK command responded")
            # print(user_connection_info.get_connection_object()[0])
            # print(user_connection_info.get_connection_object()[1])
        elif decoded_request["Command"] == "USER":
            logger.info("USER command triggered")
            response = user_cmd(decoded_request, server, conn, user_connection_info)
            connected_users = ",".join(server.get_connected_users())
            welcome_message = response + "\n" + "Connected users: " + connected_users
            conn.sendall(bytes(welcome_message, "utf-8"))
            logger.info("USER command responded")
            # print(user_connection_info.get_connection_object()[0])
            # print(user_connection_info.get_connection_object()[1])
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
def nick_cmd(decoded_request, server, client_connection, user_connection_info):
    parameter_count = len(decoded_request)
    # Nickname regex according to RFC 1459
    nickname_regex = re.compile(r'^[a-zA-Z]([0-9]|[a-zA-Z]|[-\[\]`^{}\\])*?$')
    # Validating Command according to 1459
    validation = decoded_request["Command"].isupper() and is_valid_command(decoded_request["Command"]) and parameter_count <= 3
    for i in range(1, parameter_count):
        # Validating Parameters (nicknames) according to regex
        validation = validation and bool(nickname_regex.search(decoded_request["Parameter" + str(i)]))
    # Command processing stops if request format is invalid
    if not validation:
        return "**RESPONSE: Request format is invalid"
    # If command has 1 username parameter
    if parameter_count == 2 and not server.user_exist(decoded_request["Parameter1"]):
        user_connection_info.add_nickname(decoded_request["Parameter1"])
        user_connection_info.add_connection(client_connection)
        if user_connection_info.is_connection_complete():
            if not server.connection_exist(client_connection):
                info = user_connection_info.get_connection_object()
                if server.add_connected_user(info[0], info[1]):
                    return "**RESPONSE: User " + info[0] + " joined global channel"
            else:
                return "**RESPONSE: User session already connected"
        return "**RESPONSE: Successfully registered username"
    # If command has 2 username parameters
    if parameter_count == 3 and server.user_exist(decoded_request["Parameter1"]) and not server.user_exist(decoded_request["Parameter2"]):
        if server.modify_connected_user(decoded_request["Parameter1"], decoded_request["Parameter2"], client_connection):
            return "**RESPONSE: User successfully modified to " + decoded_request["Parameter2"]
    return "**RESPONSE: An error has occurred"


def user_cmd(decoded_request, server, client_connection, user_connection_info):
    parameter_count = len(decoded_request)
    validation = decoded_request["Command"].isupper() and is_valid_command(decoded_request["Command"]) and (parameter_count >= 5) and (decoded_request["Parameter4"].startswith(":"))
    # Command processing stops if request format is invalid
    if not validation:
        return "**RESPONSE: Request format is invalid"
    # Extract user real name from parameters (all params following the : char)
    real_name = ''
    for i in range(4, parameter_count):
        if i == 4:
            decoded_request["Parameter" + str(i)] = re.sub('[:]', '', decoded_request["Parameter" + str(i)])
        real_name += decoded_request["Parameter" + str(i)] + " "
    # Add more connection info to object
    user_connection_info.add_real_name(real_name)
    user_connection_info.add_username(decoded_request["Parameter1"])
    user_connection_info.add_server_info(decoded_request["Parameter2"], decoded_request["Parameter3"])
    if user_connection_info.is_connection_complete():
        if not server.connection_exist(client_connection):
            info = user_connection_info.get_connection_object()
            if server.add_connected_user(info[0], info[1]):
                return "**RESPONSE: User " + info[0] + " joined global channel"
    else:
        return "**RESPONSE: Successfully registered user info"
    return "**RESPONSE: An error has occurred"


def join_cmd():
    return


def ping_cmd():
    return


def privmsg_cmd():
    return


def quit_cmd():
    return


class UserConnection:
    def __init__(self):
        self.nickname = ''
        self.user_connection_obj = {
            "username": "",
            "fullname": "",
            "hostname": "",
            "servername": "",
            "connection": socket
        }

    def add_connection(self, conn):
        self.user_connection_obj["connection"] = conn

    def add_nickname(self, nick):
        self.nickname = nick

    def add_username(self, username):
        self.user_connection_obj["username"] = username

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
    # For debugging purposes
    irc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Dictionary of usernames (key) and their connection info
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

    def connection_exist(self, conn):
        for user in self.connected_users:
            return self.connected_users[user]["connection"] == conn


def main():
    # Parsing script arguments from CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Target port to use', required=True)
    args = vars(parser.parse_args())

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
