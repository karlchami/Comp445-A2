#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021
#
# Distributed under terms of the MIT license.

"""
Description:

"""
import asyncio
import logging

import patterns
import view
import socket
import ast
from _thread import *
import select
import sys

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()


class IRCClient(patterns.Subscriber):

    def __init__(self):
        super().__init__()
        self.server_port = 9999
        self.nickname = str()
        self.username = str()
        self.fullname = str()
        self.hostname = str()
        self.servername = str()
        self.isConnected = False
        self._run = True

    # def __init__(self, nickname, username, fullname, hostname, servername):
    #     self.nickname = nickname
    #     self.username = username
    #     self.fullname = fullname
    #     self.hostname = hostname
    #     self.servername = servername

    def server_connection(self):
        self.server_socket = socket.socket()
        logger.info(f"Attempting connection to {self.hostname} on port {self.server_port}")
        self.server_socket.connect((self.hostname, self.server_port))
        logger.info("Connected to server socket")

    def create_user_connection(self):
        if hasattr(self, "nickname"):
            nick_command = "NICK " + self.nickname
        if hasattr(self, "username") and hasattr(self, "hostname") and hasattr(self, "servername") and hasattr(self, "fullname"):
            user_command = f"USER {self.username} {self.hostname} {self.servername} :{self.fullname}"
        if not hasattr(self, "server_socket"):
            self.server_connection()

        self.server_socket.send(bytes(nick_command, "utf-8"))
        nick_reply = self.server_socket.recv(1024).decode()
        logger.info(nick_reply)
        nick_decoded_message = ast.literal_eval(nick_reply)
        self.server_socket.send(bytes(user_command, "utf-8"))
        user_reply = self.server_socket.recv(1024).decode()
        logger.info(user_reply)
        user_decoded_response_message = ast.literal_eval(user_reply)
        # self.add_prompt_msg(nick_decoded_message["Response_Message"])
        # self.add_prompt_msg(user_decoded_response_message["Response_Message"])
        if "Joined" in nick_decoded_message["Response_Status"] or "Joined" in user_decoded_response_message["Response_Status"]:
            self.isConnected = True
            self.add_prompt_msg(f"User {self.nickname} successfully joined #global channel")
            self.listen_chat()
        elif "Fail" in nick_decoded_message["Response_Status"] or "Fail" in user_decoded_response_message["Response_Status"]:
            self.add_user_msg("Wrong prompt parameters or potential duplicate")

    def set_view(self, view):
        self.view = view

    def update(self, msg):
        # Will need to modify this
        if not isinstance(msg, str):
            raise TypeError(f"Update argument needs to be a string")
        elif not len(msg):
            # Empty string
            return
        logger.info(f"IRCClient.update -> msg: {msg}")
        self.process_input(msg)

    def process_input(self, msg):
        if msg.lower().startswith("/connect") and not self.isConnected:
            split_connect_command = msg.split(" ")
            if len(split_connect_command) == 6:
                self.add_prompt_msg(msg)
                self.nickname = split_connect_command[1]
                self.username = split_connect_command[2]
                self.fullname = split_connect_command[3]
                self.hostname = split_connect_command[4]
                self.servername = split_connect_command[5]
                self.create_user_connection()
        elif msg.lower().startswith("/msg") and self.isConnected:
            self.add_msg(msg[5:])
            self.send_chat_message(msg[5:])

        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt

    def send_chat_message(self, msg):
        privmsg_command = f"PRIVMSG #global {msg}"
        self.self.server_socket.send(bytes(privmsg_command, "utf-8"))

    def listen_chat(self):
        while True:

            # maintains a list of possible input streams
            sockets_list = [sys.stdin, self.server_socket]

            """ There are two possible input situations. Either the  
            user wants to give manual input to send to other people,  
            or the server is sending a message to be printed on the  
            screen. Select returns from sockets_list, the stream that  
            is reader for input. So for example, if the server wants  
            to send a message, then the if condition will hold true  
            below.If the user wants to send a message, the else  
            condition will evaluate as true"""
            read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])
            logger.info("Started listening thread")
            for socks in read_sockets:
                if socks == self.server_socket:
                    message = socks.recv(2048).decode()
                    self.add_user_msg(message)
                else:
                    message = sys.stdin.readline()
                    self.send_chat_message(message)
                    sys.stdout.write("<You>")
                    sys.stdout.write(message)
                    sys.stdout.flush()

    def add_user_msg(self, msg):
        self.view.add_msg("Someuser", msg)

    def add_prompt_msg(self, msg):
        self.view.add_msg("Prompt", msg)

    def add_msg(self, msg):
        self.view.add_msg(self.nickname, msg)

    async def run(self):
        """
        Driver of your IRC Client
        """

    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass


def main(args):
    client = IRCClient()
    logger.info(f"Client object created")
    with view.View() as v:
        logger.info(f"Entered the context of a View object")
        client.set_view(v)
        logger.debug(f"Passed View object to IRC Client")
        v.add_subscriber(client)
        logger.debug(f"IRC Client is subscribed to the View (to receive user input)")

        async def inner_run():
            await asyncio.gather(
                v.run(),
                client.run(),
                return_exceptions=True,
            )

        try:
            asyncio.run(inner_run())
        except KeyboardInterrupt as e:
            logger.debug(f"Signifies end of process")
    # client.close()


if __name__ == "__main__":
    # Parse your command line arguments here
    args = None
    main(args)
