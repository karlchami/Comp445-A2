import socket
import argparse
import logging
from _thread import *


def handle_user_commands(server, conn):
    username = ''
    while True:
        received_command = conn.recv(1024).decode()
        command_content = received_command.split(" ")
        if command_content[0] == "NICK":
            username = command_content[1]
            server.add_connected_user(username, conn)
            connected_users = ",".join(server.get_connected_users())
            welcome_message = "Welcome to the IRC Server, " + username + "\n" + "Connected users: " + connected_users
            conn.sendall(bytes(welcome_message, "utf-8"))
        elif command_content[0] == "QUIT":
            username = command_content[1]
            server.remove_connected_user(username)
            connected_users = ",".join(server.get_connected_users())
            quit_message = "User successfully removed, " + username + "\n" + "Connected users: " + connected_users
            conn.sendall(bytes(quit_message, "utf-8"))
        elif command_content[0] == "PRIVMSG":
            message = command_content[1]
            if username:
                broadcast_message(server, username, message)
            else:
                conn.sendall(bytes("Please use NICK first", "utf-8"))
        else:
            conn.sendall(bytes("Could not process your command", "utf-8"))


def broadcast_message(server, username, message):
    users_list = server.get_connected_users()
    users_list.pop(username)
    for conn in users_list.values():
        conn.send(bytes(message, "utf-8"))


class IRCServer:

    irc_socket = socket.socket()
    # Dictionary of usernames (key) and their connections (values)
    connected_users = {}

    def __init__(self):
        pass

    def connect(self, host, port):
        # Bind socket to host and port
        self.irc_socket.bind((host, port))
        # Avoid dropping any clients in a queue
        self.irc_socket.listen(999)
        return self.irc_socket

    def close_connection(self):
        # Close IRC Server connection
        self.irc_socket.close()

    def get_socket(self):
        # Return IRC server created and configured socket
        return self.irc_socket

    def add_connected_user(self, user, connection):
        # Add a new user connection to the server
        if not(user in self.connected_users):
            self.connected_users[user] = connection

    def remove_connected_user(self, user):
        # Remove a user connection from the server
        if user in self.connected_users:
            self.connected_users.pop(user)

    def get_connected_users(self):
        # Get all connected users in the server
        return self.connected_users


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
    server = IRCServer()
    logger.info("Server object created")

    # Bind the IRC server to the specified configuration
    server.connect(host, port)
    server_socket = server.get_socket()
    logger.info("Server connection established")

    print("Server connection established, waiting for users to connect")

    while True:
        conn, address = server_socket.accept()
        start_new_thread(handle_user_commands, (server, conn))


if __name__ == '__main__':
    main()
