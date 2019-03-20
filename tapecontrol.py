import smbus
import time

class TapeControl:
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.address = 0x04

    def write(self, value):
        self.bus.write_byte(self.address, value)

    def read(self):
        try:
            return self.bus.read_byte(self.address)
        except IOError:
            return -1

    def read_bytes(self):
        try:
            return self.bus.read_i2c_block_data(self.address, 0)
        except IOError:
            return []

    def await_response(self):
        response = 0

        while response == 0:
            time.sleep(0.5)
            response = self.read()

        return response

    def command(self, value):
        if value == 1:
            self.play_mode()
        elif value == 4:
            self.record_mode()
        elif value == 6:
            return self.stop_motor()
        else:
            self.write(value)

        return self.await_response()

    def play_mode(self):
        self.write(1)
        self.await_response()
        self.write(7)
        return self.await_response()

    def standby_mode(self):
        self.write(2)
        return self.await_response()

    def reverse_mode(self):
        self.write(3)
        return self.await_response()

    def record_mode(self):
        self.write(1)
        self.await_response()
        self.write(4)
        return self.await_response()

    def start_motor(self):
        self.write(5)
        return self.await_response()

    def stop_motor(self):
        self.write(6)
        time.sleep(0.5)
        return self.int_from_byte_array(self.read_bytes())

    def play(self):
        self.stop_motor()
        self.play_mode()
        self.start_motor()

    def rec(self):
        self.stop_motor()
        self.record_mode()
        self.start_motor()

    def stop(self):
        self.stop_motor()
        self.standby_mode()

    def rw(self):
        self.stop_motor()
        self.reverse_mode()
        self.start_motor()

    def ff(self):
        self.stop_motor()
        self.standby_mode()
        self.start_motor()

    def start_of_tape(self):
        self.write(8)
        return self.await_response()

    def int_from_byte_array(self, byte_array):
        return int("".join(map(lambda x: chr(x), [x for x in byte_array if x != 255])))

if __name__ == "__main__":
    tc = TapeControl()

    while True:
        num = input("Enter: ")

        if not num:
            continue

        tc.command(num)
