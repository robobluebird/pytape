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
            time.sleep(0.5)
            response = self.read()

        return response

    def command(self, value):
        if value == 1:
            self.playMode()
        elif value == 4:
            self.recordMode()
        elif value == 6:
            return self.stopMotor()
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
        time.sleep(0.5)
        response = self.bus.read_i2c_block_data(self.address, 0)
        return self.intFromByteArray(response)

    def play(self):
        self.stopMotor()
        self.playMode()
        self.startMotor()

    def rec(self):
        self.stopMotor()
        self.recordMode()
        self.startMotor()

    def stop(self):
        self.stopMotor()
        self.standbyMode()

    def rw(self):
        self.stopMotor()
        self.reverseMode()
        self.startMotor()

    def ff(self):
        self.stopMotor()
        self.standbyMode()
        self.startMotor()

    def intFromByteArray(self, byteArray):
        return int("".join(map(lambda x: chr(x), [x for x in byteArray if x != 255])))

if __name__ == "__main__":
    tc = TapeControl()

    while True:
        num = input("Enter: ")

        if not num:
            continue

        response = tc.command(num)

        print response
