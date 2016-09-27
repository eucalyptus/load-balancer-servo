# Copyright 2009-2013 Eucalyptus Systems, Inc.
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
#
# Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
# CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
# additional information or have any questions.

#
# Order matters here. We want to make sure we initialize logging before anything
# else happens. We need to initialize the logger that boto will be using.
#
from servo.logutil import log, set_loglevel, set_boto_loglevel
from servo.config import set_pidfile, set_boto_config
from servo.main_loop import ServoLoop
import servo.swf_worker as swf_worker
import subprocess
import os
import time
import shlex

__version__ = '1.0.0-dev'
Version = __version__

def spin_locks():
    try:
        while not (os.path.exists("/var/lib/load-balancer-servo/ntp.lock")):
            time.sleep(2)
            log.debug('waiting on ntp setup (reboot if continued)')
        os.remove("/var/lib/load-balancer-servo/ntp.lock")
    except Exception, err:
        log.error('failed to spin on locks: %s' % err)


def run_as_sudo(cmd):
    return run('sudo %s' % cmd)


def run_as_sudo_with_grep(cmd, grep):
    return run_with_grep('sudo %s' % cmd, grep)


def run(cmd):
    p = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        log.debug(output)
    return p.returncode


def run_with_grep(cmd, grep):
    proc1 = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split('grep %s' % grep), stdin=proc1.stdout, stderr=subprocess.PIPE)
    proc1.stdout.close()
    output = proc2.communicate()
    if proc2.returncode != 0:
        log.debug(output)
    return proc2.returncode

def start_all():
    spin_locks()
    start_swf_worker()
    start_servo()

def start_swf_worker():
    worker = swf_worker.get_worker()
    worker.start()

def stop_swf_worker():
    worker = swf_worker.get_worker()
    worker.stop()
    
def start_servo():
    if run_as_sudo('modprobe floppy') != 0:
        log.error('failed to load floppy driver')
    ServoLoop().run()
