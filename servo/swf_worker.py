# (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

import threading
import servo.config as config
import os
import subprocess
import shlex
import time
import signal
from os import listdir
from os.path import isfile, join
from fnmatch import fnmatch
import servo

PIDFILE = os.path.join(config.DEFAULT_PID_ROOT, "worker.pid")
DIR_LIBRARIES = "/usr/share/eucalyptus"
CLIENT_CLASS = "com.eucalyptus.simpleworkflow.common.client.WorkflowClientStandalone"
LOG_DIR = "/var/log/load-balancer-servo"
LOG_LEVEL = "DEBUG"
SWF_DOMAIN = "LoadbalancingDomain"
WORKER_JAR_REGEX="eucalyptus-loadbalancing-[0-9]*.jar"
WORKER_CLASSES = "LoadBalancingVmActivitiesImpl"
CWD = config.RUN_ROOT

singleton_worker = None
def get_worker():
    global singleton_worker
    if singleton_worker is None:
         singleton_worker = SwfWorker()
    return singleton_worker

class SwfWorker(threading.Thread):
    def __init__(self):
        self.running = False
        self.should_terminate = False
        threading.Thread.__init__(self)

    def lookup_worker_jar(self):
        result = [f for f in listdir(DIR_LIBRARIES) if isfile(join(DIR_LIBRARIES, f)) and fnmatch(f, WORKER_JAR_REGEX)]
        if len(result) == 1:
            return join(DIR_LIBRARIES, result[0])
        return None 

    def get_pid(self):
        if os.path.exists(PIDFILE):
            try:
                f=open(PIDFILE, "r")
                contents = f.readlines()
                f.close()
                return int(contents[0])
            except Exception, err:
                servo.log.error('Failed to open file %s: %s' % (PIDFILE, err))
        return None

    def process_exist(self, proc_num):
        return servo.run('ps %d' % proc_num) == 0

    def execute_with_popen(self, cmdline):
        p = subprocess.Popen(shlex.split(cmdline), stderr=subprocess.PIPE, cwd=CWD)
        return p

    def kill_pid(self, pid, blocking=True):
        os.kill(pid, signal.SIGTERM)
        while blocking:
            if not self.process_exist(pid):
                break
            servo.log.debug('Waiting for the old worker process (%d) to terminate' % pid)
            time.sleep(3) 

    def write_pid(self, pid):
        f = open(PIDFILE, "w")
        strpid = str(pid)
        f.write(strpid)
        f.close()

    def stop(self, terminate=True):
        self.running = False
        self.should_terminate = terminate

    def run(self):
        self.running = True
        pid = self.get_pid()
        proc = None
        # check pid file and lookup process
        if pid and self.process_exist(pid):
            servo.log.debug('Existing SWF worker process is found (%d)' % pid)
            self.kill_pid(pid)
        try:
            # if no process, start a new Java process
            # prepare arguments to the process
            swf_url = config.get_swf_service_url()
            if not swf_url:
                raise Exception('Simple workflow service url is not found')
            swf_url = 'http://%s:%d/' % (swf_url, config.get_webservice_port())
            instance_id = config.get_servo_id()
            if not instance_id:
                raise Exception('Instance ID is not found')
            worker_jar = self.lookup_worker_jar()
            if not worker_jar:
                raise Exception('No worker jar is found')

            cmdline = 'java -cp .:%s/* %s --logdir %s --logappender cloud-debug-file --loglevel %s -d %s -e %s --jar %s --classes %s -l %s' % (DIR_LIBRARIES, CLIENT_CLASS, LOG_DIR, LOG_LEVEL, SWF_DOMAIN, swf_url, worker_jar, WORKER_CLASSES, instance_id)
            servo.log.debug('Running SWF worker: %s' % cmdline)
            proc = self.execute_with_popen(cmdline)
            pid = proc.pid
            self.write_pid(pid)
        except Exception, err:
            servo.log.error('Failed to run SWF worker: %s' % err)

        if not proc or proc.poll() is not None:
            if proc.returncode is None:
                servo.log.error('Shutting down thread because no process is running')
            else:
                servo.log.error('Shutting down thread because process terminated with return code = %d' % proc.returncode)
            return

        # keep checking the status of process 
        DEBUG_LOG_PERIOD_SEC = 300
        count = 0
        while self.running and proc.poll() is None:
            time.sleep(1) 
            count += 1
            if count % DEBUG_LOG_PERIOD_SEC == 0:
                count = 0
                servo.log.info("Swf worker process is running (%d)" % pid)
     
        # if instructed, kill the java process
        if self.should_terminate and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait()
                servo.log.info('Swf worker process has terminated successfully')
            except Exception, err:
                servo.log.error('Failed to terminate process during shutdown: %s', err)
        elif proc.poll() is not None:
            servo.log.error('Swf worker process unexpectedly terminated with return code=%d' % proc.returncode)
        else:
            servo.log.info('Shutting down thread without terminating worker process (%d)' % pid)
     
        self.running = False
        self.should_terminate = False
