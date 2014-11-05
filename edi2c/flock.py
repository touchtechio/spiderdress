"""Process-level locking with flock().

http://blog.vmfarms.com/2011/03/cross-process-locking-and.html
"""
import os
import fcntl

class Flock:
    def __init__(self, filename):
        self.filename = filename
        self.handle = open(filename, 'w')

    def acquire(self):
        fcntl.flock(self.handle, fcntl.LOCK_EX)

    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)

    def __del__(self):
        self.handle.close()
