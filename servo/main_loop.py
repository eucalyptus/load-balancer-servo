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
import traceback
import urllib2
import servo
import servo.ws
import redis
import boto
import xml.sax
import json

from boto.resultset import ResultSet
from boto.compat import six
from servo.ws.loadbalancer import LoadBalancer
from servo.ws.policies import PolicyDescription
from servo.haproxy import ProxyManager
from servo.haproxy.listener import Listener
import servo.hostname_cache
import servo.health_check as health_check
from servo.health_check import HealthCheckConfig, HealthCheckManager
import servo.mon.listener as mon
from servo.mon.stat import stat_instance
from servo.mon.access_logger import AccessLogger
from servo.lb_policy import LoadbalancerPolicy
from collections import Iterable

class ServoLoop(object):
    proxy_mgr = ProxyManager()
    hc_mgr = HealthCheckManager()
    log_listener = mon.LogListener(stat_instance)
    access_logger = AccessLogger()

    def __init__(self):
        # get the instance id from metadata service
        self.__instance_id = None
        self.__elb_host = config.get_clc_host() # TODO: should query user-data 
        if self.__instance_id is None:
            self.__instance_id = config.get_servo_id()

        self.__redis = None
        self.__pubsub = None
        servo.log.debug('main loop running with elb_host=%s, instance_id=%s' % (self.__elb_host, self.__instance_id))

    @staticmethod
    def get_redis():
        return redis.StrictRedis(host='localhost', port=6379)

    @staticmethod
    def report_cloudwatch_metrics(msg):
        try:
            if not 'data' in msg or not msg['data']:
                raise Exception('No data field in the received redis message')
            msg = msg['data']
        except Exception, err:
            servo.log.error('failed to parse get-cloudwatch-metrics message')

        metric_json = '{}'      
        try:
            metric_json = stat_instance.get_json_and_clear_stat()
        except Exception, err:
            servo.log.error('failed to retrieve cw metrics in json format: %s' % str(err))               
        try:
            r = ServoLoop.get_redis()
            r.lpush('get-cloudwatch-metrics-reply', metric_json)
        except Exception, err:
            servo.log.error('failed to publish cw metrics data: %s' % str(err))

    @staticmethod
    def report_instance_status(msg):
        hc_mgr = ServoLoop.hc_mgr
        try:
            if not 'data' in msg or not msg['data']:
                raise Exception('No data field in the received redis message')
            msg = msg['data']
        except Exception, err:
            servo.log.error('failed to parse get-instance-status message')

        instances = {}
        for instance_id in hc_mgr.list_instances():
            status = hc_mgr.health_status(instance_id)
            if status is None:
                continue
            instances[instance_id] = status
        json_format = json.dumps(instances)
        try:
            r = ServoLoop.get_redis()
            r.lpush('get-instance-status-reply', json_format)
        except Exception, err:
            servo.log.error('failed to publish instance status data: %s' % str(err))

    @staticmethod
    def unmarshall_policy(msg):
        markers = [('member', LoadBalancer)]
        rs = ResultSet(markers)
        h = boto.handler.XmlHandler(rs, None)
        if isinstance(msg, six.text_type):
            msg = msg.encode('utf-8')
        xml.sax.parseString(msg, h)
        lbs = rs
        if lbs and len(lbs) > 0:
            lb = lbs[0]  
            if lb.policy_descriptions and len(lb.policy_descriptions) > 0:
                return lb.policy_descriptions[0]
        return None
 
    @staticmethod
    def set_policy(msg):
        try:
            if not 'data' in msg or not msg['data']:
                raise Exception('No data field in the received redis message')
            msg = msg['data']
            policy = ServoLoop.unmarshall_policy(msg)
            ServoLoop.loadbalancer_policies[policy.policy_name] = policy 
        except Exception, err:
            servo.log.error('failed to unmarshall policy description: %s' % str(err))
 
    @staticmethod
    def unmarshall_loadbalancer(msg):
        markers = [('member', LoadBalancer)]
        rs = ResultSet(markers)
        h = boto.handler.XmlHandler(rs, None)
        if isinstance(msg, six.text_type):
            msg = msg.encode('utf-8')
        xml.sax.parseString(msg, h)
        return rs

    @staticmethod
    def set_loadbalancer(msg):
        proxy_mgr = ServoLoop.proxy_mgr
        hc_mgr = ServoLoop.hc_mgr
        log_listener = ServoLoop.log_listener
        access_logger = ServoLoop.access_logger

        lbs = None
        try:
            if not 'data' in msg or not msg['data']:
                raise Exception('No data field in the received redis message')
            msg = msg['data']
            lbs = ServoLoop.unmarshall_loadbalancer(msg)
        except Exception, err:
            servo.log.error('failed to parse loadbalancer message: %s' % str(err))

        if lbs is None:
            servo.log.warning('Received message contains no loadbalancers')
        else:
            # prepare Listener lists
            # call update_listeners
            received=[] 
            try:
                conn_idle_timeout = config.CONNECTION_IDLE_TIMEOUT
                for lb in lbs:
                    try:
                        if log_listener: # assume there is only one loadbalancer per servo
                            log_listener.set_loadbalancer(lb.name)
                        attr = lb.attributes
                        conn_idle_timeout = attr.connecting_settings.idle_timeout
                        if int(conn_idle_timeout) < 1:
                            conn_idle_timeout = 1
                        elif int(conn_idle_timeout) > 3600:
                            conn_idle_timeout = 3600
                        access_log_setting = attr.access_log
                        access_logger.loadbalancer = lb.name
                        if access_log_setting.s3_bucket_name != None:
                            access_logger.bucket_name = access_log_setting.s3_bucket_name
                            servo.log.debug('access log bucket name: %s' % urllib2.quote(access_logger.bucket_name))
                        if access_log_setting.s3_bucket_prefix != None:
                            access_logger.bucket_prefix = access_log_setting.s3_bucket_prefix
                            servo.log.debug('access log bucket prefix: %s' % urllib2.quote(access_logger.bucket_prefix))
                        if access_log_setting.emit_interval != None:
                            access_logger.emit_interval = int(access_log_setting.emit_interval)
                            servo.log.debug('access log emit interval: %d' % access_logger.emit_interval)
                        if access_log_setting.enabled != None:
                            access_logger.enabled = access_log_setting.enabled
                            servo.log.debug('access log enabled?: %s' % access_logger.enabled)
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
                    # record instance ip address
                    if lb.instances is not None and isinstance(lb.instances, Iterable):
                        instances.extend(lb.instances)
                        for inst in lb.instances:
                            inst_id=inst.instance_id
                            ipaddr=inst.instance_ip_address
                            servo.hostname_cache.register(inst_id, ipaddr)
                        
                    instance_ids = [inst.instance_id for inst in instances]
                    hc_mgr.set_instances(instances)
                    in_service_instances = []
                    for inst_id in instance_ids:                  
                        if hc_mgr.health_status(inst_id) is 'InService':
                            in_service_instances.append(inst_id)

                    if lb.listeners is not None and isinstance(lb.listeners, Iterable) :
                        for listener in lb.listeners:
                            protocol=listener.protocol
                            port=listener.load_balancer_port
                            instance_port=listener.instance_port
                            instance_protocol=listener.instance_protocol 
                            ssl_cert=str(listener.ssl_certificate_id)
                            policies = ServoLoop.get_listener_policies(lb, listener.policy_names)
                            policies.extend(ServoLoop.get_backend_policies(lb, instance_port))
                            l = Listener(protocol=protocol, port=port, instance_port=instance_port, instance_protocol=instance_protocol, ssl_cert=ssl_cert, loadbalancer=lb.name, policies=policies, connection_idle_timeout=conn_idle_timeout)
                            for inst_id in in_service_instances:
                                hostname = servo.hostname_cache.get_hostname(inst_id)
                                if hostname is not None: l.add_instance(hostname) 
                            received.append(l)
            except Exception, err:
                servo.log.error('failed to receive listeners: %s' % err) 
            try:
                proxy_mgr.update_listeners(received)
                servo.log.debug('Listener updated')
            except Exception, err:
                servo.log.error('failed to update proxy listeners: %s' % err) 
    
    def run(self):
        access_logger = ServoLoop.access_logger
        access_logger.start()

        log_listener = ServoLoop.log_listener
        log_listener.access_logger = access_logger
        log_listener.start()

        while True: 
            try:
                self.__redis = ServoLoop.get_redis()
                self.__pubsub = self.__redis.pubsub()
                self.__pubsub.subscribe(**{'set-policy': ServoLoop.set_policy})
                self.__pubsub.subscribe(**{'set-loadbalancer': ServoLoop.set_loadbalancer})
                self.__pubsub.subscribe(**{'get-instance-status': ServoLoop.report_instance_status})
                self.__pubsub.subscribe(**{'get-cloudwatch-metrics': ServoLoop.report_cloudwatch_metrics})

                for msg in self.__pubsub.listen():
                    pass
            except Exception, err:
                servo.log.error('Failed to subscribe redis channels. Is redis running?')
                time.sleep(10)
                continue

    loadbalancer_policies={}

    @staticmethod
    def get_backend_policies(loadbalancer, instance_port):
        if not loadbalancer or not loadbalancer.backends:
            return []
        policy_names = []
        policies = []
        try:
            for backend in loadbalancer.backends:
                if backend.instance_port == instance_port:
                    for p in backend.policies:
                        policy_names.append(p.policy_name)
            for policy_name, policy_desc in ServoLoop.loadbalancer_policies.items():
                if policy_name in policy_names or policy_desc.policy_type_name == 'PublicKeyPolicyType':
                    policy = LoadbalancerPolicy.from_policy_description(policy_desc)
                    if policy:
                        policies.append(policy)
        except Exception, err:
            servo.log.error('failed to create backend policy objects: %s' % err)
            servo.log.debug(traceback.format_exc())

        return policies       

    @staticmethod
    def get_listener_policies(loadbalancer, listener_policy_names):
        if not loadbalancer or not listener_policy_names:
            return []
        policies = [] 
        try:
            for policy_name in listener_policy_names:
                if policy_name in ServoLoop.loadbalancer_policies:
                    policy_desc = ServoLoop.loadbalancer_policies[policy_name]
                    policy = LoadbalancerPolicy.from_policy_description(policy_desc)
                    if policy:
                        policies.append(policy)
                    else:
                        servo.log.error('failed to create policy object from policy %s' % policy_name)
                else:
                    servo.log.error('unable to find policy description: %s' % policy_name)
        except Exception, err:
            servo.log.error('failed to create policy objects: %s' % err)
            servo.log.debug(traceback.format_exc())
        return policies

