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
import httplib2
import config
import servo
import servo.ws
from servo.haproxy import ProxyManager
from servo.haproxy.listener import Listener
import servo.hostname_cache
from collections import Iterable

class ServoLoop(object):
    STOPPED = "stopped"
    STOPPING = "stopping"
    RUNNING = "running"

    def __init__(self):
        # get the instance id from metadata service
        self.__instance_id = 'i-5CAC4274'
        self.__elb_host = config.get_clc_host() # TODO: should query user-data 
        if self.__instance_id is None:
            resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/instance-id")
            if resp['status'] != '200' or len(content) <= 0:
                raise Exception('could not query the metadata for instance id (%s,%s)' % (resp, content))
            self.__instance_id = content
        self.__status = ServoLoop.STOPPED
        servo.log.debug('main loop running with elb_host=%s, instance_id=%s' % (self.__elb_host, self.__instance_id))

    def start(self):
        # (future) retrieve IAM role credentials
        access_key_id = config.get_access_key_id()
        secret_access_key = config.get_secret_access_key()
        # (future) setup haproxy template  (retrieved from metadata service)
        # periodically
        self.__status = ServoLoop.RUNNING 
        proxy_mgr = ProxyManager()
        while self.__status == ServoLoop.RUNNING:
            # call elb-describe-services
            lbs = None
            try:
                con = servo.ws.connect_elb(host_name=self.__elb_host, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
                lbs = con.get_servo_load_balancers(self.__instance_id)
            except Exception, err:
                servo.log.error('failed to query the elb service: %s' % err)
            if lbs is None:
                servo.log.warning('failed to find the loadbalancers')
            else:
                # prepare Listener lists
                # call updateListeners
                received=[] 
                try:
                    for lb in lbs:
                        instances = []
                        if lb.instances is not None and isinstance(lb.instances, Iterable):
                            for inst in lb.instances:
                                instances.append(str(inst.id))
                        if lb.listeners is not None and isinstance(lb.listeners, Iterable) :
                            for listener in lb.listeners:
                                protocol=listener.protocol
                                port=listener.load_balancer_port
                                instance_port=listener.instance_port
                                instance_protocol=None # TODO: boto doesn't have the field
                                ssl_cert=None # TODO: not supported
                                l = Listener(protocol=protocol, port=port, instance_port=instance_port, instance_protocol=instance_protocol, ssl_cert=ssl_cert, loadbalancer=lb.name)
                                for inst_id in instances:
                                    hostname = servo.hostname_cache.get_hostname(inst_id)
                                    if hostname is not None: l.addInstance(hostname) 
                                received.append(l)

                except Exception, err:
                    servo.log.error('failed to receive listeners: %s' % err) 
                try:
                    if len(received) > 0:
                        proxy_mgr.updateListeners(received)
                        servo.log.debug('listener updated')
                except Exception, err:
                    servo.log.error('failed to update proxy listeners: %s' % err) 
        
          # (future) put health check results to the elb service
          # (future) put cloudwatch metrics to the elb service
            start_time = time.time()
            while time.time() - start_time < config.QUERY_PERIOD_SEC and self.__status == ServoLoop.RUNNING:
                time.sleep(1)

        self.__status = ServoLoop.STOPPED

    def stop(self):
        self.__status = ServoLoop.STOPPING

    def getStatus(self):
        return self.__status
