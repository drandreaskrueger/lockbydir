# lockbydir.py = Locking across processes. Using lockdir existence & age.

### @summary 

An easy to use lock mechanism, with lock timeout, and limited waiting patience.

### @usage

    L = DLock( "LOCKNAME" ) # step A: instantiate, with name
    acquired = L.LoopWhileLocked_ThenLocking() # step B: waitThenTryLocking
    if acquired:
        time.sleep(1)       # Step C: Use scarce resource (maximum for TIMEOUT secs!)
        L.unlocking()       # Step D: unlocking = resource free for next user
    return acquired         # Optional: Tell the caller. 

### @motivation

I want locking of the django DB, across concurrent uwsgi processes, for any underlying DB. See posting: http://stackoverflow.com/q/28030536/3693375 I got great hints, and learnt a lot. But when no one could really help me to the end, I created this class 'DLock'. 

### @mechanism:

A lock is represented by a lockdir, in the current directory (or a RAMDISK).

* While it exists, and its filedate is recent, the lock is 'locked'.
* If the file does not exist, or is timed out, the lock is 'unlocked'.

Users need not care about the lockdir, but access the lock by two simple functions: 
* **.LoopWhileLocked_ThenLocking()** and 
* **.unlocking()**

### @parameters

TIMEOUT, and PATIENCE can be changed in each DLock instance, or by subclassing DLock.

* TIMEOUT: Seconds after which the lock opens automatically.
* PATIENCE: Seconds after which no more hope to acquire the lock. 

### @examples

* Shortest possible usage is in howToUse().
* The inner workings are well explained in testDLocks().
* Parallel processes are demonstrated in 2 examples in 'lockbydir_concurrent.py'. 

### @liveplayer
You can see the examples running live(!) in a GITplayer, thanks to PythonAnywhere!

* [testDLock() (inner workings)](https://www.pythonanywhere.com/gists/4b0b06bf9c13d8e5ea76/gistfile1.txt/python2/)
* [lockbydir_concurrent.py example 1 (several processes use same lock)](https://www.pythonanywhere.com/gists/6133112519b52eb435c2/gistfile1.txt/python2)
* [lockbydir_concurrent.py example 2 (massive hammering)](https://www.pythonanywhere.com/gists/d0209dd72d66efdb2c8f/gistfile1.txt/python2)

Or you download it, and start all 3 examples like this:  

    git clone https://github.com/drandreaskrueger/lockbydir.git
    cd lockbydir
    python lockbydir.py 
    python lockbydir_concurrent.py 
    python -c "import lockbydir_concurrent; lockbydir_concurrent.startMassive()"
    
@note:     Tested on Python 2.7.5. Works on Windows and Linux.

@requires: lockbydir.py, lockbydir_OS.py, lockbydir_concurrent.py

@since:    23 Jan 2015, last change: See commit/file date    

### @related:
http://stackoverflow.com/a/21444311/3693375 and http://stackoverflow.com/a/28532580/3693375 and probably http://stackoverflow.com/q/1348026/3693375

- - -
### @human

@contact:  python (at) AndreasKrueger (dot) de   

@license:  Never remove my name, nor the examples - and send me job offers.

@todo:     I am poor, send bitcoins: 1MT9gazTyodKVU3XFEUgR5aCwG7rXXiuWC Thx! 

