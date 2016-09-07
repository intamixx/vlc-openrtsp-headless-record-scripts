#!/usr/bin/python

# Copyright (c) Intamixx

"""
Daemonize pyinotify's notifier for watching camera directories and launching record script
"""

# Import required libraries, raise an exception if not installed
try:
        import functools
        import sys
        import os
        import pyinotify
        import subprocess
        import syslog
        import time
        import shlex
except ImportError as e:
        print "\n%s is not installed. Please install it before running this script." % (e)
        exit (1)

cameras = ['front', 'tree', 'back']

class Counter(object):
    """
    Simple counter.
    """
    def __init__(self):
        self.count = 0
    def plusone(self):
        self.count += 1

class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
                print "Creating:", event.pathname
                for camera in cameras:
                        if camera in event.pathname:
                                syslog.syslog(syslog.LOG_INFO, "Running %s %s" % (camera, event.pathname) )
                                runCMD('%s' % camera)

        def process_IN_DELETE(self, event):
                print "Removing:", event.pathname

def runCMD(camera):
    cmd = "/usr/bin/python /home/vyos/scripts/pykam-rtsp-rec.py -c %s -d 32" % camera
    syslog.syslog(syslog.LOG_INFO, "Checking CMD %s is running ..." % cmd)
    process = os.popen("ps ax -o pid,cmd | grep -i \'%s\' | grep -v grep" % cmd).read()

    if (process):
        print process
        process = process.lstrip(' ')
        process = process.rstrip()
        (pid, prog) = process.split(' ',1)
        syslog.syslog(syslog.LOG_INFO, "Program CMD %s [%s] is already running! ..." % (prog, pid) )
    else:
        p = subprocess.Popen(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        syslog.syslog(syslog.LOG_INFO, "Launching CMD %s [%s]" % (cmd, p.pid) )

wm = pyinotify.WatchManager()
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE # watched events

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

dateNow = time.strftime("%Y%m%d")

# Change watch directories here
watch1 = "/mnt/deracam-front/%s/images" % dateNow
watch2 = "/mnt/deracam-tree/%s/images" % dateNow
watch3 = "/mnt/deracam-back/%s/images" % dateNow

wm.add_watch([watch1, watch2, watch3], mask, rec=True)

#on_loop_func = functools.partial(on_loop, counter=Counter() )
try:
        notifier.loop(daemonize=True, pid_file='/tmp/pykamnotify.pid', stdout='/tmp/pykamnotify.log', stderr='/tmp/pykamnotify.log')
except pyinotify.NotifierError, err:
        print >> sys.stderr, err
