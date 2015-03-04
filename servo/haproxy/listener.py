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

class Listener(object):
    def __init__(self, protocol, port, instance_port=None, instance_protocol=None, ssl_cert=None, loadbalancer=None, policies = None, connection_idle_timeout=None):
        self.__loadbalancer = loadbalancer  #loadbalancer name for debugging
        if protocol is not None:
            protocol = protocol.lower()
        self.__protocol = protocol
        self.__port = port
        if instance_port is not None:
            self.__instance_port = instance_port
        else:
            self.__instance_port = port
        if instance_protocol is not None:
            self.__instance_protocol = instance_protocol.lower()
        else:
            self.__instance_protocol = protocol
        self.__ssl_cert = ssl_cert
        self.__instances = set() 
        self.__ssl_cert_path = None
        self.__policies = policies
        self.__connection_idle_timeout = connection_idle_timeout
 
    def protocol(self):
        return self.__protocol
    
    def port(self):
        return self.__port
    
    def instance_port(self):
        return self.__instance_port

    def instance_protocol(self):
        return self.__instance_protocol

    def ssl_cert_arn(self):
        return self.__ssl_cert

    def add_instance(self, hostname):
        self.__instances.add(hostname)

    def remove_instance(self, hostname):
        self.__instances.remove(hostname)

    def has_instance(self, hostname):
        return hostname in self__instances

    def instances(self):
        return self.__instances

    def loadbalancer(self):
        return self.__loadbalancer

    def set_ssl_cert_path(self, path):
        self.__ssl_cert_path = path

    def ssl_cert_path(self):
        return self.__ssl_cert_path
 
    def policies(self):
        return self.__policies

    def set_connection_idle_timeout(self, timeout):
        self.__connection_idle_timeout = timeout

    def connection_idle_timeout(self):
        return self.__connection_idle_timeout
    
    def __eq__(self, other):
        if not isinstance(other, Listener):
            return False
        if self.__port != other.__port:
            return False 
        if self.__protocol != other.__protocol:
            return False
        if self.__instance_port != other.__instance_port:
            return False
        if self.__instance_protocol != other.__instance_protocol:
            return False
        if self.__ssl_cert != other.__ssl_cert:
            return False
        if self.policies() != other.policies():
            return False
        if self.__connection_idle_timeout != other.__connection_idle_timeout:
            return False
        if len(self.__instances.symmetric_difference(other.__instances)) > 0:
            return False
        return True
  
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'listener-%s-%d: [%s]' % (self.__protocol, self.__port, self.__instances)
    
    def __str__(self):
        return self.__repr__()
