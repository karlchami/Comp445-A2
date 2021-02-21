import socket
import argparse
import logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Target port to use', required=True)
    args = vars(parser.parse_args())
    port = int(args['port'])

    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    logger = logging.getLogger()

    server = IRCServer()
    logger.info("Server object created")
    server.connect("localhost", port)
    logger.info("Server connection established")

    logger.info("Listening to requests")
    while True:
        server.receive()


class IRCServer:
    irc_socket = socket.socket()

    def __init__(self):
        return

    def connect(self, servername, portnum):
        self.irc_socket.bind((servername, portnum))
        self.irc_socket.listen(9)

    def close_connection(self):
        self.irc_socket.close()

    def send(self, message):
        self.irc_socket.send(bytes(message, "utf-8"))

    def receive(self):
        client, client_address = self.irc_socket.accept()
        response = client.recv(2040)
        reply_message = "Welcome, " + response.decode()
        client.send(bytes(reply_message, "utf-8"))
        client.close()


if __name__ == '__main__':
    main()
