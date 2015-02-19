'''
lockbydir.py - Locking across processes. Using lockdir existence and age. 

@contact:  python (at) AndreasKrueger (dot) de
@since:    23 Jan 2015

@license:  Never remove my name, nor the examples - and send me job offers.
@bitcoin:  I am poor, send bitcoins: 1MT9gazTyodKVU3XFEUgR5aCwG7rXXiuWC Thx! 

@requires: lockbydir_OS.py                # OS level routines for lockdir 
@requires: lockbydir_concurrent.py        # for multiprocess example   

@call:     L = DLock( "name" )            # see howToUse() for details
@return:   class with .LoopWhileLocked_ThenLocking() and .unlocking()

@summary 

An easy to use lock mechanism, with lock timeout, and limited waiting patience.

I want locking of the django DB, across concurrent uwsgi processes, for any 
underlying DB. See posting: http://stackoverflow.com/q/28030536/3693375
When no one could really help me to the end, I created this class 'DLock'.

Inner workings:
A lock is represented by a lockdir, in the current directory (or a RAMDISK).

While it exists, and its filedate is recent, the lock is 'locked'.
If the dir does not exist, or is timed out, the lock is 'unlocked'.

Users need not care about the lockdir, but access the DLock class 
by two functions: .LoopWhileLocked_ThenLocking() and .unlocking()


Parameters:
TIMEOUT:  Seconds after which a lock opens automatically.
PATIENCE: Seconds after which no more hope to acquire the lock. 

Default TIMEOUT, and PATIENCE can be changed in each DLock instance, 
or (better) by subclassing DLock. 

Shortest possible usage is in howToUse().
The inner workings are well explained in testDLocks().
Parallel processes are shown in 2 examples in 'lockbydir_concurrent.py'. 


@todo: Possible future improvement:

TODO 1: how to make this atomic ?

    if self.timedOut():
       self.breakLock()  
       
I have never seen it happen (as the first step is very fast), but it is not 
impossible that 2 processes both arrive at .timedOut() = True at the same time. 
And when one has done '.breakLock()' AND later already created a new lock, 
only then the second one reaches the '.breakLock()'. 
Very improbable, but not impossible.  Then two could both be locking. 

I have no idea how to solve this. What is the equivalent of a successful mkdir, 
when successful non-existence of a directory is the criterion? While at the same 
time exactly that is the starting point for the opposite process. A riddle. 



TODO 2: Put timeout into lock dir

At the moment all processes using DLock with same name must make sure 
that they use the same TIMEOUT!  See 'lockbydir_concurrent.FastDLock'
for an elegant way to guarantee that. (Subclassing DLock)
 
New idea: Put timeout into lockdir, then each lockdir creator can decide 
about his own timeout - and all waiting consumers have to obey to that.
Would really put PATIENCE into the waiting one, and TIMEOUT into the lock.

Considerable overhead because all waiting processes will check often 
for timeout, so lots of read-access to the disk. Or all waiting loops 
get a timer each, and only come back to checking for timeout as soon
as the lock's time is up. Quite a bit of work - perhaps?
  
Still, a good idea, I guess. But as all my processes have the same timeout,
not necessary for my purposes. Fork this GIT if you want to implement it. 
(Or pay me to code it. See @bitcoin.)


And please: Contact me. Send a postcard. In any case. Thanks a lot.
This was a very interesting task! :-) Learnt a lot! Python is great!

See my github For feature requests, ideas, suggestions, appraisal, criticism:
@issues https://github.com/drandreaskrueger/lockbydir/issues
@wiki   https://github.com/drandreaskrueger/lockbydir/wiki 


'''

# default values: 
# (Overwrite in your DLock() instance, not here!)

# for looping:
CHECKEVERYXSECONDS = 0.03 # How frequently check 'isUnlocked' in while loop.

# Locked resource MUST be freed after this timeout!
# Old lockdir is treated as if it didn't exist at all.
# ! After timeout, the lock does not protect anymore !
TIMEOUT = 10  # for some of the examples, 10 is optimal.

# When trying to get the resource, don't wait longer than this.
# Between first attempt to lock, and finally giving up:
PATIENCE = 30

# do not change:
REMOVETIMEDOUT = True  # default: remove old locks when tested by 'isLocked'

import time

from lockbydir_OS import LOCKDIREXTENSION, pathExists, pathAgeInSeconds
from lockbydir_OS import mkdir_ReturnWhetherSuccessful, rmdir_ReturnWhetherSuccessfullyRemoved


class DLock:
    """Locking by directory existence, and age. With 2 auto-timeouts:
    
       TIMEOUT: After 'timeout' seconds a lockdir is like no lockdir.
       PATIENCE: A waiting instance gives up after 'patience' seconds. 
    
       Only the lock 'name' is relevant for the state, i.e.:
       Several instances with identical 'name's share the same lock!"""

    # begin PUBLIC 
    # the following three are the only functions which you need to access:
    
    def __init__(self, name):
        self.name = name
        self.lockingTime = None
        self.startedWaitingTime = None
        
        # default values. Overwrite in your instance if other values wanted.
        # explanations: See top of this code file.
        self.TIMEOUT = TIMEOUT
        self.PATIENCE = PATIENCE
        self.CHECKEVERYXSECONDS = CHECKEVERYXSECONDS
        self.REMOVETIMEDOUT = REMOVETIMEDOUT
        self.LOCKDIREXTENSION = LOCKDIREXTENSION

    def LoopWhileLocked_ThenLocking(self):
        """THIS is the correct way to acquire a lock.
        
           It waits for lock to open or time out, then tries locking.
           (If many are waiting,) repeat only until PATIENCE is gone. 
           
           Returns False if locking failed.
           Returns True if locking succeeded.
        """
        self.startedWaitingTime = time.time()
        acquired = False
        
        while (not acquired and self.stillPatience()):  
            _ = self.loopWhileLocked() 
            acquired = self.locking()
            
        return acquired 

    def unlocking( self ):
        """Try remove lock if owned by me & not timed-out yet.
           If removal happened, return true.
           If not, return false.
           
           N.B.: Only the rightful lock can use unlocking.
           N.B.: Unlocking is only possible before timeout.
           
        """
        
        if self.lockingTime == None: # cannot be the owner
            return False

        # never unlock after timeout, 
        # because it might already be owned by other process!
        elif (time.time() - self.lockingTime) < self.TIMEOUT:
            self.lockingTime = None
            return self.breakLock()
        else:
            return False # so it had already timed out

    # end PUBLIC functions.
    # begin PRIVATE functions. Usually no need to call them:


    def dirname (self):
        "lockname plus extension = lock dir name"
        return self.name + LOCKDIREXTENSION

    def breakLock(self):
        """Low level routine, do not call directly unless you really know why!
           
           If lock owner, just use 'unlocking'.
           Or: Just let it time out, old dir is like no dir.
           
           returns True if there was a lockdir, and rmdir was successful.
           returns False if not existed, or rmdir failed."""
        try:
            return rmdir_ReturnWhetherSuccessfullyRemoved ( self.dirname() )
        except:
            return False


    def exists (self):
        "Does a lockdir for this lockname exist?"
        return pathExists ( self.dirname() )

    def age(self):
        """total seconds since last modification.
           N.B.: Can return ERROR=-1 if simultaneous file access."""
        return pathAgeInSeconds( self.dirname() )

    def timedOut (self):
        "is last modification longer ago than 'timeout' seconds?"
        return self.age() > self.TIMEOUT

    def existsAndNotTimedOut(self):
        ".exists() and not .timedOut()"
        return (self.exists() and not self.timedOut())
    
    def startWaiting(self):
        "store first moment of trying to acquire lock, for patience condition"
        if self.startedWaitingTime == None:
            self.startedWaitingTime = time.time()
    

    def locking(self):
        """Try to create a lockdir for this lockname, by mkdir 
           ... then return true.
            
           If already existed and not timed out yet, 
           (or mkdir fails for other reasons), then return false."""
           
        self.startWaiting()
           
        if self.existsAndNotTimedOut():
            return False

        acquired = mkdir_ReturnWhetherSuccessful ( self.dirname() )
        
        if acquired:
            self.lockingTime = time.time()
            self.startedWaitingTime = None
            
        return acquired



    def stillPatience(self):
        "Waiting instance has limited patience. Return whether patience left."    
        nervousness = time.time() - self.startedWaitingTime
        return (nervousness < self.PATIENCE)  
    
    def loopWhileLocked(self):
        """Returns False if it was not locked anyway.
           Returns True if it had to wait.
        
           If locked, then test in 'checkeveryXseconds' intervals.
           (But only until patience is gone.)
           
           Then, when not locked anymore, return True.
           
           Only a helper function, used in 'LoopWhileLocked_ThenLocking'
        """
           
        if not self.isLocked():
            return False
        
        self.startWaiting()
        
        while self.isLocked() and self.stillPatience():
            time.sleep (self.CHECKEVERYXSECONDS)
        return True


    def removeIfTimedOut (self):
        "delete the lockfile after timeout"
        # TODO: how to make this atomic ??????????????
        if self.timedOut():
            self.breakLock()    

    def isLocked( self ): 
        """If locked, return True.
           If not locked or timed out, return False.
           
           Default is to delete a timedOut lockfile."
        """
        if not self.exists():
            return False
        
        if self.timedOut():
            if self.REMOVETIMEDOUT: self.removeIfTimedOut()
            return False
        
        return True # in all other cases it is locked



def getInfoLogger(ID = ""):
    "nice printing with timestamp and choosable IDs"
    
    # reload to redefine basicConfig:
    import sys, logging; reload(sys.modules['logging']); import logging
    FORMAT = '[%(asctime)s.%(msecs).03d] ' + ID + ' %(message)s'
    logging.basicConfig(format=FORMAT,  datefmt='%I:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    return logger.info 

#    logger = getLogger('[%(asctime)s.%(msecs).03d] ' + ID + ' %(message)s')
    


def testDLock():
    "Present the inner workings, and all relevant functions."

    Log = getInfoLogger()

    name = "example"
    Log("INITIALIZE DLock instance:")
    L = DLock (name)
    Log("L = %s" % L )
    Log("L.dirname = %s (pathname of the lockdir)", L.dirname() )
    Log("A hard delete; usually do not use, only at beginning perhaps:")
    Log("L.breakLock = %s (from earlier runs perhaps)" % L.breakLock() )
    Log("L.exists = %s (no lockdir because of above breakLock)", L.exists() ) 
    Log("")

    Log("EXAMPLE: locking, and see what it does:")    
    Log("locking = %s", L.locking () )
    
    Log("sleep a bit ...")
    time.sleep(1)
    
    Log("L.age = %s" % L.age ( ))
    Log("L.isLocked = %s" % L.isLocked())
    Log("L.exists = %s" % L.exists() )
    Log("")
    
    Log("EXAMPLE: Show effect of timeout on 'isLocked'")
    L.TIMEOUT = 1
    Log("L.TIMEOUT = 1")
    Log("L.isLocked = %s" % L.isLocked())
    Log("L.exists = %s (as 'isLocked' removed the timedout dir)" % L.exists())
    Log("")
    
    Log("EXAMPLE: Demonstrate loopWhileLocked()")
    L.TIMEOUT = 3
    Log("L.TIMEOUT = 3")
    Log("L.locking = %s", L.locking () )

    Log("L.loopWhileLocked() ... ")
    Log(" = %s", L.loopWhileLocked())
    Log("end loop (Hint: Study the timestamps on the left)")
    Log("L.isLocked = %s" % L.isLocked())
    Log("")
    
    Log("EXAMPLE: Try locking when already locked:")
    Log("L.locking = %s", L.locking () )
    Log("L.locking = %s (cannot because already locked)", L.locking () )
    Log("")
    
    Log("EXAMPLE: Not the instance, but 'name' of lock is deciding:")
    Log("Create new DLock instance L2:, using SAME lock-name i.e. lock-dir:" )
    L2 = DLock (name) 
    Log("L2 = %s" % L2)
    Log("(L.dirname == L2.dirname) = %s" % (L.dirname() == L2.dirname()))
    res = L2.locking ()
    Log("L2.locking = %s  (Cannot. Already locked by L, 'name' decides)" % res)
    
    Log("L2.LoopWhileLocked_ThenLocking() ...  (waiting for default timeout)")
    res = L2.LoopWhileLocked_ThenLocking()
    Log("= %s (could acquire lock after old locking timed out)", res )
    Log("L2.isLocked = %s" % L2.isLocked())
    Log("L.isLocked = %s (yes, also. Only the 'name' decides.)" % L.isLocked())
    Log("")
    
    
    Log("EXAMPLE: create situation where lack of patience ends the waiting.")
    Log("(usually this happens when many threads/process are competing,")
    Log(" but here artificially created by TIMEOUT larger than PATIENCE)")
    
    Log("L.breakLock = %s (to reset the situation)" % L.breakLock()) 
    Log("")
    L.TIMEOUT = 10
    Log("L.TIMEOUT = 10")
    Log("L.locking = %s (acquired by L)" % L.locking())
    Log("")
    Log("L2.TIMEOUT = 10")
    L2.TIMEOUT = 10
    Log("L2.PATIENCE = 4")
    L2.PATIENCE = 4 
    Log("L2.LoopWhileLocked_ThenLocking() ... ") 
    res = L2.LoopWhileLocked_ThenLocking()
    Log("= %s (gave up due to lack of patience)", res )
    Log("L.isLocked = %s" % L.isLocked())
    time.sleep(6)
    Log("L.isLocked = %s" % L.isLocked())
    Log("End. More examples in the other files.")

def print_Ramdisk_Manual():
    """Measured:
    500 threads waiting for 1 DLock - overhead by threading, print, and locking:
    Windows with HD: min=0.0063 max=0.0704 median=0.0279 mean=0.0274 stdv=0.0131
    Linux with SSD:  
    DLock in RAM:    
    So: When time critical, put DLock in RAM!
    """

    print "\nN.B.:"
    print"""On Linux a (tiny!) ramdisk can reduce the overhead a little bit.
    modprobe rd
    mkfs -q /dev/ram1 100
    mkdir -p /ramcache
    mount /dev/ram1 /ramcache
    df -H | grep ramcache"""
    print "Then you simple use lockname = '/ramcache/lockname'"
    print


def howToUse(secs = 9):
    """short version how to use DLocks: A, B, C (, D)."""
     
    L = DLock( "LOCKNAME" ) # step A: instantiate, with name
    acquired = L.LoopWhileLocked_ThenLocking() # step B: waitThenTryLocking
    if acquired:
        time.sleep(secs)    # Step C: Use scarce resource (max TIMEOUT secs!)
        L.unlocking()       # Step D: unlocking = resource free for next user
    return acquired         # Optional: Tell the caller.

if __name__ == '__main__':
    # print_Ramdisk_Manual()
    
    testDLock()
    howToUse(1)

