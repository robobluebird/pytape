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
        self.headers = {'Accept': 'application/json'}

    def uploads(self, tape_id):
        r = requests.get("%s/tapes/%s/uploads" % (self.base_url, tape_id), headers = self.headers)
        return r.json()['uploads']

    def download(self, tape_id, name, filepath):
        url = "%s/tapes/%s/uploads/%s" % (self.base_url, tape_id, name)
        r = requests.get(url,  headers = self.headers)
        response = requests.get(url, stream=True)
        handle = open(filepath, "wb")
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                handle.write(chunk)
        handle.close()
        return handle.closed

    def mark(self, tape_id, name):
        url = "%s/tapes/%s/uploads/%s/ok" % (self.base_url, tape_id, name)
        r = requests.post(url, headers = self.headers)
        return r.status_code == 200

    def check_tape_name(self, name):
        r = requests.get("%s/tapes/%s/check" % (self.base_url, name), headers = self.headers)
        return r.status_code == 404

    def create(self, name, ticks):
        url = "%s/tapes" % self.base_url
        r = requests.post(url, data = {'name': name, 'ticks': ticks}, headers = self.headers)
        return r.status_code == 200

    def update(self, name, side, complete = False, filename = None, ticks = None):
        url = "%s/tapes/%s/side/%s" % (self.base_url, name, side)

        print "-- updating/ --"
        print name
        print side
        print complete
        print filename
        print ticks
        print "-- /updating --"
        print ""

        r = requests.put(url, data = {'side': side, 'complete': complete, 'filename': filename, 'ticks': ticks}, headers = self.headers)

        if r.status_code == 200:
            return r.json()['tape']
        else:
            return None

    def tapes(self):
        r = requests.get("%s/tapes" % self.base_url, headers = self.headers)

        if r.status_code == 200:
            return r.json()['tapes']
        else:
            return []

    def tape(self, name):
        r = requests.get("%s/tapes/%s" % (self.base_url, name), headers = self.headers)

        if r.status_code == 200:
            return r.json()['tape']
        else:
            return None

    def stop(self):
        self.do_monitoring = False
        self.thread.join()

    def start(self):
        self.thread = Thread(target=self.monitor)
        self.thread.start()

# if __name__ == "__main__":

