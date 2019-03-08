import requests
import time
import subprocess
import os
from tapecontrol import TapeControl

class Web:
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

if __name__ == "__main__":
    w = Web()
    tc = TapeControl()

    while True:
        response = w.check()

        if len(response['uploads']) > 0:
            name = response['uploads'][0]

            print "downloading %s..." % name

            w.download(name)

            print "done!"

            print "sending to tape..."

            cmd = "mpg123 %s" % name

            tc.recordMode()

            tc.startMotor()

            result = subprocess.check_output(cmd, shell = True )

            result = tc.stopMotor()

            print result

            tc.standbyMode()

            w.mark(name)

            os.remove(name)

            print "downloaded, recorded, and marked finished!"
        else:
            print "nothing to do"

        time.sleep(5)
