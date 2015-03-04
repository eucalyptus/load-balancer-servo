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
import os
import servo
import servo.ws
from servo.haproxy import ProxyManager
from servo.haproxy.listener import Listener
import servo.hostname_cache
import servo.health_check as health_check
from servo.health_check import HealthCheckConfig, HealthCheckManager
import servo.mon.listener as mon
from servo.mon.stat import stat_instance
from servo.lb_policy import LoadbalancerPolicy
from collections import Iterable

class ServoLoop(object):
    STOPPED = "stopped"
    STOPPING = "stopping"
    RUNNING = "running"

    def __init__(self):
        # get the instance id from metadata service
        self.__instance_id = None
        self.__elb_host = config.get_clc_host() # TODO: should query user-data 
        if self.__instance_id is None:
            self.__instance_id = config.get_servo_id()

        self.__status = ServoLoop.STOPPED
        servo.log.debug('main loop running with elb_host=%s, instance_id=%s' % (self.__elb_host, self.__instance_id))

    def start(self):
        if config.ENABLE_CLOUD_WATCH:
            hl = mon.LogListener(stat_instance)
            hl.start()
        self.__status = ServoLoop.RUNNING 
        proxy_mgr = ProxyManager()
        hc_mgr = HealthCheckManager()
        while self.__status == ServoLoop.RUNNING:
            # call elb-describe-services
            lbs = None
            try:
                access_key_id = config.get_access_key_id()
                secret_access_key = config.get_secret_access_key()
                security_token = config.get_security_token()
                con = servo.ws.connect_elb(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, security_token=security_token)
                lbs = con.get_servo_load_balancers(self.__instance_id)
            except Exception, err:
                servo.log.error('failed to query the elb service: %s' % err)
            if lbs is None:
                servo.log.warning('failed to find the loadbalancers')
            else:
                # prepare Listener lists
                # call update_listeners
                received=[] 
                try:
                    conn_idle_timeout = config.CONNECTION_IDLE_TIMEOUT
                    for lb in lbs:
                        try:
                            attr = lb.attributes
                            conn_idle_timeout = attr.connecting_settings.idle_timeout
                            if int(conn_idle_timeout) < 1:
                                conn_idle_timeout = 1
                            elif int(conn_idle_timeout) > 3600:
                                conn_idle_timeout = 3600
                        except Exception, err:
                            servo.log.warning('failed to get connection idle timeout: %s' % str(err))
                        if lb.health_check is not None:
                            interval = lb.health_check.interval
                            healthy_threshold = lb.health_check.healthy_threshold
                            unhealthy_threshold = lb.health_check.unhealthy_threshold
                            timeout = lb.health_check.timeout
                            target = lb.health_check.target
                            if interval is None or healthy_threshold is None or unhealthy_threshold is None or timeout is None or  target is None: 
                                pass
                            else:
                                hc = HealthCheckConfig(interval, healthy_threshold, unhealthy_threshold, timeout, target)
                                if health_check.health_check_config is None or health_check.health_check_config != hc:
                                    health_check.health_check_config = hc
                                    servo.log.info('new health check config: %s' % hc)
                                    hc_mgr.reset()
                        instances = []
                        if lb.instances is not None and isinstance(lb.instances, Iterable):
                            for inst in lb.instances:
                                instances.append(str(inst.id))
                        
                        hc_mgr.set_instances(instances)
                        in_service_instances = []
                        for inst_id in instances:                  
                            if hc_mgr.health_status(inst_id) is 'InService':
                                in_service_instances.append(inst_id)

                        if lb.listeners is not None and isinstance(lb.listeners, Iterable) :
                            for listener in lb.listeners:
                                protocol=listener.protocol
                                port=listener.load_balancer_port
                                instance_port=listener.instance_port
                                instance_protocol=None # TODO: boto doesn't have the field
                                ssl_cert=str(listener.ssl_certificate_id)
                                policies = ServoLoop.get_policies(lb, listener.policy_names)
                                l = Listener(protocol=protocol, port=port, instance_port=instance_port, instance_protocol=instance_protocol, ssl_cert=ssl_cert, loadbalancer=lb.name, policies=policies, connection_idle_timeout=conn_idle_timeout)
                                for inst_id in in_service_instances:
                                    hostname = servo.hostname_cache.get_hostname(inst_id)
                                    if hostname is not None: l.add_instance(hostname) 
                                received.append(l)
                except Exception, err:
                    servo.log.error('failed to receive listeners: %s' % err) 
                try:
                    proxy_mgr.update_listeners(received)
                    servo.log.debug('listener updated')
                except Exception, err:
                    servo.log.error('failed to update proxy listeners: %s' % err) 
        
          # (future) put health check results to the elb service
          # (future) put cloudwatch metrics to the elb service
            query_period_delay = config.QUERY_PERIOD_SEC
            while query_period_delay > 0 and self.__status == ServoLoop.RUNNING:
                time.sleep(1)
                query_period_delay -= 1

        self.__status = ServoLoop.STOPPED

    def stop(self):
        self.__status = ServoLoop.STOPPING

    def status(self):
        return self.__status

    @staticmethod
    def get_policies(loadbalancer, policy_names):
        if not loadbalancer or not policy_names:
            return []
        policies = [] 
        try:
            for policy_desc in loadbalancer.policy_descriptions: 
                if policy_desc.policy_name in policy_names:
                    policy = LoadbalancerPolicy.from_policy_description(policy_desc)
                    if policy:
                        servo.log.debug('import policy: %s' % policy)
                        policies.append(policy)
        except Exception, err:
            servo.log.error('failed to create policy objects: %s' % err)
            servo.log.debug(traceback.format_exc())
        return policies

