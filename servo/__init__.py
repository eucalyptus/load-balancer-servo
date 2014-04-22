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
from servo.logutil import log, set_loglevel
from servo.config import set_pidfile, set_boto_config
from servo.main_loop import ServoLoop
from servo.cw_loop import CWLoop
import subprocess
import os
import time

__version__ = '1.0.0-dev'
Version = __version__

def spin_locks():
    try:
        while not (os.path.exists("/var/lib/load-balancer-servo/dns.lock") and os.path.exists("/var/lib/load-balancer-servo/ntp.lock")):
            time.sleep(2)
            log.debug('waiting on dns and ntp setup (reboot if continued)')
        os.remove("/var/lib/load-balancer-servo/dns.lock")
        os.remove("/var/lib/load-balancer-servo/ntp.lock")
    except Exception, err:
        log.error('failed to spin on locks: %s' % err)

def start_servo():
    spin_locks()
    cmd_line = 'sudo modprobe floppy > /dev/null'
    if subprocess.call(cmd_line, shell=True) != 0:
        log.error('failed to load floppy driver')
    CWLoop().start()
    ServoLoop().start()
