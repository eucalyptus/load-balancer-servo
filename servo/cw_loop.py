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

import time
import config
import threading
import servo
import servo.ws
from servo.mon.stat import stat_instance

class CWLoop(threading.Thread):
    def __init__(self):
        self.running = True
        threading.Thread.__init__(self)

    def run(self):
        servo.log.info('starting cloudwatch metrics reporter')
        elb_host = config.get_clc_host()
        aws_access_key_id = config.get_access_key_id()
        aws_secret_access_key = config.get_secret_access_key()
        security_token = config.get_security_token()
        servo_instance_id = config.get_servo_id()
        if elb_host is None or servo_instance_id is None:
            servo.log.error('some required parameters are missing; failed to start cloudwatch report loop')
            return

        start_time = time.time()
        while time.time() - start_time < config.CWATCH_REPORT_PERIOD_SEC and self.running:
            time.sleep(1)

        con = servo.ws.connect_elb(host_name=elb_host, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, security_token=security_token)
        while self.running:
            try:
                metric = stat_instance.get_and_clear_stat()
                con.put_cw_metric(servo_instance_id, metric)
                servo.log.debug('reported the metrics: %s' % metric)
            except Exception, err:
                servo.log.error('failed to report the cloudwatch metrics: %s', err)
 
            start_time = time.time()
            while time.time() - start_time < config.CWATCH_REPORT_PERIOD_SEC and self.running:
                time.sleep(1)

    def stop(self):
        self.running = False
