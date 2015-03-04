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
from boto.resultset import ResultSet
class PolicyAttrDescription(object):
    def __init__(self, connection=None):
        self.attr_name = None
        self.attr_value = None

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'AttributeName':
            self.attr_name = value
        elif name == 'AttributeValue':
            self.attr_value = value

class PolicyDescription(object):
    def __init__(self, connection=None):
        self.policy_name = None
        self.policy_type_name = None
        self.policy_attr_descriptions=[]

    def startElement(self, name, attrs, connection):
        if name == 'PolicyAttributeDescriptions':
            rs = ResultSet([('member', PolicyAttrDescription)])
            self.policy_attr_descriptions = rs
            return rs

    def endElement(self, name, value, connection):
        if name == 'PolicyName':
            self.policy_name = value
        elif name == 'PolicyTypeName':
            self.policy_type_name = value
