def is_valid_command(command):
    # Validates whether the command in the decoded request is an implemented command
    valid_commands = ["NICK", "USER", "JOIN", "PING", "PRIVMSG", "QUIT"]
    if command in valid_commands:
        return command
    return "DOES_NOT_EXIST"