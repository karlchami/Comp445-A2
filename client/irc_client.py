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
import sys
import threading
import time

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(("localhost", 9999))

class IRCClient(patterns.Subscriber):
    global nick_in
    global username_in
    global hostname_in
    global portname_in
    global realname_in

    def __init__(self, username):
        super().__init__()
        self.username = username
        self._run = True

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
        # Will need to modify this

        self.add_msg(msg)
        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt
        else:
            print(msg)

    def add_msg(self, msg):
        self.view.add_msg(self.username, msg)

    def receive_msg(self):
        while True:
            msg_recv = c.recv(1024).decode()
            if not msg_recv: sys.exit(0)
            if "{'Command': 'PRIVMSG'," in msg_recv:
                continue
            self.add_msg(msg_recv)

    async def run(self):
        """
        Driver of your IRC Client
        """
        receive_thread = threading.Thread(target=self.receive_msg).start()
        msg_sent = "Hello World!"
        c.send(bytes(f"PRIVMSG #global :" + msg_sent, "utf-8"))


    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass


def main(args):
    # Pass your arguments where necessary

    loop = True
    while loop:
        nick_in = input("Please enter your NICK: ")
        c.send(bytes("NICK " + nick_in, "utf-8"))
        print("Got reply: ")
        nick_response = c.recv(1024).decode()
        if nick_response == "Invalid Request":
            print(nick_response)
            print("Please enter valid Nick credentials")
        else:
            loop = False
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

    client = IRCClient(nick_in)
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
    client.close()


if __name__ == "__main__":
    args = None
    main(args)
