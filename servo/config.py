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
import os
import httplib2
import servo
import boto
import boto.provider

DEFAULT_PID_ROOT = "/var/run/load-balancer-servo"
DEFAULT_PIDFILE = os.path.join(DEFAULT_PID_ROOT, "servo.pid")
CONF_ROOT = "/etc/load-balancer-servo"
RUN_ROOT = "/var/lib/load-balancer-servo"
HAPROXY_BIN = "/usr/sbin/haproxy"
SUDO_BIN = "/usr/bin/sudo"
CW_LISTENER_DOM_SOCKET ='/var/lib/load-balancer-servo/haproxy.sock'
FLOPPY_MOUNT_DIR = RUN_ROOT+"/floppy"
CONNECTION_IDLE_TIMEOUT = 60
CONFIG_FILE = CONF_ROOT + "/servo.conf"

# Apply default values in case user does not specify
pidfile = DEFAULT_PIDFILE
pidroot = DEFAULT_PID_ROOT
boto_config = None
cred_provider = None

def get_provider():
    global boto_config
    global cred_provider
    if not cred_provider:
        if boto_config:
            boto.provider.config = boto.Config(boto_config)
        cred_provider = boto.provider.get_default()
    return cred_provider

def set_boto_config(filename):
    if not os.path.isfile(filename):
        raise Exception('could not find boto config {0}'.format(filename))
    global boto_config
    boto_config = filename

# Update pidfile and pidroot variables in global scope.
# This is called if the user has chosen to use a custom
# pidfile location from the command line.
def set_pidfile(filename):
    global pidfile
    global pidroot
    pidfile = filename
    pidroot = os.path.dirname(pidfile)

user_data_store={}  


def read_config_file():
    try:
        f = open(CONFIG_FILE)
        content = f.read()
        lines = content.split('\n')
        for l in lines:
            if len(l.strip()):
                kv = l.split('=')
                if len(kv) == 2:
                    user_data_store[kv[0]] = kv[1]
    except Exception, err:
        raise Exception('Could not read configuration file due to %s' % err)


def get_value(key):
    if key in user_data_store:
       return user_data_store[key]
    else:
        read_config_file()
        if key not in user_data_store:
            raise Exception('could not find %s' % key) 
        return user_data_store[key]

def get_access_key_id(): 
    akey = get_provider().get_access_key()
    return akey

def get_secret_access_key():
    skey = get_provider().get_secret_key()
    return skey

def get_security_token():
    token = get_provider().get_security_token()
    return token

###### DEPRECATED ########
def get_clc_host():
    return '169.254.169.254'

def get_clc_port():
    val=get_value('eucalyptus_port')
    if val is not None:
        return int(val)
    else:
        return val

def get_ec2_path():
    return get_value('eucalyptus_path')
###### END DEPRECATED #######

def get_elb_service_url():
    return get_value('elb_service_url')

def get_euare_service_url():
    return get_value('euare_service_url')

def get_objectstorage_service_host():
    return get_value('objectstorage_service_url')

def get_swf_service_url():
    return get_value('simpleworkflow_service_url')

def get_owner_account_id():
    return get_value('loadbalancer_owner_account')

def get_ntp_server_url():
    return get_value('ntp_server')

def get_webservice_port():
    try:
        return int(get_value('webservice_port'))
    except Exception, err:
        return 8773

__availability_zone = None
def get_availability_zone():
    global __availability_zone
    if __availability_zone is None:
        resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/placement/availability-zone")
        if resp['status'] != '200' or len(content) <= 0:
            raise Exception('could not query the metadata for availability zone (%s,%s)' % (resp, content))
        __availability_zone = content
    return __availability_zone

__servo_id = None
def get_servo_id():
    global __servo_id 
    if __servo_id is None:
        resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/instance-id")
        if resp['status'] != '200' or len(content) <= 0:
            raise Exception('could not query the metadata for instance id (%s,%s)' % (resp, content))
        __servo_id = content
    return __servo_id

__public_ip = None
def get_public_ip():
    global __public_ip
    if __public_ip is None:
        try:
            resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/public-ipv4")
            if resp['status'] != '200' or len(content) <= 0:
                return None
            __public_ip = content
        except Exception, err:
            return None
    return __public_ip

__private_ip = None
def get_private_ip():
    global __private_ip
    if __private_ip is None:
        try:
            resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/local-ipv4")
            if resp['status'] != '200' or len(content) <= 0:
                return None
            __private_ip = content
        except Exception, err:
            return None
    return __private_ip

def appcookie_length():
    return 4096

def appcookie_timeout():
    try:
        return 60*int(get_value('app-cookie-duration'))
    except Exception, err:
        return 60*24 #24 hours
