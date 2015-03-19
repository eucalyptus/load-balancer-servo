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
class BackendInstance(object):
    def __init__(self, connection=None):
        self.instance_id = None
        self.instance_ip_address = None
        self.report_health_check = False

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'InstanceId':
            self.instance_id = value
        elif name == 'InstanceIpAddress':
            self.instance_ip_address = value
        elif name == 'ReportHealthCheck':
            if value == 'true':
                self.report_health_check = True
            else:
                self.report_health_check = False
        
    def __eq__(self, other):
        if not isinstance(other, BackendInstance):
            return False
        if self.instance_id != other.instance_id:
            return False
        if self.instance_ip_address != other.instance_ip_address:
            return False
        if self.report_health_check != other.report_health_check:
            return False
        return True
   
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'backend instance (%s-%s)' % (self.instance_id, self.instance_ip_address)

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return self.instance_id
