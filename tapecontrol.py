import smbus
import time

class TapeControl:
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.address = 0x04

    def write(self, value):
        self.bus.write_byte(self.address, value)

    def read(self):
        return self.bus.read_byte(self.address)

    def awaitResponse(self):
        response = 0

        while response == 0:
            time.sleep(1)
            response = self.read()

        return response

    def command(self, value):
        if value == 1:
            self.playMode()
        elif value == 4:
            self.recordMode()
        else:
            self.write(value)

        return self.awaitResponse()

    def playMode(self):
        self.write(1)
        self.awaitResponse()
        self.write(7)
        return self.awaitResponse()

    def standbyMode(self):
        self.write(2)
        return self.awaitResponse()

    def reverseMode(self):
        self.write(3)
        return self.awaitResponse()

    def recordMode(self):
        self.write(1)
        self.awaitResponse()
        self.write(4)
        return self.awaitResponse()

    def startMotor(self):
        self.write(5)
        return self.awaitResponse()

    def stopMotor(self):
        self.write(6)
        return self.awaitResponse()

if __name__ == "__main__":
    tc = TapeControl()

    while True:
        num = input("Enter: ")

        if not num:
            continue

        response = tc.command(num)

        print "we sent %x and we got %x" % (num, response)
