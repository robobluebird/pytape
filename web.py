import requests
import time
import subprocess
import os
from tapecontrol import TapeControl
from threading import Thread

class Web:
    def __init__(self, owner):
        self.owner = owner
        self.do_monitoring = False
        self.tc = TapeControl()
        self.base_url = 'https://sheltered-forest-46485.herokuapp.com'

    def check(self):
        r = requests.get("%s/uploads" % self.base_url)
        return r.json()

    def download(self, name):
        url = "%s/uploads/%s" % (self.base_url, name)
        r = requests.get(url, allow_redirects=True)
        return open(name, 'wb').write(r.content)

    def mark(self, name):
        url = "%s/uploads/%s/ok" % (self.base_url, name)
        r = requests.post(url)
        return (r.status_code, r.json())

    def create(self, name, ticks):
        url = "%s/tapes" % self.base_url
        r = requests.post(url, data = {'name': name, 'ticks': ticks})
        return (r.status_code, r.json())

    def update(self, name, side, filename, ticks):
        url = "%s/tapes/%s" % (self.base_url, name)

        r = requests.put(url, data = {'side': side, 'filename': filename, 'ticks': ticks})

        return (r.status_code, r.json())

    def tapes(self):
        r = requests.get("%s/tapes" % self.base_url)

        if r.status_code == 200:
            return r.json()['tapes']
        else:
            return []

    def tape(self, name):
        r = requests.get("%s/tapes/%s" % (self.base_url, name))

        if r.status_code == 200:
            return r.json()['tape']
        else:
            return None

    def stop(self):
        self.update("stopping!")

        self.do_monitoring = False
        self.thread.join()

    def start(self):
        self.thread = Thread(target=self.monitor)
        self.thread.start()

    def update(self, message):
        if self.owner != None:
            self.owner.update(message)
        else:
            print message

    def monitor(self):
        self.do_monitoring = True

        while self.do_monitoring:
            self.update("checking the web...")

            response = self.check()

            if len(response['uploads']) > 0:
                name = response['uploads'][0]

                self.update("downloading %s..." % name)

                self.download(name)

                self.update("sending %s to tape..." % name)

                cmd = "mpg123 -q %s" % name

                self.tc.recordMode()

                self.tc.startMotor()

                result = subprocess.check_output(cmd, shell = True )

                result = self.tc.stopMotor()

                print result

                self.tc.standbyMode()

                self.mark(name)

                os.remove(name)

                self.update("downloaded, recorded, and marked finished!")
            else:
                self.update("nothing to do!")

            time.sleep(5)


if __name__ == "__main__":
    w = Web()

    w.monitor()

