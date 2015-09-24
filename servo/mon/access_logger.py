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
from datetime import datetime as dt
import servo
import servo.config as config
import threading
import boto
import socket
import random
import string
import tempfile
import os
from boto.s3.connection import S3Connection
from boto.s3.key import Key

class AccessLogger(threading.Thread):
    def __init__(self):
        self.running = True
        threading.Thread.__init__(self)
        self.emit_interval = 60 # in minute
        self.bucket_name = None
        self.bucket_prefix = None
        self.enabled = False
        self.loadbalancer = None
        self._last_emit_minute = -1
        self._logs = []
        self._emitted = False
        self._tmp_log_file = None

    def run(self):
        servo.log.info('Starting access logger thread')
        while self.running:
            time.sleep(10)
            self.try_emit()

    def try_emit(self):
        if not self.enabled:
            return
        if not self.bucket_name:
            servo.log.error('Access logging is enabled without bucket name')
            return
        try:
            if len(self._logs) > 0:
                self._tmp_log_file = self.write_log(self._tmp_log_file)
        except Exception, err:
            servo.log.error('Failed to write logs to temp file: %s' % err)
            self._tmp_log_file = None
        finally:
            del self._logs[:]
        now = dt.now()
        cur_min = now.minute
        if cur_min % self.emit_interval == 0:
            if not self._emitted:
                try:
                    self.do_emit(self._tmp_log_file)
                except Exception, err:
                    servo.log.error('Failed to emit access logs: %s' % err)
                finally:
                    if self._tmp_log_file:
                        os.unlink(self._tmp_log_file)
                    self._tmp_log_file = None
                    self._emitted = True
        else:
            self._emitted = False

    def write_log(self, file_path=None):
        if not file_path:
            tmpfile = tempfile.mkstemp()
            file_path = tmpfile[1] 
        fd = None
        try:
            fd = os.open(file_path, os.O_APPEND | os.O_WRONLY | os.O_CREAT)
	    for line in self._logs:
                os.write(fd, line+'\n')
            os.close(fd)
            fd = None
        finally:
            if fd:
                os.close(fd)

        return file_path
     
    def do_emit(self, tmpfile_path=None):
        if not tmpfile_path:
            return
        aws_access_key_id = config.get_access_key_id()
        aws_secret_access_key = config.get_secret_access_key()
        security_token = config.get_security_token()
        conn = boto.connect_s3(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, security_token=security_token, is_secure=False, port=8773, path='/services/objectstorage', host= config.get_objectstorage_service_host(), calling_format='boto.s3.connection.OrdinaryCallingFormat')
        if not conn:
            raise Exception('Could not connect to object storage (S3) service') 

        key_name = self.generate_log_file_name()
        bucket = conn.get_bucket(self.bucket_name, validate=False)
        k = Key(bucket)
        k.key = key_name
        k.set_contents_from_filename(tmpfile_path, policy='bucket-owner-full-control')
        servo.log.debug('Access logs were emitted successfully: s3://%s/%s'  % (self.bucket_name,key_name))

    def generate_log_file_name(self):
        name = ''
        if self.bucket_prefix:
            name = self.bucket_prefix+'/'
        #{Bucket}/{Prefix}/AWSLogs/{AWS AccountID}/elasticloadbalancing/{Region}/{Year}/{Month}/{Day}/{AWS Account ID}_elasticloadbalancing_{Region}_{Load Balancer Name}_{End Time}_{Load Balancer IP}_{Random String}.log
        #S3://mylogsbucket/myapp/prod/AWSLogs/123456789012/elasticloadbalancing/us-east-1/2014/02/15/123456789012_elasticloadbalancing_us-east-1_my-test-loadbalancer_20140215T2340Z_172.160.001.192_20sg8hgm.log
        now = dt.utcnow()
        name = name + 'AWSLogs/' + config.get_owner_account_id() + '/elasticloadbalancing/eucalyptus/'+str(now.year)+'/'+str(now.month)+'/'+str(now.day)+'/'+config.get_owner_account_id()+'_elasticloadbalancing_eucalyptus_'+self.loadbalancer+'_'+now.strftime('%Y%m%dT%H%MZ')+'_'+socket.gethostbyname(socket.gethostname())+'_'+''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)) +'.log'
        return name

    def add_log(self, log):
        if self.enabled and self.bucket_name:
            self._logs.append(log)
     
    def stop(self):
        self.running = False
