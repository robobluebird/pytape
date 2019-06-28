import smbus
import time

class TapeControl:
    def __init__(self):
        self.redo_connection()

    def redo_connection(self):
        self.bus = smbus.SMBus(1)
        time.sleep(1)
        self.address = 0x04

    def write(self, value):
        print "1"
        print "value: %d" % value

        try:
            return self.bus.write_byte(self.address, value)
        except IOError as e:
            print e
            print "crazy pep"
            self.redo_connection()
            return -1

    def write_with_retry(self, value):
        print "2"
        return self.write(value)

    def write_bytes(self, word):
        print "3"

        data = map(lambda x: ord(x), list(word)) 

        try:
            return self.bus.write_i2c_block_data(self.address, 0, data)
        except IOError as e:
            print e
            print "crazy bleep"
            self.redo_connection()
            return -1

    def write_bytes_with_retry(self, word):
        print "4"
        return self.write_bytes(word)

    def read(self):
        print "5"

        try:
            res = self.bus.read_byte(self.address)
            print res
            return res
        except IOError as e:
            print e
            print "crazy blep"
            self.redo_connection()
            return -1

    def read_bytes(self):
        print "6"

        try:
            return self.bus.read_i2c_block_data(self.address, 0)
        except IOError as e:
            print "HELP"
            print e
            self.redo_connection()
            return []

    def await_bytes_response(self):
        print "7"

        response = -1

        while response == -1:
            print "7.5"
            time.sleep(0.5)
            response = self.read_bytes()

        return response

    def await_response(self):
        print "8"

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
            self.write_with_retry(value)

        return self.await_response()

    def play_mode(self):
        self.write_with_retry(1)
        self.await_response()
        self.write_with_retry(7)
        return self.await_response()

    def standby_mode(self):
        self.write_with_retry(2)
        return self.await_response()

    def reverse_mode(self):
        self.write_with_retry(3)
        return self.await_response()

    def record_mode(self):
        self.write_with_retry(1)
        self.await_response()
        self.write_with_retry(4)
        return self.await_response()

    def start_motor(self):
        self.write_with_retry(5)
        return self.await_response()

    def stop_motor(self):
        self.write_with_retry(6)
        return self.await_response()

    def start_recording(self):
        self.record_mode()
        self.start_motor()

    def stop_recording(self):
        self.stop()

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

    def get_message(self):
        self.write_with_retry(9)
        time.sleep(0.5)
        return self.string_from_byte_array(self.await_bytes_response())

    def start_of_tape(self):
        self.write_with_retry(8)
        return self.await_response()

    def advance(self, ticks):
        self.write_bytes_with_retry("advance:%d" % ticks)
        return self.await_response()

    def new_tape(self):
        self.write_with_retry(10)
        return self.await_response()

    def get_ticks(self):
        self.write_with_retry(11)
        time.sleep(0.5)
        return self.string_from_byte_array(self.await_bytes_response())

    def int_from_byte_array(self, byte_array):
        return int(self.string_from_byte_array(byte_array))

    def string_from_byte_array(self, byte_array):
        try:
            print byte_array
            return "".join(map(lambda x: chr(x), [x for x in byte_array if x != 255]))
        except TypeError as e:
            print e
            return ""

if __name__ == "__main__":
    tc = TapeControl()

    while True:
        num = input("Enter: ")

        if not num:
            continue

        tc.command(num)
