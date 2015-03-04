# Copyright 2009-2015 Eucalyptus Systems, Inc.
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

from servo.ws.policies import PolicyDescription
import servo
class LoadbalancerPolicy(object):
    def __init__(self, policy_type_name, policy_name, attributes={}):
        self._policy_type_name = policy_type_name
        self._policy_name = policy_name
        self._attributes = attributes

    def policy_name(self):
        return self._policy_name

    def policy_type_name(self):
        return self._policy_type_name
 
    def attributes(self):
        return self._attributes

    def __eq__(self, other):
        if not isinstance(other, LoadbalancerPolicy):
            return False
        if self.policy_name() != other.policy_name():
            return False
        if self.policy_type_name() != other.policy_type_name():
            return False
        if len(self.attributes()) != len(other.attributes()):
            return False
        for k,v in self.attributes().items():
            if not other.attributes().has_key(k):
                return False
            if v != other.attributes()[k]:
                return False
        return True
   
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'loadbalancer policy (%s-%s-%s)' % (self.policy_name(), self.policy_type_name(), self.attributes())

    def __str__(self):
        return self.__repr__()

    @staticmethod 
    def from_policy_description(policy_desc):
        if policy_desc.policy_type_name == 'AppCookieStickinessPolicyType':
            if policy_desc.policy_name and policy_desc.policy_attr_descriptions:
                for attr in policy_desc.policy_attr_descriptions:
                    if attr.attr_name == 'CookieName':
                        return AppCookieStickinessPolicy(policy_desc.policy_name, attr.attr_value)
        elif policy_desc.policy_type_name == 'LBCookieStickinessPolicyType':
            if policy_desc.policy_name and policy_desc.policy_attr_descriptions:
                for attr in policy_desc.policy_attr_descriptions:
                    if attr.attr_name == 'CookieExpirationPeriod':
                        return LBCookieStickinessPolicy(policy_desc.policy_name, attr.attr_value)
        elif policy_desc.policy_type_name == 'SSLNegotiationPolicyType':
            if policy_desc.policy_name and policy_desc.policy_attr_descriptions:
                attr_dict = {}
                for attr in policy_desc.policy_attr_descriptions:
                    key = attr.attr_name
                    val = attr.attr_value
                    attr_dict[key] = val
                return SSLNegotiationPolicy(policy_desc.policy_name, attr_dict)
        return None


class AppCookieStickinessPolicy(LoadbalancerPolicy):
    def __init__(self, policy_name, cookie_name):
        LoadbalancerPolicy.__init__(self, 'AppCookieStickinessPolicyType', policy_name, {'CookieName':cookie_name})

    def cookie_name(self):
        if self.attributes().has_key('CookieName'):
            return self.attributes()['CookieName']
        else:
            return None

class LBCookieStickinessPolicy(LoadbalancerPolicy):
    def __init__(self, policy_name, expiration_period):
        LoadbalancerPolicy.__init__(self, 'LBCookieStickinessPolicyType', policy_name, {'CookieExpirationPeriod':expiration_period})

    def cookie_expiration_period(self):
        if self.attributes().has_key('CookieExpirationPeriod'):
            return self.attributes()['CookieExpirationPeriod']
        else:
            return None

class SSLNegotiationPolicy(LoadbalancerPolicy):
    def __init__(self, policy_name, attributes):
        LoadbalancerPolicy.__init__(self, 'SSLNegotiationPolicyType', policy_name, attributes)

    def attr_true(self, attr_name):
        if self.attributes().has_key(attr_name) and self.attributes()[attr_name] == 'true':
            return True
        else:
            return False

    def ssl_v2(self):
        return self.attr_true('Protocol-SSLv2')
    
    def ssl_v3(self):
        return self.attr_true('Protocol-SSLv3')

    def tls_v1(self):
        return self.attr_true('Protocol-TLSv1')

    def tls_v11(self):
        return self.attr_true('Protocol-TLSv1.1')

    def tls_v12(self):
        return self.attr_true('Protocol-TLSv1.2')

    def server_defined_cipher_order(self):
        return self.attr_true('Server-Defined-Cipher-Order')

    def reference_security_policy(self):
        if self.attributes().has_key('Reference-Security-Policy'):
            return self.attributes()['Reference-Security-Policy']
    
    def ciphers(self):
        non_cipher_attrs = set(['Protocol-SSLv2','Protocol-SSLv3','Protocol-TLSv1','Protocol-TLSv1.1','Protocol-TLSv1.2','Server-Defined-Cipher-Order','Reference-Security-Policy'])
        cipher_list = []
        for k,v in self.attributes().items():
            if not k in non_cipher_attrs and self.attributes()[k] == 'true':
                    cipher_list.append(k)
        return cipher_list
