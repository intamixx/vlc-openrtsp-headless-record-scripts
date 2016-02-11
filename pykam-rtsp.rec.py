#!/usr/bin/python

# Copyright (c) Intamixx

"""
Custom record facility to record from rtsp cameras using ffmpeg.
Kills ffmpeg using sigint after recording duration has lapsed.

python kamrecord.py -c <camera: front, tree, back> -d <record duration in seconds>
"""

# Import required libraries, raise an exception if not installed
try:
        import syslog
        import time
        import getopt
        import sys
        import os
        import socket
except ImportError as e:
        print "\n%s is not installed. Please install it before running this script." % (e)
        exit (1)

from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL, SIGINT
from subprocess import PIPE, Popen

def front():
    hostip = '192.168.10.1'
    port = '2091'
    return hostip, port
def tree():
    hostip = '192.168.10.2'
    port = '2092'
    return hostip, port
def back():
    hostip = '192.168.10.3'
    port = '2093'
    return hostip, port
def errhandler():
    print "Unknown Camera, Run with -h for help"
    sys.exit(1)

cameras = { "front" : front,
                "tree" : tree,
                "back" : back,
}

def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1, env = None):
    '''
    Run a command with a timeout after which it will be forcibly
    killed.
    '''
    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    p = Popen(args, shell = shell, cwd = cwd, stdout = PIPE, stderr = PIPE, env = env)
    syslog.syslog(syslog.LOG_INFO, "Running %s -> Pid [%d] " % (ffmpeg, p.pid) )
    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        if timeout != -1:
            alarm(0)
    except Alarm:
        pids = [p.pid]
        if kill_tree:
            pids.extend(get_process_children(p.pid))
        for pid in pids:
            # process might have died before getting to this line
            # so wrap to avoid OSError: no such process
            syslog.syslog(syslog.LOG_INFO, "Killing %s -> Pid [%d] " % (ffmpeg, p.pid) )
            try: 
                kill(pid, SIGINT)
            except OSError:
                pass
        return -2, '', ''
    return p.returncode, stdout, stderr

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True,
              stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]

def check_camera(hostip, port, camera):
        # Create a TCP socket
                s = socket.socket()
		s.settimeout(10)
                syslog.syslog(syslog.LOG_INFO, "Attempting connect -> %s Kam" % camera)
                print "Attempting to connect to %s on port %s" % (hostip, port)
                try:
                        s.connect((hostip, port))
                        syslog.syslog(syslog.LOG_INFO, "Connected -> %s:%s" % (hostip, port) )
                        print "Connected to %s on port %s" % (hostip, port)
                        return True
                except socket.timeout:
                        syslog.syslog(syslog.LOG_INFO, "Caught a connection timeout -> %s" % (hostip) )
                        print "Caught a connection timeout %s" % (hostip)
                        os._exit(1)
                        return False
                except socket.error, e:
                        syslog.syslog(syslog.LOG_INFO, "Connect Failed -> %s:%s" % (hostip, port) )
                        print "Connection to %s on port %s failed: %s" % (hostip, port, e)
                        os._exit(1)
                        return False

def main(argv):
    camera = ''
    duration = ''
    hostip = ''
    port = ''
    service = '12'
    framerate = '25'
    quality = '1'
    username = 'user'
    password = 'pass'
    timeNow = time.strftime("%Y%m%d%H%M%S")
    directory = '/mnt/videos'

    try:
        opts, args = getopt.getopt(argv,"hc:d:",["camera=","duration="])
    except getopt.GetoptError:
     print '%s -c <camera: front, tree, back> -d <record duration in seconds>' % format(os.path.abspath(__file__))
     sys.exit(2)
    for opt, arg in opts:
     if opt == '-h':
        print '%s -c <camera: front, tree, back> -d <record duration in seconds>' % format(os.path.abspath(__file__))
        sys.exit()
     elif opt in ("-c", "--camera"):
        camera = arg
     elif opt in ("-d", "--duration"):
        duration = arg
    if not camera or not duration:
        print '%s -c <camera: front, tree, back> -d <record duration in seconds>' % format(os.path.abspath(__file__))
        sys.exit(1)
    else:
        duration = int(duration)

    # locate ffmpeg program
    cmd_exists = lambda x: any(os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
    try:
        result = cmd_exists('%s' % ffmpeg)
    except e: sys.exit('ERROR: Error locating %s' % ffmpeg)
    if result == False:
        sys.exit('ERROR: Error %s not found' % ffmpeg)

    # check directory exists
    result = os.path.exists('%s' % directory)
    if result == False:
        syslog.syslog(syslog.LOG_INFO, "Directory %s not Found" % directory )
        print 'Directory %s not Found' % (directory)
        try:
                 os.makedirs('%s' % directory)
        except OSError:
                syslog.syslog(syslog.LOG_INFO, "Could not create directory %s" % directory )
                sys.exit('ERROR: Could not create directory %s' % directory)

    ( hostip, port ) = cameras.get(camera, errhandler)()

    print "Camera: %s\nIP: %s\nRTSP Port: %s" % (camera, hostip, port)

    port = int(port)
    check = check_camera(hostip, port, camera)

    syslog.syslog(syslog.LOG_INFO, "Running %s -> Record %s Kam" % (ffmpeg, camera) )
    runStr = "%s -rtsp_transport tcp -y -i rtsp://%s:%s@%s:%s/%s -r %s -an /%s/%s-%s.mp4" % (ffmpeg, username, password, hostip, port, service, framerate, directory, camera, timeNow)

    print runStr
    ( retCode, stdout, stderr ) = run(runStr, shell = True, timeout = duration)
    retCode = int(retCode)
    if (retCode == -2):
        print "Command exited normally"
        sys.exit(0)
    else:
        print "Command failed"
        print "Return Code: %s" % retCode
        print "%s\n%s" % (stdout, stderr)
        sys.exit(1)

if __name__ == '__main__':
    ffmpeg = 'ffmpeg'
    main(sys.argv[1:])
