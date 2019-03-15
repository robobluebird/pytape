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

    def check(self):
        r = requests.get('https://sheltered-forest-46485.herokuapp.com/uploads')

        return r.json()

    def download(self, name):
        url = "https://sheltered-forest-46485.herokuapp.com/uploads/%s" % name

        r = requests.get(url, allow_redirects=True)
        
        open(name, 'wb').write(r.content)

    def mark(self, name):
        url = "https://sheltered-forest-46485.herokuapp.com/uploads/%s/ok" % name

        r = requests.post(url)

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

