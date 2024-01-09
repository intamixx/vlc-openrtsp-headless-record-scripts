#!/usr/bin/python3

import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time
import subprocess
import pycurl
import sys
import os
import socket
import syslog

from datetime import datetime
from threading import Thread
import subprocess, threading, sys, os, signal

# datetime object containing current date and time
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
print("date and time =", dt_string)

def getNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.connect(('<broadcast>', 0))
    return s.getsockname()[0]

localip = getNetworkIp()

def front():
    hostip = '192.168.0.91'
    port = '2081'
    url = "http://{}:{}/tmpfs/auto.jpg".format(hostip, port)
    return hostip, port, url
def tree():
    hostip = '192.168.0.92'
    port = '2082'
    url = "http://{}:{}/tmpfs/auto.jpg".format(hostip, port)
    return hostip, port, url
def back():
    hostip = '192.168.0.93'
    port = '2083'
    url = "http://{}:{}/tmpfs/auto.jpg".format(hostip, port)
    return hostip, port, url
def container():
    hostip = '192.168.0.94'
    port = '2084'
    url = 'http://{}:{}/Streaming/channels/1/picture'.format(hostip, port)
    return hostip, port, url
def frontgate():
    hostip = '192.168.0.95'
    port = '2085'
    url = 'http://{}:{}/Streaming/channels/1/picture'.format(hostip, port)
    return hostip, port, url
def errhandler():
    print ("Unknown Camera, Run with -h for help")
    sys.exit(1)

cameras = { "front" : front,
                "tree" : tree,
                "back" : back,
                "container" : container,
                "frontgate" : frontgate
}

def check_camera(hostip, port, camera):
        # Create a TCP socket
                s = socket.socket()
                s.settimeout(3)
                syslog.syslog(syslog.LOG_INFO, "Attempting connect -> %s Kam" % camera)
                print(("Attempting to connect to %s on port %s") % (hostip, port))
                try:
                        s.connect((hostip, port))
                        syslog.syslog(syslog.LOG_INFO, "Connected -> %s:%s" % (hostip, port) )
                        print(("Connected to %s on port %s") % (hostip, port))
                        return True
                except socket.timeout:
                        syslog.syslog(syslog.LOG_INFO, "Caught a connection timeout -> %s" % (hostip) )
                        print(("Caught a connection timeout %s") % (hostip))
                        #os._exit(1)
                        return False
                except socket.error as e:
                        syslog.syslog(syslog.LOG_INFO, "Connect Failed -> %s:%s" % (hostip, port) )
                        print(("Connection to %s on port %s failed: %s") % (hostip, port, e))
                        #os._exit(1)
                        return False

def get_kam_image(camera):
        ( hostip, port, url ) = cameras.get(camera, errhandler)()
        print(("Camera: %s\nIP: %s\nHTTP Port: %s") % (camera, hostip, port))
        port = int(port)
        check = check_camera(hostip, port, camera)

        if check == True:
                timeNow = time.strftime("%Y%m%d%H%M%S")
                output_directory = '/var/www/html/doorbell'
                filename = ("%s-%s.jpg") % (camera, timeNow)
                output_filename = ("%s/%s") % (output_directory, filename)
                #headers = ['Authorization: Basic YWxxxxxxxxxIzNA==']

                username = 'user'
                password = 'Numark!234'
                c = pycurl.Curl()
                c.setopt(c.SSL_VERIFYPEER, False)
                c.setopt(c.VERBOSE, True)
                c.setopt(c.URL, url)
                c.setopt(c.TIMEOUT, 5)
                c.setopt(c.USERAGENT, 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.0.3705; .NET CLR 1.1.4322)')
                c.setopt(c.HTTPAUTH, c.HTTPAUTH_DIGEST)
                c.setopt(c.USERPWD, "%s:%s" % (username, password))
                c.setopt(c.HEADER, 0)

                print (url)
                with open(output_filename, 'wb') as f:
                        c.setopt(c.WRITEFUNCTION, f.write)
                        try:
                                c.perform()
                        except pycurl.error as e:
                                print ('An error occurred: ', e)
                                c.close()
                                #sys.exit(2)

                # HTTP response code, e.g. 200.
                print('Status: %d' % c.getinfo(c.RESPONSE_CODE))
                # Elapsed time for the transfer.
                print('Time: %f' % c.getinfo(c.TOTAL_TIME))

                if c.getinfo(c.RESPONSE_CODE) == 200:
                        print ("Successful get of camera image")
                        link = ("http://%s/doorbell/%s" % (localip, filename))
                        return link
                else:
                        print ("Error downloading camera image")
                        link = ("null")
                c.close()
        else:
                link = ("%s Kam unavailable" % camera)

        return link

def run1():
        link1 = get_kam_image("frontgate")
        return link1

def run2():
        link2 = get_kam_image("container")
        return link2

def blinkled():
        GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)
        print ("LED off")
        GPIO.output(18,GPIO.HIGH)
        time.sleep(0.1)
        print ("LED on")
        GPIO.output(18,GPIO.LOW)

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            try:
                print ('Thread started')
                self.process = subprocess.Popen(self.cmd, shell=True)
                self.output, self.error = self.process.communicate()
                print ('Thread finished')
            except:
                self.error = traceback.format_exc()
                self.status = -1

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            print ('Timeout. Terminating process')
            self.process.terminate()
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            os.kill(os.getpid(self.process.pid), signal.SIGTERM)
            thread.join()
        print (self.process.returncode, self.output, self.error)
        result[thread] = self.process.returncode
        return (self.process.returncode)

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def button_callback(channel):
    if GPIO.input(10):
        print("Button was pushed!")
        launchthreads()
        time.sleep(2)
        launchthreads()

def launchthreads():
        # datetime object containing current date and time
        now = datetime.now()
        #print("now =", now)
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print("date and time =", dt_string)

        print("In main block")
        t1 = ThreadWithReturnValue(target=run1)
        threads = [t1]
        t2 = ThreadWithReturnValue(target=run2)
        threads += [t2]
        t3 = ThreadWithReturnValue(target=blinkled)
        threads += [t3]

        t1.start()
        t2.start()
        t3.start()

#       print(t1.join())
        link1 = t1.join()
#       print(t2.join())
        link2 = t2.join()

#       for tloop in threads:
#           print ("***************")
#           print (tloop.join())
#           tloop.join()

        print("End of main block")

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

#       link1 = get_kam_image("frontgate")
#       link2 = get_kam_image("container")
        print ("------------------")
#       print (link1)
#       print (link2)
        timeout = 5
        threads = []
        global result
        result = {}
        chatids = ["5810526317", "5693732711"]
        for chatid in chatids:
                try:
                        cmdstr = "/usr/local/bin/telegram -t 5878417338:AAFPJX55XJVxxxxxxxxxxl9Zaey59eZWiY -c %s 'DoorBell Pushed @ %s\r\n Images - %s | %s'" % (chatid, dt_string, link1, link2)
                        command = Command(cmdstr)
                        t = threading.Thread(target=command.run, args=(timeout,))
                        print (t)
                        threads.append(t)
                        t.start()
                        t.join()
#                main_thread = threading.currentThread()
#                for t in threading.enumerate():
#                        print ("- Starting %s" % t.getName())
#                        if t is main_thread:
#                               continue
#                        t.join()
                except:
                        print ("Something went wrong creating a thread")
                        #sys.exit(1)

        print (result)
        for key, value in result.items():
                if value != 0:
                        print ("Error occurred running command")
                        #sys.exit(1)
                else:
                        print ("Command run successfully")
                        #sys.exit(0)

        time.sleep(1)

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

GPIO.add_event_detect(10,GPIO.FALLING,callback=button_callback, bouncetime=500) # Setup event on pin 10 rising edge

a = 1
while a==1:
     time.sleep(1)
#    launchthreads()
#    time.sleep(20)
#    message = input("Press enter to quit\n\n") # Run until someone presses enter

GPIO.cleanup() # Clean up
