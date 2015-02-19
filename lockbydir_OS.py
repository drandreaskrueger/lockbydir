'''
lockbydir_OS.py - OS Level routines, for DLock = Locking across processes. 

@contact:  python (at) AndreasKrueger (dot) de
@since:    23 Jan 2015

@license:  Never remove my name, nor the examples - and send me job offers.
@bitcoin:  I am poor, send bitcoins: 1MT9gazTyodKVU3XFEUgR5aCwG7rXXiuWC Thx! 

@requires: lockbydir.py                    # the higher DLock routines 
@requires: lockbydir_concurrent.py         # for multiprocess example   

@call:     run
@return:   stdout (2 tests)

@summary 

DLock is an easy to use lock mechanism, 
with lock timeout, and limited waiting patience.

For the higher level routines, and more explanations, see lockbydir.py 

This file contains all routines for the OS level:
* filepath existence, modification date, age
* mkdir
* rmdir


See my github For feature requests, ideas, suggestions, appraisal, criticism:
@issues https://github.com/drandreaskrueger/lockbydir/issues
@wiki https://github.com/drandreaskrueger/lockbydir/wiki 
'''

RAMDISK = "/ramcache/"   # see lockbydir.print_Ramdisk_Manual  
RAMDISK = ""             # if you have such a ramdisk, uncomment this

# dir extension:
LOCKDIREXTENSION = ".lockdir"

# do not change:
ERROR = -1             # when filedate not accessible = other process writes.

import os, datetime, math


def pathExists (pathname):
    "does the path exist?"
    return os.path.exists(pathname)

def pathModificationDate(pathname):
    "last modification date of path, as datetime.datetime"
    t = os.path.getmtime(pathname)
    return datetime.datetime.fromtimestamp(t)

def testing_pathAge_onWindows():
    "Demonstration why the next function is unfortunately necessary, on Windows"

    print "Try this several times - on windows. "
    print "Sometimes 'age' turns out negative\n"
    
    pathname = "juhu-lashflahsdlhdaios42"
    try: os.rmdir(pathname)
    except: pass
    
    now1 = datetime.datetime.now()
    os.mkdir(pathname)
    pathTimestamp = pathModificationDate(pathname)
    now2 = now = datetime.datetime.now()
    
    print "before:   ", now1
    print "filedate: ", pathTimestamp
    print "after:    ", now2 
                    
    age = (now - pathTimestamp).total_seconds() 
    print "                      age = %+.6f" % age

    # windows precision of .now() is milliseconds
    # but file date has microseconds precision:

    print "\ncorrection of microseconds to milliseconds precision:"    
    if os.name == "nt":
        microseconds = pathTimestamp.microsecond
        print microseconds
        # strip away microsecond digits:
        microseconds = int ( math.floor ( microseconds / 1000) * 1000 ) 
        print microseconds
        pathTimestamp = pathTimestamp.replace (microsecond = microseconds)
        age = (now - pathTimestamp).total_seconds() 
        print "                      age = %+.6f" % age
    else:
        print "only necessary on windows"
        
    os.rmdir(pathname)

def millisecondsPrecisionOnly (DT):
    """Windows precision of .now() is milliseconds
       but file date has precision of microseconds. 
       This here corrects for that, by stripping away digits.
       
       All this is wasting only 0.00001 - 0.00002 seconds, 
       including the if os.name == "nt" ... so no problem!
    """
    microseconds = DT.microsecond
    # strip away microsecond digits:
    microseconds = int ( math.floor (microseconds/1000) * 1000 )
    return DT.replace (microsecond = microseconds)


def pathAgeInSeconds(pathname):
    "Last modification of path was how many seconds ago?"
    try:
        pathTimestamp = pathModificationDate(pathname)
    except:
        age = ERROR # e.g. WindowsError: [Error 5] Access denied: '...lockdir'
    else:
        now = datetime.datetime.now()
        if os.name == "nt":
            pathTimestamp = millisecondsPrecisionOnly (pathTimestamp) 
        age = ( now - pathTimestamp ).total_seconds() 

    return age


## locking implemented as (success of) directory creation and removal.
## read more at 
##   http://en.wikipedia.org/wiki/File_locking#Lock_files
##   http://wiki.bash-hackers.org/howto/mutex

try:
    from exceptions import WindowsError as OSError
except ImportError:
    ## on Linux: "ImportError: cannot import name WindowsError"
    from exceptions import OSError

def mkdir_ReturnWhetherSuccessful(pathname):
    try:
        os.mkdir(pathname)
        return True
    except OSError as e:
    # except Exception as e:
        # print type(e), e.errno, e, 
        ## Windows:  
        ##   <type 'exceptions.WindowsError'>    17 [Error 183] Cannot create a file when that file already exists: 'testing'
        ##   or when concurrent:                 13 WindowsError(5, 'Access is denied')
        ## Linux:    <type 'exceptions.OSError'> 17 [Errno 17] File exists: 'testing' 
        ##   or when concurrent & virtualbox     71, OSError(71, 'Protocol error')
        ##   or when full:                           OSError: [Errno 28] No space left on device: '/ramcache/oneNarrowBedForManySleepers.lockdir'
        if e.errno in (17,13,71): 
            return False
        else: 
            raise e
    
def rmdir_ReturnWhetherSuccessfullyRemoved(pathname):
    try:
        os.rmdir(pathname)
        return True
    except OSError as e:
    # except Exception as e:
        # print type(e), e.errno, e,  
        ## Windows: <type 'exceptions.WindowsError'>  2  [Error 2] The system cannot find the file specified: 'testing' (result = False)
        ##          or when concurrent:              13 WindowsError(5, 'Access is denied')
        ## Linux:   <type 'exceptions.OSError'>       2 [Errno 2] No such file or directory: 'testing' 
        ##   or when concurrent & virtualbox         71, OSError(71, 'Protocol error')
        if e.errno in (2,13,71): 
            return False
        else: 
            raise e


########## 2 tests: ###########################################

def test_mkdirRmdir():
    "Should print: done True True False True False False."

    pathname ="testing"
    print "reset situation:", 
    _ = rmdir_ReturnWhetherSuccessfullyRemoved(pathname) 
    print "done"
    print
        
    print "mkdir attempt 1:",
    print "result = %s" % mkdir_ReturnWhetherSuccessful(pathname)
    print
    
    print "exists, ageInSeconds = %s, %s" % (pathExists(pathname), pathAgeInSeconds(pathname)) 
    print "mkdir attempt 2:",
    print "result = %s" %  mkdir_ReturnWhetherSuccessful(pathname)
    print
    
    print "rmdir attempt 1:",
    print "result = %s" %  rmdir_ReturnWhetherSuccessfullyRemoved(pathname)
    print
    
    print "exists, ageInSeconds = %s, %s" % (pathExists(pathname), pathAgeInSeconds(pathname)) 
    print "rmdir attempt 2:",
    print "result = %s" %  rmdir_ReturnWhetherSuccessfullyRemoved(pathname)
    print

def mkdirRmdir(pathname, Q):
    """Makes and removes a dir. Catches all yet uncaught exceptions. 
       Returns results, or ErrorNumbers, by appending to Q"""
       
    try:
        res1 = mkdir_ReturnWhetherSuccessful(pathname)
    except Exception as e:
        res1 = (e.errno, e)
        
    try:
        res2 = rmdir_ReturnWhetherSuccessfullyRemoved(pathname)
    except Exception as e:
        res2 = (e.errno, e)
        
    Q.append( (res1, res2) )

def test_mkdirRmdirConcurrent(n):
    """Simulatenous operations, to see which other errornumbers might come up.
       If results are only True and False, all is good, and taken care of."""
    
    import threading
    Q, pathname = [], "testing"

    t  = [threading.Thread( target = mkdirRmdir, args=(pathname, Q,)) 
          for _ in range(n)]
    
    for thr in t: thr.start() 
    for thr in t: thr.join() # wait until all threads finished 

    print Q

def tests():
    print "\nlockbydir.py OS-level routines. Tests."
    print "\nTest 1:\n"
    test_mkdirRmdir()
    print "\nTest 2:\n"
    test_mkdirRmdirConcurrent(10)
    
    
    
    
if __name__ == '__main__':
    ## testing_pathAge_onWindows()
    tests()

