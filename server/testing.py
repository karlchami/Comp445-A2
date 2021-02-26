import re

cmd = "NICK Karl"


nick1_regex = re.compile(r'^(NICK)(\s)([a-z][\w\-\[\]`^{}\\]*)(([\s][a-z][\w\-\[\]`^{}\\]*)*)$')
nick2_regex = re.compile(r'^(NICK)(\s)([a-z][\w\-\[\]`^{}\\]*)')
user_regex = re.compile(r'^(USER)(\s)(\w+)(\s)(\w+)(\s)(\w+)(\s:)([\w ]+)$')
quit_regex = re.compile(r'^(QUIT)([\s:]*)(.*)$')
who_regex = re.compile(r'^(WHO)(\s)(\*)([\w\-\[\]`^{}\\]+)$')
ping_regex = re.compile(r'^(PING)$')


print(bool(nick1_regex.search(cmd)))


