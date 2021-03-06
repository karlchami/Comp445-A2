# Comp 445 Assignment 2 
## Socket Programming - IRC Chat


Karl-Joey Chami - 27736657
Nicolas Zito - 40029473

## How to run
### Server
In order to start a server it is required to specify the port it runs on.
* Navigate to **/irc_chat** using ```cd irc_chat```
* Run ```python server.py -p 1234``` to run on port 1234

### Client
You can run as many client instances as you would like to.
In order to connect a client instance to the server it is required to specify the same port used to run server.

* Navigate to **/irc_chat** using ```cd irc_chat```
* Run ```python client.py -p 1234``` to bind to server port 1234

## How to use a client
* To register yourself as a new user you should enter the **/connect** command as such
    * ```/connect nickname username name```
* Once you are connected (and assuming your entered parameters are unique) you will be joined to the global channel
* To send a chat message enter the command **/msg** follow by a message as such
    *  ```/msg Hello World!```
* To leave the channel, close the chat and the connection with the server, use the **/quit** command as such
    * ```/quit``` 
* If you close the chat without quitting, you will be automatically disconnected from the channel and server
