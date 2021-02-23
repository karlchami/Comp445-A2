

class CrustyCrust:
    def __init__(self):
        self.names = []

    def add_name(self, name):
        self.names.append(name)

    def get_names(self):
        return self.names


crust = CrustyCrust()
crust.add_name("Karl")
print(crust.get_names())

crisp = CrustyCrust()
crisp.add_name("John")
print(crisp.get_names())
