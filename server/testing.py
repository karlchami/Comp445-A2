import re
dic = {
    'Karl': {'username': 'karlchami', 'fullname': 'Karl Chami', 'hostname': 'local', 'servername': 'host'},
    'Elie': {'username': 'elie', 'fullname': 'Elie', 'hostname': 'sdsd', 'servername': 'sdfsd'}
}

word = "chami"

for name in dic:
    boolean = (word in name) or (word in dic[name]["username"]) or (word in dic[name]["fullname"]) or (word in dic[name]["hostname"]) or (name in dic[name]["servername"])
    if boolean:
        print(name)
