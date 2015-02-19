'''
lockbydir_concurrent.py - Locking across processes, live example. 

@contact:  python (at) AndreasKrueger (dot) de
@since:    23 Jan 2015

@license:  Never remove my name, nor the examples - and send me job offers.
@bitcoin:  I am poor, send bitcoins: 1MT9gazTyodKVU3XFEUgR5aCwG7rXXiuWC Thx! 

@requires: lockbydir.py         # the DLock class
@requires: lockbydir_OS.py      # lockdir OS-level routines

@call:     run this whole file, or call 'startSeveral(4)'
@return:   stdout

@summary 

Concurrent usage of 1 scarce resource, moderated by a DLock.
 

Example 1: Real Multi-Processing. Verbose Logging. 

To show how DLock can lock across independent processes, 4 copies of this
script are spawned. They simultaneously write to stdout. The simple example:

4 sleepers are sharing 1 narrow bed, so always only 1 sleeper can sleep; 
the others must wait - or get impatient, and give up. 

There is a small probability that one sleeper forgets to unlock after use,
to demonstrate the lock TIMEOUT. There is limited PATIENCE also, so that
at least one of the sleepers will give up without ever acquiring the lock/bed.


Example 2: Massive hammering. Hundreds of consumers of 1 resource.

For simplicity, implemented multi-threading. Last test if DLock is safe.

n sleepers are started as threads, all wait for 1 bed, which is DLock'ed.
After one sleeper finishes, he notes the time. At the end, all these times
are compared, to show that there was never an overlap of sleepers.


For the inner workings of DLock, see the other example lockbydir.testDLock().

My github For feature requests, ideas, suggestions, appraisal, criticism:

@home   https://github.com/drandreaskrueger/lockbydir
@issues https://github.com/drandreaskrueger/lockbydir/issues
@wiki   https://github.com/drandreaskrueger/lockbydir/wiki 
'''

RUN_EXAMPLE = 1  # 1 or 2

RAMDISK = "/ramcache/"   # see lockbydir.print_Ramdisk_Manual  
RAMDISK = ""             # if you have such a ramdisk, uncomment this line

from lockbydir import DLock, getInfoLogger, TIMEOUT, print_Ramdisk_Manual

######################################################################
# concurrent example 1
# Multi-processing! This was the goal of the whole game :-)

# Same example as usually: Several sleepers are competing for 1 bed:
######################################################################

import time, subprocess, sys, random

SLEEPTIME = 6                # how long each sleeper will use the bed 
FORGETTINGPROBABILITY = 0.25 # how likely to forget unlocking after use
LOCKNAME = "oneBed"          # name the lock

def createStress(L):
    """This is only to create the artificial situation in which  
       processes give up early. Demonstration purposes only."""
        
    L.CHECKEVERYXSECONDS = 0.01     # check very often  
    L.PATIENCE = 13 # low patience, to have case in which acquisition fails
    

def howToUse(secs = 9):
    """short version how to use DLocks: A, B, C (, D). Just a reminder."""
     
    L = DLock( "LOCKNAME" ) # step A: instantiate, with name
    acquired = L.LoopWhileLocked_ThenLocking() # step B: waitThenTryLocking
    if acquired:
        time.sleep(secs)    # Step C: Use scarce resource (max TIMEOUT secs!)
        L.unlocking()       # Step D: unlocking = resource free for next user
    return acquired         # Optional: Tell the caller. 
      

def compete( arg ):
    """Creates DLock instance, acquires lock, sleeps, (then unlocks).
       Verbose explanation how to use the DLocks: A, B, C (, D). 
       
       See comments:
    """
    Log = getInfoLogger("[pId=%(process).5d]") # nice printing with timestamp
    Log("(%s   ) started." % arg); 
    
    # STEP A: create DLock instance
    L = DLock( LOCKNAME )
    Log("(%s.A ) created Lock instance  L = DLock('%s')" % (arg, LOCKNAME))

    # change settings, only here for this demonstration:
    createStress (L) # other way to redefine parameters: FastDLock (see below) 

    # STEP B: 
    # Wait for unlocked, then locking. If already unlocked, immediate locking.
    Log("(%s.B1) entering L.LoopWhileLocked_ThenLocking" % (arg))
    acquired = L.LoopWhileLocked_ThenLocking()
    time.sleep(0.01) # only necessary to give other loggers a chance to catch up
    Log("(%s.B2) L.LoopWhileLocked_ThenLocking ended with = %s" % (arg, acquired) )
    if not acquired:
        Log("(%s   ) failed to get resource, due to lack of my patience ... "  % (arg))
        result = "I NEVER slept :-("
        
    else:
        # STEP C: use the scarce resource:
        Log("(%s.C1) USING THE BED for %.1f seconds  ... "  % (arg, SLEEPTIME))
        time.sleep(SLEEPTIME)
        Log("(%s.C2) end of sleep!"  % (arg))
        result = "I slept very well :-)"
    
        if random.random() > FORGETTINGPROBABILITY:
            # Step D: unlocking 
            Log("(%s.D ) L.unlocking = %s" %  (arg, L.unlocking()))
        else:
            Log("(%s.D ) unlocking FORGOTTEN. Sorry. You need to wait for timeout." % arg)
            # After 'timeout' seconds, it automatically times out.

    Log("(%s   ) ending: %s" % (arg, result))


def spawnAnotherPython(i):
    """opens this script again, but with an argument 'i'. New process."""
    
    return subprocess.Popen("python %s %d" % (__file__, i), shell=True)

def startSeveral( N ):
    "Spawns several independent python processes."
    
    Log = getInfoLogger('[pId=%(process).5d]') # nice printing with timestamp
    
    Log("EXAMPLE: Several processes are competing for the same resource:" )
    Log("There is only 1 bed, but %d sleepers. ;-)" % N )
    Log("")

    Log("These are the outputs of the %d subroutines:" % N)
    
    subroutines = [spawnAnotherPython(i) for i in range(1,1+N)] # see above
        
    # wait until all subroutines are finished:
    for r in subroutines:
        r.wait()    # in case of subprocess.Popen
        
    Log("All %d subroutines ended." % N)
    empty = not DLock(LOCKNAME).isLocked()
    Log("Bed is empty = %s." % empty)
    
    if not empty:
        t = TIMEOUT - SLEEPTIME
        Log("Ouch. Someone forgot to unlock, so")
        Log("wait another %d seconds, and test again:" % t)
        time.sleep(t)
        Log("Bed is empty = %s." % (not DLock(LOCKNAME).isLocked()))


def startSpawner():
    startSeveral( 4 )

##################################################
# concurrent example 2
# hammering test, to check if all is well now.
# Hundred of consumers try to get 1 resource.
# For simplicity, implemented multi-threading.
##################################################

import timeit

class FastDLock (DLock):
    "This is actually a good way to change the default parameters"
    def __init__(self, name):
        DLock.__init__(self, name)
        
        self.CHECKEVERYXSECONDS = 0.005 # check lock status very often
        self.PATIENCE = 5               # no one waits longer than this
        
    
def tryToGetIntoTheOneBed(lockname, secs, timestamps, Log ):
    "Consumer thread. Hundreds of these will be started."

    L = FastDLock(lockname)  # step A: instantiate, with name 
    acquired = L.LoopWhileLocked_ThenLocking() # step B: waitThenTryLocking

    if acquired:
        time.sleep(secs)     # Step C: Use scarce resource 
        timestamps.append(timeit.default_timer()) # store current time
        good = L.unlocking() # Step D: unlocking = resource free for next user
        if not good: raise Exception ("oh shit") # :-) 
        Log("yes, me slept.")
    else:
        Log("NO, me not.")
        

def massiveNumberOfUsers(n, secs):
    """n consumers competing for 1 resource,
       to use it for 'secs' seconds, then store the end time.
       
       At the end, all those end times are analyzed for their
       consecutive differences, to see if a lock violation happened.
    """
    
    lockname = RAMDISK + "oneNarrowBedForManySleepers"
    timestamps = []
    
    Log = getInfoLogger('[thrId=%(thread).5d]') # nice printing with timestamp
    
    import threading
    # create 'n' such threads
    t = [threading.Thread(target = tryToGetIntoTheOneBed, 
                          args = (lockname, secs, timestamps, Log)) 
         for _ in range(n)]
    
    for thr in t: thr.start()
    for thr in t: thr.join()    # wait for all to finish
    
    ns = len(timestamps)        # number of those who got lucky
    
    timestamps.sort()           
    diffs = [timestamps[i] - timestamps[i-1]  # time differences  
             for i in range(1, ns)  ]

    diffs = map ( lambda x: round (x, 4) , diffs) # round all to 0.0001  
    diffs.sort()      # better for reading
    
    print "Result: %d succeeded in acquiring the lock" % ns  , 
    print "and %d had not enough patience to wait longer." % (n - ns)
    print
    print "Differences between %d recorded sleep end times, sorted. " % ns
    print "If all of these are > %f then the DLock has worked fine." % secs
    print diffs
    
    print "overhead by threading, print, and locking:", 
    diffs = [d - secs for d in diffs] 
    theMin, theMax = min(diffs), max(diffs)
    print "min=%.4f max=%.4f" % (theMin, theMax),
    try:
        # pip install statistics 
        import statistics
    except: pass
    else:
        mean = statistics.mean(diffs)
        median = statistics.median(diffs)
        stdev = statistics.stdev(diffs)
        print "median=%.4f mean=%.4f stdv=%.4f" % (median, mean, stdev),
    print
        
    
def startMassive():
    massiveNumberOfUsers(300, 0.05)
    print_Ramdisk_Manual()
    
def startMassive_ForGitPlayer():
    print "\n\nSorry, the PythonAnywhere GITplayer only allows to spawn very few threads."
    print "Clone the Git to your own computer to see this work with 300 threads:"
    print "https://github.com/drandreaskrueger/lockbydir\n\n"
    massiveNumberOfUsers(11, 0.5)
    print_Ramdisk_Manual()

if __name__ == '__main__':

    if RUN_EXAMPLE == 1:    
        if len(sys.argv) == 1:        # without an argument, start spawner.
            startSpawner()
        else:                         # if script is called with an argument,
            compete( sys.argv [1] )   # then start a competing sleeper

    if RUN_EXAMPLE == 2:
        startMassive()                # last test before the Autobahn ;-)
        
