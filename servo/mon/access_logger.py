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
import urllib2
import os
import subprocess
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
        servo.log.debug('access log enabled?: %s' % self.enabled)
        if not self.enabled:
            return

        if self.bucket_name:
            servo.log.debug('access log bucket name: %s' % urllib2.quote(self.bucket_name))
        if self.bucket_prefix:
            servo.log.debug('access log bucket prefix: %s' % urllib2.quote(self.bucket_prefix))
        servo.log.debug('access log emit interval: %d' % self.emit_interval)

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
        fd = None
        if not file_path:
            tmpfile = tempfile.mkstemp()
            fd = tmpfile[0]
            file_path = tmpfile[1] 
        try:
            if not fd:
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
        conn = boto.connect_s3(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, security_token=security_token, is_secure=False, port=config.get_webservice_port(), path='/services/objectstorage', host= config.get_objectstorage_service_host(), calling_format='boto.s3.connection.OrdinaryCallingFormat')
        if not conn:
            raise Exception('Could not connect to object storage (S3) service') 

        key_name = self.generate_log_file_name()
        bucket = conn.get_bucket(self.bucket_name, validate=False)
        k = Key(bucket)
        k.key = key_name
        k.set_contents_from_filename(tmpfile_path, policy='bucket-owner-full-control')
        servo.log.debug('Access logs were emitted successfully: s3://%s/%s'  % (urllib2.quote(self.bucket_name),urllib2.quote(key_name)))

    def get_accesslog_ip(self):
        try:
            default_ip = "0.0.0.0"
            ip = config.get_public_ip()
            if ip is None or ip == default_ip:
                ip = self.extract_from_secondary_nic()
            if ip is None:
                ip = config.get_private_ip()
            if ip is None:
                ip = default_ip
            return ip
        except Exception, err:
            servo.log.debug("Failed to get IP: %s" % err)

    def extract_from_secondary_nic(self):
        secondary_ip = None
        try:
            SECONDARY_DEVICE = 'eth1'
            proc = subprocess.Popen(['/usr/sbin/ip', 'addr', 'show', 'dev', SECONDARY_DEVICE], stdout=subprocess.PIPE)
            if proc and proc.stdout:
                while True:
                    line = proc.stdout.readline()
                    if not line or len(line) <= 0:
                        break
                    else:
                        if line.find('inet') >= 0 and line.find('inet6') < 0:
                            tokens = line.split()
                            tokens = tokens[1].split('/')
                            secondary_ip = tokens[0]
                            break
            return secondary_ip
        except Exception, err:
            return secondary_ip

    def generate_log_file_name(self):
        name = ''
        if self.bucket_prefix:
            name = self.bucket_prefix+'/'
        #{Bucket}/{Prefix}/AWSLogs/{AWS AccountID}/elasticloadbalancing/{Region}/{Year}/{Month}/{Day}/{AWS Account ID}_elasticloadbalancing_{Region}_{Load Balancer Name}_{End Time}_{Load Balancer IP}_{Random String}.log
        #S3://mylogsbucket/myapp/prod/AWSLogs/123456789012/elasticloadbalancing/us-east-1/2014/02/15/123456789012_elasticloadbalancing_us-east-1_my-test-loadbalancer_20140215T2340Z_172.160.001.192_20sg8hgm.log
        now = dt.utcnow()
        ip_addr = self.get_accesslog_ip()
        if not ip_addr:
            ip_addr = '127.0.0.1'
        name = name + 'AWSLogs/' + config.get_owner_account_id() + '/elasticloadbalancing/eucalyptus/'+str(now.year)+'/'+str(now.month)+'/'+str(now.day)+'/'+config.get_owner_account_id()+'_elasticloadbalancing_eucalyptus_'+self.loadbalancer+'_'+now.strftime('%Y%m%dT%H%MZ')+'_'+ip_addr+'_'+''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)) +'.log'
        return name

    def add_log(self, log):
        if self.enabled and self.bucket_name:
            self._logs.append(log)
     
    def stop(self):
        self.running = False
