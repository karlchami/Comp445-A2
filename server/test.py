user_connection_obj = {"karl": {
    "username": "fdfd",
    "fullname": "df",
    "hostname": "dfd",
    "server_name": "dfd"
}}

for element in user_connection_obj:
    print(user_connection_obj.get(element).get("hostname"))

