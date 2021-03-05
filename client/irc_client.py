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
        self.add_prompt_msg(nick_decoded_message["Response_Message"])
        self.add_prompt_msg(user_decoded_response_message["Response_Message"])
        if "Success" in nick_decoded_message["Response_Status"] and "Success" in user_decoded_response_message["Response_Status"]:
            self.isConnected = True


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
        if msg.lower().startswith("/connect"):
            split_connect_command = msg.split(" ")
            if len(split_connect_command) == 6:
                self.add_prompt_msg(msg)
                self.nickname = split_connect_command[1]
                self.username = split_connect_command[2]
                self.fullname = split_connect_command[3]
                self.hostname = split_connect_command[4]
                self.servername = split_connect_command[5]
                self.create_user_connection()
        elif self.isConnected:
            self.add_msg(msg)
        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt

    def add_prompt_msg(self, msg):
        self.view.add_msg("Prompt", msg)

    def add_msg(self, msg):
        self.view.add_msg(self.username, msg)

    async def run(self):
        """
        Driver of your IRC Client
        """

    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass


def main(args):
    # Pass your arguments where necessary
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
