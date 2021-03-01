import socket
import argparse
import logging
import re
from _thread import *

# Initialize logger
logging.basicConfig(filename="server.log", level=logging.DEBUG)
logger = logging.getLogger()


# TODO: Change welcome_message to return only dict. Kept for debugging purposes.
def handle_user_commands(server, conn):
    logger.info("New thread")
    user_connection_info = UserConnection()
    switch = {"NICK": nick_cmd, "USER": user_cmd, "PING": ping_cmd, "WHO": who_cmd, "PRIVMSG": privmsg_cmd, "QUIT": quit_cmd}
    while True:
        raw_request = conn.recv(1024).decode()
        decoded_request = decode_request(raw_request)
        if (decoded_request["Command"] in switch) and (validate_command(decoded_request["Command"], raw_request)):
            response = switch[decoded_request["Command"]](decoded_request, server, conn, user_connection_info)
            # connected_users = ",".join(server.get_connected_users())
            # welcome_message = str(response) + "\n" + "Connected users: " + connected_users
            conn.sendall(bytes(str(response), "utf-8"))
        else:
            conn.sendall(bytes("Invalid Request", "utf-8"))


# Validate command formats according to IRC 1459
def validate_command(command, raw_request):
    regex_validations = {
        "NICK": re.compile(r'^(NICK)(\s)([a-zA-Z][\w\-\[\]`^{}\\]*)(([\s][a-zA-Z][\w\-\[\]`^{}\\]*)*)$'),
        "USER": re.compile(r'^(USER)(\s)(\w+)(\s)(\w+)(\s)(\w+)(\s:)([\w ]+)$'),
        "QUIT": re.compile(r'^(QUIT)([\s:]*)(.*)$'),
        "WHO": re.compile(r'^(WHO)(\s)(\*)([\w\-\[\]`^{}\\]+)$'),
        "PING": re.compile(r'^(PING)$'),
        "PRIVMSG": re.compile(r'^(PRIVMSG #global)(\s:)(.*)$')
    }
    return bool(regex_validations[command].search(raw_request))


# Decodes request into commands and parameters object
def decode_request(request):
    # Decodes a request into a dict object with Command and Parameters while handling special char ":" as one parameter
    split_char = request.split(":")
    request_content = split_char[0].split()
    if len(split_char) > 1:
        for i in range(1, len(split_char)):
            request_content.append(split_char[i])
    decoded_request = {}
    command = request_content[0]
    decoded_request["Command"] = command
    if len(request_content) > 1:
        for i in range(1, len(request_content)):
            parameter = "Parameter" + str(i)
            decoded_request[parameter] = request_content[i]
    return decoded_request


# Builds a dictionary that acts as the response object
def response_builder(decoded_request, response_status, response_message):
    decoded_request["Response_Status"] = response_status
    decoded_request["Response_Message"] = response_message
    return decoded_request


# Handles addition or modification of nickname on server. Returns boolean as status indication for success/fail.
def nick_cmd(decoded_request, server, client_connection, user_connection_info):
    parameter_count = len(decoded_request)
    # If command has 1 username parameter ensure non existing connection + nickname, and USER command info were provided before adding user to server connection
    if parameter_count == 2 and not server.user_exist(decoded_request["Parameter1"]):
        user_connection_info.add_nickname(decoded_request["Parameter1"])
        user_connection_info.add_connection(client_connection)
        if user_connection_info.is_connection_complete():
            if not server.connection_exist(client_connection):
                info = user_connection_info.get_connection_object()
                if server.add_connected_user(info[0], info[1]):
                    return response_builder(decoded_request, "Success", "User " + info[0] + " joined global channel")
            else:
                return response_builder(decoded_request, "Fail", "User session already connected")
        return response_builder(decoded_request, "Success", "Successfully registered username")
    # If command has 2 username parameters ensure old nick exists (and belongs to current client connection) and new nick doesn't exist
    if parameter_count == 3 and server.user_exist(decoded_request["Parameter1"]) and not server.user_exist(decoded_request["Parameter2"]):
        if server.modify_connected_user(decoded_request["Parameter1"], decoded_request["Parameter2"], client_connection):
            user_connection_info.add_nickname(decoded_request["Parameter2"])
            return response_builder(decoded_request, "Success", "User successfully modified to " + decoded_request["Parameter2"])
    return response_builder(decoded_request, "Fail", "An error has occurred")


# Handles addition of user info (Name, server, hostname) to the server
def user_cmd(decoded_request, server, client_connection, user_connection_info):
    user_connection_info.add_real_name(decoded_request["Parameter4"])
    user_connection_info.add_username(decoded_request["Parameter1"])
    user_connection_info.add_server_info(decoded_request["Parameter2"], decoded_request["Parameter3"])
    # Ensure non existing connection + nickname, and NICK command info were provided before adding user to server connection
    if user_connection_info.is_connection_complete():
        if not server.connection_exist(client_connection):
            info = user_connection_info.get_connection_object()
            if server.add_connected_user(info[0], info[1]):
                return response_builder(decoded_request, "Success", "User " + info[0] + " joined global channel")
    else:
        return response_builder(decoded_request, "Success", "Successfully registered user info")
    return response_builder(decoded_request, "Fail", "An error has occurred")


# Verifies if user has an active connection in server
def ping_cmd(decoded_request, server, client_connection, *_):
    if server.connection_exist(client_connection):
        return response_builder(decoded_request, "Success", "PONG " + str(client_connection))
    return response_builder(decoded_request, "Fail", "No existing connection")


def who_cmd(decoded_request, server, client_connection, user_connection_info):
    connected_users = server.get_connected_users()
    if not server.connection_exist(client_connection):
        return response_builder(decoded_request, "FAIL", "No existing connection")
    match = decoded_request["Parameter1"][1:]
    matched_users = []
    for name in connected_users:
        boolean = (match in name) or\
                  (match in connected_users[name]["username"]) or\
                  (match in connected_users[name]["fullname"]) or\
                  (match in connected_users[name]["hostname"]) or\
                  (match in connected_users[name]["servername"])
        if boolean and (name != user_connection_info.get_connection_object()[0]):
            matched_users.append(name)
    return response_builder(decoded_request, "Success", str(matched_users))


# Broadcast any message to all connected users except specified one (current user)
def broadcast_message(server, username, message):
    users_list = server.get_connected_users().copy()
    users_list.pop(username)
    for conn in users_list:
        users_list[conn]["connection"].send(bytes(message, "utf-8"))


# Send message to if connection exists
def privmsg_cmd(decoded_request, server, client_connection, user_connection_info):
    message_to_send = decoded_request["Parameter2"]
    if server.connection_exist(client_connection):
        broadcast_message(server, user_connection_info.get_connection_object()[0], message_to_send)
        return response_builder(decoded_request, "Success", "Message sent")
    return response_builder(decoded_request, "Failed", "No existing connection")


# Quit server and delete all existing connections
def quit_cmd(decoded_request, server, client_connection, user_connection_info):
    quit_message = user_connection_info.get_connection_object()[0]
    if len(decoded_request) > 1:
        quit_message = decoded_request["Parameter1"]
    if server.connection_exist(client_connection):
        broadcast_message(server, user_connection_info.get_connection_object()[0], quit_message)
    if server.remove_connected_user(user_connection_info.get_connection_object()[0], client_connection):
        user_connection_info.clear_connection()
        return response_builder(decoded_request, "Success", "Leaving server")
    return response_builder(decoded_request, "Error", "No existing connection")


# Object that holds and helps ensure all user info have been provided prior to adding them to an active server connection
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

    def clear_connection(self):
        self.nickname = ''
        self.user_connection_obj = {
            "username": "",
            "fullname": "",
            "hostname": "",
            "servername": "",
            "connection": socket
        }


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
        # Verifies that user to be modified belongs to provided connection
        if (old_user in self.connected_users) and (self.connected_users.get(old_user).get("connection") == conn):
            self.connected_users[new_user] = self.connected_users.pop(old_user)
            return True
        return False

    def remove_connected_user(self, user, conn):
        # Remove a user connection from the server
        if (user in self.connected_users) and (self.connected_users.get(user).get("connection") == conn):
            self.connected_users.pop(user)
            return True
        return False

    def get_connected_users(self):
        # Get all connected users in the server
        return self.connected_users

    def user_exist(self, user):
        return user in self.connected_users

    def connection_exist(self, conn):
        for user in self.connected_users:
            if self.connected_users[user]["connection"] == conn:
                return True
        return False


def main():
    # Parsing script arguments from CLI

    #Temp disabled args for simplicity.
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-p', '--port', help='Target port to use', required=True)
    # args = vars(parser.parse_args())


    # IRC Server Config
    host = "localhost"
    port = 9999
    # hard coded port for simplicity
    # port = int(args['port'])

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
