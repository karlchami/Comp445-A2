import re

def decode_request(request):
    # Decodes a request into a dict object with Command and Parameters
    request_content = request.split()
    decoded_request = {}
    command = request_content[0]
    decoded_request["Command"] = command
    for i in range(1, len(request_content)):
        parameter = "Parameter" + str(i)
        decoded_request[parameter] = request_content[i]
    return decoded_request


decoded = decode_request("USER Karl too * :Karl-Joey gabrioel Chami")

real_name = ''
for i in range(4, len(decoded)):
    if i == 4:
        decoded["Parameter" + str(i)] = " " + re.sub('[:]', '', decoded["Parameter" + str(i)])
    real_name += decoded["Parameter" + str(i)] + " "

print(real_name)