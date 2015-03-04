# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from boto.ec2.elb.healthcheck import HealthCheck
from boto.ec2.elb.listener import Listener
from boto.ec2.elb.listelement import ListElement
from boto.ec2.elb.securitygroup import SecurityGroup
from boto.ec2.instanceinfo import InstanceInfo
from boto.resultset import ResultSet
from servo.ws.attributes import LbAttributes
from servo.ws.policies import PolicyDescription
import servo

class LoadBalancer(object):
    """
    Represents an EC2 Load Balancer, extended to support Euca-specific Loadbalancer definition
    """

    def __init__(self, connection=None, name=None, endpoints=None):
        """
        :ivar boto.ec2.elb.ELBConnection connection: The connection this load
            balancer was instance was instantiated from.
        :ivar list listeners: A list of tuples in the form of
            ``(<Inbound port>, <Outbound port>, <Protocol>)``
        :ivar boto.ec2.elb.healthcheck.HealthCheck health_check: The health
            check policy for this load balancer.
        :ivar list servo.ws.policies.PolicyDescription: A list of load balancer policies
        :ivar str name: The name of the Load Balancer.
        :ivar str dns_name: The external DNS name for the balancer.
        :ivar str created_time: A date+time string showing when the
            load balancer was created.
        :ivar list instances: A list of :py:class:`boto.ec2.instanceinfo.InstanceInfo`
            instances, representing the EC2 instances this load balancer is
            distributing requests to.
        :ivar list availability_zones: The availability zones this balancer
            covers.
        :ivar str canonical_hosted_zone_name: Current CNAME for the balancer.
        :ivar str canonical_hosted_zone_name_id: The Route 53 hosted zone
            ID of this balancer. Needed when creating an Alias record in a
            Route 53 hosted zone.
        :ivar boto.ec2.elb.securitygroup.SecurityGroup source_security_group:
            The security group that you can use as part of your inbound rules
            for your load balancer back-end instances to disallow traffic
            from sources other than your load balancer.
        :ivar list subnets: A list of subnets this balancer is on.
        :ivar list security_groups: A list of additional security groups that
            have been applied.
        :ivar str vpc_id: The ID of the VPC that this ELB resides within.
        :ivar list backends: A list of :py:class:`boto.ec2.elb.loadbalancer.Backend
            back-end server descriptions.
        """
        self.connection = connection
        self.name = name
        self.listeners = None
        self.health_check = None
        self.policy_descriptions = None
        self.dns_name = None
        self.created_time = None
        self.instances = None
        self.availability_zones = ListElement()
        self.canonical_hosted_zone_name = None
        self.canonical_hosted_zone_name_id = None
        self.source_security_group = None
        self.subnets = ListElement()
        self.security_groups = ListElement()
        self.vpc_id = None
        self.scheme = None
        self.backends = None
        self.attributes = None

    def __repr__(self):
        return 'LoadBalancer:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'HealthCheck':
            self.health_check = HealthCheck(self)
            return self.health_check
        elif name == 'ListenerDescriptions':
            self.listeners = ResultSet([('member', Listener)])
            return self.listeners
        elif name == 'AvailabilityZones':
            return self.availability_zones
        elif name == 'Instances':
            self.instances = ResultSet([('member', InstanceInfo)])
            return self.instances
        elif name == 'PolicyDescriptions':
            self.policy_descriptions = ResultSet([('member', PolicyDescription)])
            return self.policy_descriptions
        elif name == 'SourceSecurityGroup':
            self.source_security_group = SecurityGroup()
            return self.source_security_group
        elif name == 'Subnets':
            return self.subnets
        elif name == 'SecurityGroups':
            return self.security_groups
        elif name == 'VPCId':
            pass
        elif name == "BackendServerDescriptions":
            self.backends = ResultSet([('member', Backend)])
            return self.backends
        elif name == "LoadBalancerAttributes":
            self.attributes = LbAttributes(self)
            return self.attributes
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'LoadBalancerName':
            self.name = value
        elif name == 'DNSName':
            self.dns_name = value
        elif name == 'CreatedTime':
            self.created_time = value
        elif name == 'InstanceId':
            self.instances.append(value)
        elif name == 'CanonicalHostedZoneName':
            self.canonical_hosted_zone_name = value
        elif name == 'CanonicalHostedZoneNameID':
            self.canonical_hosted_zone_name_id = value
        elif name == 'VPCId':
            self.vpc_id = value
        elif name == 'Scheme':
            self.scheme = value
        else:
            setattr(self, name, value)

