"""

N.B.: lockbyfile works perfectly on Windows, but NOT on Linux!

See my question:
http://stackoverflow.com/a/28532580/3693375

The reason:
'os.rename(src, dst): On Unix, if dst exists and is a file, it will be replaced silently'

And I based my lock on the fact that rename raises an exception when dst already exists.
  
*merde*

I have now fixed it differently, with mkdir rmdir. 
Do NOT use this here on Linux, lockbyfile is not a safe lock on Linux!

"""


'''
lockbyFILE.py - Locking across processes. Using lockFILE existence and age. 

@contact:  python (at) AndreasKrueger (dot) de
@since:    23 Jan 2015

@license:  Never remove my name, nor the examples - and send me job offers.
@todo:     I am poor, send bitcoins: 1MT9gazTyodKVU3XFEUgR5aCwG7rXXiuWC Thx! 

@requires: lockbydir.py                    # for fully working OS indep. code
@requires: lockbydir_concurrent.py         # for multiprocess example   

@call:     L = DLock( "name" )   # see howToUse() for details
@return:   class with .LoopWhileLocked_ThenLocking() and .unlocking()

@summary 

See lockbydir.py for overview.

These are only the take-outs, that are obsolete now.

Inner workings:
A lock is represented by a lockfile, in the current directory.
While it exists, and its filedate is recent, the lock is 'locked'.
If the file does not exist, or is timed out, the lock is 'unlocked'.

fileLocking is a 2 step process: 
Create tempfile, then rename to common filename;
lock is successfully acquired when rename succeeded.

But works properly only on Windows ...

See lockbydir.py now!

See my github For feature requests, ideas, suggestions, appraisal, criticism:
@issues https://github.com/drandreaskrueger/lockbydir/issues
@wiki https://github.com/drandreaskrueger/lockbydir/wiki 
'''

# file extension:
LOCKFILEEXTENSION = ".lockfile"
ERROR = -1

import os, datetime, threading, time



def f_exists (filename):
    "does the file exist?"
    return os.path.exists(filename)

def f_modification_date(filename):
    "last modification date of file, as datetime.datetime"
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def f_age(filename):
    "Last modification of file was how many seconds ago?"
    try:
        age = (datetime.datetime.now() - f_modification_date(filename))
        age = age.total_seconds()
    except:
        age = ERROR # e.g. WindowsError: [Error 5] Access denied: '...lockfile'
    return age

def make_temp_f (name, extension):
    "create a temporary file, unique by (name, PID, threadID, time)"     
    pid, tid = os.getpid(), threading.currentThread().ident
    timestamp = time.clock()
    tmp_file = "%s_%s_%s_%s%s" % \
            ( name, pid, tid, timestamp, extension)
            
    open(tmp_file, 'w').close() # if this fails, user should know. HD broken?
    return tmp_file

def renameOrRemove (file1, file2):
    """If rename file1 to file2 succeeds, return True.
       If fails, remove file1, and return False
       
       SHIT: This is safe only on Windows, the reason on Linux is this 'silently':
       
       os.rename(src, dst)
       Rename the file or directory src to dst. 
       If dst is a directory, OSError will be raised. 
       On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. 
       The operation may fail on some Unix flavors if src and dst are on different filesystems. 
       If successful, the renaming will be an atomic operation (this is a POSIX requirement). 
       On Windows, if dst already exists, OSError will be raised even if it is a file
       https://docs.python.org/2/library/os.html#os.rename
       """
    try:
        os.rename( file1, file2 )
        return True
    except (OSError, ValueError, IOError):
        os.remove( file1 )
        return False
    
""" 
# big problem: Different behaviour on Windows and Linux:

import os

try: os.remove("a")
except: pass
try: os.remove("b")
except: pass

f = open("a", 'w')
f.write("lalala")
f.close()

f = open("b", 'w')
f.write("lalala")
f.close()

os.rename( "a", "b")

# raises exception on windows, but silently overwrites on Linux. *meh*

"""  


class DLock:
    """only the now obsolete stuff. see lockbydir.py for remaining code"""

    def fn (self):
        "lockname plus extension = lockfile"
        return self.name + LOCKFILEEXTENSION
    
    def locking_byfile_OBSOLETE(self):
        """Tries to create a lockfile for this lockname,
           by renaming ... then return true.
            
           If already existed and not timed out yet, 
           (or renaming fails for other reasons), then return false."""
           
        self.startWaiting()
           
        if self.existsAndNotTimedOut():
            return False

        # idea adapted from http://stackoverflow.com/a/21444311/3693375
        # "Assuming ... os.rename as an atomic operation ..."
        # (but that example did not provide a timeout)
        # (and MUCH later I noticed it is not safe on Linux)
        
        tmp_file = make_temp_f (self.name, LOCKFILEEXTENSION)
        acquired = renameOrRemove (tmp_file, self.fn() )
        
        if acquired:
            self.lockingTime = time.time()
            self.startedWaitingTime = None
            
        return acquired

    def breakLock_OBSOLETE(self):
        """Low level routine, do not call directly unless you really know why!
           
           If lock owner, just use 'unlocking'.
           Or: Just let it time out, old file is like no file.
           
           returns True if there was a lockfile for this lockname.
           return False if not."""
        try:
            os.remove ( self.fn() )
            return True
        except:
            return False




if __name__ == '__main__':
    print "... contains only the OBSOLETE stuff. See lockbydir.py for properly working lock."
    
    
